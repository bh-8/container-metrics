"""
container_metrics.py

core
"""

# IMPORTS

from alive_progress import alive_bar
import argparse
import datetime
import gridfs
import hashlib
import json
import logging
import os
from pathlib import Path
import sys
log = None

from abstract_structure_mapping import ContainerSection, ContainerSegment, Coverage
from abstract_pipeline import AbstractPipeline
from container_formats import *
from pipeline_formats import *
from static_utils import MIMEDetector, MongoInterface, flatten_paths, to_camel_case

# GLOBAL STATIC MAPPINGS

PROG_NAME = "container-metrics"
MIME_INFO = "./container_formats/mime_mapping.json"

# STRUCTURE MAP ACQUISITION

class StructureMapping():
    def __init__(self, file_path: Path, supported_mime_types: dict, analysis_depth_cap: int) -> None:
        self.__file_path: Path = file_path
        self.__supported_mime_types: dict = supported_mime_types
        self.__analysis_depth_cap: int = analysis_depth_cap

        self.__structure_mapping: dict = {
            "_gridfs": None,
            "meta": {
                "file": {
                    "name": None,
                    "size": None,
                    "type": {
                        "magic": None,
                        "extension": None
                    },
                    "sha256": None,
                    "created": None,
                    "modified": None
                },
                "investigation": {
                    "started": None,
                    "finished": None
                }
            },
            "sections": []
        }

        self.__file_data: bytes = None
        with open(file_path, "rb") as _fhandle:
            self.__file_data = _fhandle.read()
        if self.__file_data == None:
            raise IOError(f"could not read file '{file_path}'")

        # init analysis queue with initial entry
        self.__analysis_queue: list[dict] = []
        self.queue_analysis(0)

        self.__init_meta()
        self.__file_structure_analysis()

    def queue_analysis(self, position: int, depth: int = 0, length: int | None = None) -> None:
        self.__analysis_queue.append({
            "position": position,
            "length": length,
            "depth": depth
        })
        log.info(f"analysis queue extended by section from position {position}")

    def __init_meta(self) -> None:
        self.__structure_mapping["meta"]["investigation"]["started"] = datetime.datetime.now().isoformat()

        self.__structure_mapping["meta"]["file"]["name"] = self.__file_path.name
        self.__structure_mapping["meta"]["file"]["size"] = len(self.__file_data)
        self.__structure_mapping["meta"]["file"]["type"]["magic"] = MIMEDetector.from_bytes_by_magic(self.__file_data)
        self.__structure_mapping["meta"]["file"]["type"]["extension"] = MIMEDetector.from_path_by_filename(self.__file_path)
        self.__structure_mapping["meta"]["file"]["sha256"] = hashlib.sha256(self.__file_data).hexdigest()
        self.__structure_mapping["meta"]["file"]["created"] = datetime.datetime.fromtimestamp(os.path.getctime(self.__file_path)).isoformat()
        self.__structure_mapping["meta"]["file"]["modified"] = datetime.datetime.fromtimestamp(os.path.getmtime(self.__file_path)).isoformat()

    def __file_structure_analysis(self) -> None:
        while len(self.__analysis_queue) > 0:
            # read analysis parameters
            _analysis_position: int = self.__analysis_queue[0]["position"]
            _analysis_length: int = len(self.__file_data) - _analysis_position if self.__analysis_queue[0]["length"] == None else self.__analysis_queue[0]["length"]
            _analysis_depth: int = self.__analysis_queue[0]["depth"]
            self.__analysis_queue.pop(0)

            # abort at maximum structure analysis depth
            if _analysis_depth > self.__analysis_depth_cap:
                continue

            # decide mime-type of data section
            _analysis_data: bytes = self.__file_data[_analysis_position:_analysis_position+_analysis_length]
            _mime_type: str = MIMEDetector.from_bytes_by_magic(_analysis_data)

            # find begin of files even when mime type is unknown at first
            if not _mime_type in self.__supported_mime_types:
                log.warning(f"encountered unsupported mime type '{_mime_type}' on position {_analysis_position}")
                hitmap: list[dict] = []
                for k in self.__supported_mime_types.keys():
                    if len(self.__supported_mime_types[k]) > 2:
                        for t in self.__supported_mime_types[k][2]:
                            s: bytes = bytes.fromhex(t)
                            f: int = self.__file_data.find(s, _analysis_position)
                            if f > _analysis_position:
                                hitmap.append([f, f - _analysis_position])
                if len(hitmap) > 0:
                    hit = sorted(hitmap, key=lambda d: d[0])[0]
                    self.queue_analysis(hit[0], _analysis_depth + 1)
                    _analysis_length = hit[1]
                    _analysis_data: bytes = self.__file_data[_analysis_position:_analysis_position+_analysis_length]

            _section: ContainerSection = ContainerSection(self, _analysis_position, _analysis_data, _mime_type, _analysis_depth)

            # decide specialized analysis
            if _mime_type in self.__supported_mime_types:
                _mime_type_info: list[str] = self.__supported_mime_types[_mime_type]
                _mime_id: str = _mime_type_info[0]
                _section.set_mime_name(_mime_type_info[1])

                # check existence of required implementation
                _class_label: str = f"{to_camel_case(_mime_id)}Analysis"
                if not _class_label in globals():
                    raise NotImplementedError(f"could not find class '{_class_label}', expected definition in '{_mime_id}.py'")

                # initiate format specific analysis
                _format_specific_analysis = globals()[_class_label]()
                _section = _format_specific_analysis.process(_section)
            else:
                _section.set_length(_analysis_length)

            # coverage
            try:
                _coverage: Coverage = Coverage.from_section(_section)
                _section.add_segment(_coverage.as_uncovered_segment)
            except ValueError:
                log.critical("could not perform coverage analysis as section has no length")
                _section.add_segment(ContainerSegment("uncovered"))

            self.__structure_mapping["sections"].append(_section.as_dictionary)

    @property
    def as_dictionary(self) -> dict:
        self.__structure_mapping["meta"]["investigation"]["finished"] = datetime.datetime.now().isoformat()
        return self.__structure_mapping
    @property
    def file_data(self) -> bytes:
        return self.__file_data

# ENTRYPOINT

class Main:
    # entry point
    def __init__(self) -> None:
        parser = argparse.ArgumentParser(
            prog=f"{PROG_NAME}",
            usage=f"{PROG_NAME} <command> [<args>]",
            description="""possible commands are:
  acquire\textract and import metrics from container files into database
  query  \tquery database to export selected metrics in different formats""",
            epilog=None, # [TODO]: credits o.a.
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        # display help when no argument given
        if len(sys.argv) <= 1:
            parser.print_help()
            sys.exit(0)

        # subcommand option
        parser.add_argument("command", help="subcommand to run")
        args = parser.parse_args(sys.argv[1:2])

        # check whether this class contains a method for the requested subcommand
        if not hasattr(self, f"subcmd_{args.command}"):
            parser.print_help()
            sys.exit(1)

        # call subcommand method
        getattr(self, f"subcmd_{args.command}")()

    @staticmethod
    def __verify_db_connection(connection: str):
        MongoInterface.set_connection(connection)
        if len(MongoInterface.get_connection()["admin"].list_collection_names()) != 2:
            raise ConnectionError("could not verify mongo db connection")

    @staticmethod
    def __init_logger(log_level: str) -> None:
        logging.basicConfig(level=getattr(logging, log_level.upper()))

        global log
        log = logging.getLogger(__name__)

    # subcommand 'acquire'
    def subcmd_acquire(self):
        parser = argparse.ArgumentParser(
            prog=f"{PROG_NAME} acquire",
            description="scan container files, extract and import metrics into database",
            epilog=None
        )
        parser.add_argument("mongodb",
            type=str,
            metavar="<mongodb>",
            help="mongodb connection string"
        )
        parser.add_argument("collection",
            type=str,
            metavar="<collection>",
            help="mongodb collection identifier"
        )

        parser.add_argument("paths",
            type=str,
            metavar="<path>",
            nargs="+",
            help="one or more paths to container files/directories"
        )
        parser.add_argument("--max-depth",
            metavar="<n>",
            type=int,
            default=16,
            help="maxiumum recursive analysis depth"
        )
        parser.add_argument("--recursive",
            action="store_true",
            help="traverse given directories recursively"
        )
        parser.add_argument("--log",
            type=str,
            choices=["debug", "info", "warning", "error"],
            default="warning",
            help="logging level"
        )

        # display help when no argument given
        if len(sys.argv) <= 2:
            parser.print_help()
            sys.exit(1)

        db_name: str = f"{datetime.datetime.now().year}-{datetime.datetime.now().month:02d}-{datetime.datetime.now().day:02d}"

        try:
            # subcommand arguments
            args = parser.parse_args(sys.argv[2:])

            # init logger
            self.__init_logger(args.log)

            # test connection to mongo db instance
            log.debug(f"setting up connection to '{args.mongodb}'...")
            self.__verify_db_connection(args.mongodb)
            log.info(f"connected to database via '{args.mongodb}'")

            c_name: str = args.collection

            ####################################################################################################

            if args.max_depth < 0:
                raise ValueError("maximum analysis depth can not be negative")

            # gather input files
            log.debug("resolving input paths...")
            path_list = flatten_paths([Path(x).resolve() for x in args.paths], args.recursive)
            log.info(f"found {len(path_list)} file(s) in total")

            # load 'mapping.json'
            supported_mime_types: dict = {}
            with open(MIME_INFO) as json_handle:
                supported_mime_types = json.loads(json_handle.read())
            log.info(f"supported mime-types are {', '.join(list(supported_mime_types.keys()))}")

            # loop supported files
            with alive_bar(len(path_list), title="acquisition progress") as pbar:
                for file_path in path_list:
                    log.info(f"processing file '{file_path.name}'...")

                    # analysis
                    structure_mapping: StructureMapping = StructureMapping(file_path, supported_mime_types, args.max_depth)

                    structure_mapping_dict: dict = structure_mapping.as_dictionary

                    # insert json structure into database

                    target_db = MongoInterface.get_connection()[db_name]
                    grid_fs = gridfs.GridFS(target_db, "gridfs")
                    log.info(f"transferring raw data to gridfs: '{db_name}/gridfs'...")
                    grid_fs_id = grid_fs.put(structure_mapping.file_data, filename=file_path.name)

                    log.info(f"transferring bson to mongodb: '{db_name}/{c_name}-gridfs:{grid_fs_id}'...")
                    structure_mapping_dict["_gridfs"] = grid_fs_id
                    target_collection = MongoInterface.get_connection()[db_name][c_name]
                    target_collection.insert_one(structure_mapping_dict)

                    pbar(1)
            log.info("done")
        except Exception as e:
            print(f"##################################################")
            print(f" > ERROR: acquisition failed due to an unexpected exception!")
            raise e

    # subcommand 'query'
    def subcmd_query(self):
        parser = argparse.ArgumentParser(
            prog=f"{PROG_NAME} query",
            description="query database to export selected metrics in different formats",
            epilog=None
        )
        parser.add_argument("mongodb",
            type=str,
            metavar="<mongodb>",
            help="mongodb connection string"
        )
        parser.add_argument("collection",
            type=str,
            metavar="<collection>",
            help="mongodb collection identifier"
        )

        parser.add_argument("pipeline",
            type=str,
            #metavar="<pipeline>",
            choices=["csv", "json", "yara"], # TODO: csv arff ...
            help="output format"
        )
        parser.add_argument("--log",
            type=str,
            choices=["debug", "info", "warning", "error"],
            default="warning",
            help="logging level"
        )

        # display help when no argument given
        if len(sys.argv) <= 2:
            parser.print_help()
            sys.exit(1)

        db_name: str = f"{datetime.datetime.now().year}-{datetime.datetime.now().month:02d}-{datetime.datetime.now().day:02d}"

        try:
            # subcommand arguments
            args = parser.parse_args(sys.argv[2:])

            # init logger
            self.__init_logger(args.log)

            # test connection to mongo db instance
            log.debug(f"setting up connection to '{args.mongodb}'...")
            self.__verify_db_connection(args.mongodb)
            log.info(f"connected to database via '{args.mongodb}'")

            c_name: str = args.collection

            ####################################################################################################

            if not db_name in MongoInterface.get_connection().list_database_names():
                raise ValueError(f"database '{db_name}' does not exist")
            if not c_name in MongoInterface.get_connection()[db_name].list_collection_names():
                raise ValueError(f"database '{db_name}' has no collection named '{c_name}'")

            target_db = MongoInterface.get_connection()[db_name]
            grid_fs = gridfs.GridFS(target_db, "gridfs")

            target_collection = MongoInterface.get_connection()[db_name][c_name]

            # check existence of required implementation
            pipeline_id: str = f"{args.pipeline}_pipeline"
            class_label: str = f"{to_camel_case(pipeline_id)}"
            if not class_label in globals():
                raise NotImplementedError(f"could not find class '{class_label}', expected definition in '{pipeline_id}.py'")

            params: any = None
            match args.pipeline:
                case "csv":
                    params: list[str] = ["audio/mpeg:id3v2:offset,length,frame_id,content"," image/jpeg:jpeg_segments:offset,length,id,long_name", "application/pdf:xref:offset,length,object_number", "application/pdf:body:data.data./Nums.data.*.data,data.data./Nums.data.*,data.data./Matrix.data,data.data./BBox.data"]
                case "json":
                    pass
                case "yara":
                    params: list[str] = ["./io/test.yara"]
                case _:
                    raise ValueError(f"unknown pipeline '{args.pipeline}'")

            # loop entries
            with alive_bar(target_collection.count_documents({}), title="querying progress") as pbar:
                for document in target_collection.find():
                    # read bson
                    log.info(f"retrieving data from database: '{db_name}/{c_name}-id:{document['_id']}-gridfs:{document['_gridfs']}'...")
                    bson_document = grid_fs.get(document["_gridfs"]).read()

                    # initiate format specific analysis
                    log.info(f"processing file '{document['meta']['file']['name']}'...")
                    pipeline: AbstractPipeline = globals()[class_label](document, bson_document, params)
                    pipeline.process()

                    pbar(1)
            log.info("done")
        except Exception as e:
            print(f"##################################################")
            print(f" > ERROR: querying failed due to an unexpected exception!")
            raise e

# entry point
if __name__ == "__main__":
    Main()
