from abstract_intermediate_format import ContainerSection, ContainerSegment, ContainerFragment, Coverage
from container_formats import *
from alive_progress import alive_bar
import argparse
import datetime
import gridfs
import json
from pathlib import Path
from static_utils import StaticLogger, MIMEDetector, MongoInterface, flatten_paths, to_camel_case
import sys
import hashlib
import os

# TODO: JPEG
# TODO: MP3

# TODO: logging
# TODO: todos
# TODO: class variables start _; privates no underscore!

PROG_NAME = "container-metrics"
MIME_INFO = "./container_formats/mime_mapping.json"

class IntermediateFormat():
    def __init__(self, file_path: Path, supported_mime_types: dict, analysis_depth_cap: int) -> None:
        self.logger: StaticLogger = StaticLogger.get_logger() #TODO: log output
        self.file_path: Path = file_path
        self.supported_mime_types: dict = supported_mime_types
        self.analysis_depth_cap: int = analysis_depth_cap

        self.intermediate_format: dict = {
            "meta": {
                "file_name": None,
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
                },
                "gridfs": None
            },
            "sections": []
        }

        self.file_data: bytes = None
        with open(file_path, "rb") as _fhandle:
            self.file_data = _fhandle.read()
        if self.file_data == None:
            raise IOError(f"could not read file '{file_path}'")

        # init analysis queue with initial entry
        self.analysis_queue: list[dict] = []
        self.queue_analysis(0)

        self.init_investigation_meta()
        self.file_structure_analysis()

    def queue_analysis(self, position: int, depth: int = 0, length: int | None = None) -> None:
        self.analysis_queue.append({
            "position": position,
            "length": length,
            "depth": depth
        })

    def init_investigation_meta(self) -> None:
        self.intermediate_format["meta"]["investigation"]["started"] = datetime.datetime.now().isoformat()

        self.intermediate_format["meta"]["file_name"] = self.file_path.name #TODO: remove later
        self.intermediate_format["meta"]["file"]["name"] = self.file_path.name
        self.intermediate_format["meta"]["file"]["size"] = len(self.file_data)
        self.intermediate_format["meta"]["file"]["type"]["magic"] = MIMEDetector.from_bytes_by_magic(self.file_data)
        self.intermediate_format["meta"]["file"]["type"]["extension"] = MIMEDetector.from_path_by_filename(self.file_path)
        self.intermediate_format["meta"]["file"]["sha256"] = hashlib.sha256(self.file_data).hexdigest()
        self.intermediate_format["meta"]["file"]["created"] = datetime.datetime.fromtimestamp(os.path.getctime(self.file_path)).isoformat()
        self.intermediate_format["meta"]["file"]["modified"] = datetime.datetime.fromtimestamp(os.path.getmtime(self.file_path)).isoformat()

    def file_structure_analysis(self) -> None:
        while len(self.analysis_queue) > 0:
            # read analysis parameters
            _analysis_position: int = self.analysis_queue[0]["position"]
            _analysis_length: int = len(self.file_data) - _analysis_position if self.analysis_queue[0]["length"] == None else self.analysis_queue[0]["length"]
            _analysis_depth: int = self.analysis_queue[0]["depth"]
            self.analysis_queue.pop(0)

            # abort at maximum structure analysis depth
            if _analysis_depth > self.analysis_depth_cap:
                continue

            # decide mime-type of data section
            _analysis_data: bytes = self.file_data[_analysis_position:_analysis_position+_analysis_length]
            _mime_type: str = MIMEDetector.from_bytes_by_magic(_analysis_data)

            # find begin of files even when mime type is unknown at first
            if not _mime_type in self.supported_mime_types:
                hitmap: list[dict] = []
                for k in self.supported_mime_types.keys():
                    if len(self.supported_mime_types[k]) > 2:
                        s: bytes = bytes.fromhex(self.supported_mime_types[k][2])
                        f: int = self.file_data.find(s, _analysis_position)
                        if f > _analysis_position:
                            hitmap.append([f, f - _analysis_position])
                if len(hitmap) > 0:
                    hit = sorted(hitmap, key=lambda d: d[0])[0]
                    self.queue_analysis(hit[0], _analysis_depth + 1)
                    _analysis_length = hit[1]
                    _analysis_data: bytes = self.file_data[_analysis_position:_analysis_position+_analysis_length]

            _section: ContainerSection = ContainerSection(self, _analysis_position, _analysis_data, _mime_type, _analysis_depth)

            # decide specialized analysis
            if _mime_type in self.supported_mime_types:
                _mime_type_info: list[str] = self.supported_mime_types[_mime_type]
                _mime_id: str = _mime_type_info[0]
                _section.set_mime_name(_mime_type_info[1])

                # check existence of required implementation
                _class_label: str = f"{to_camel_case(_mime_id)}Analysis"
                if not _class_label in globals():
                    raise NotImplementedError(f"could not find class '{_class_label}', expected definition in '{_mime_id}.py'")

                # initiate format specific analysis
                _format_specific_analysis = globals()[_class_label]()
                _section = _format_specific_analysis.process_section(_section)
            else:
                _section.set_length(_analysis_length)

            # coverage
            try:
                _coverage: Coverage = Coverage.from_section(_section)
                _section.add_segment("uncovered", _coverage.get_uncovered_segment())
            except ValueError:
                self.logger.critical("could not perform coverage analysis as section has no length")
                _section.add_segment("uncovered", ContainerSegment())

            self.intermediate_format["sections"].append(_section.get_section())

    def get_intermediate_format(self) -> dict:
        self.intermediate_format["meta"]["investigation"]["finished"] = datetime.datetime.now().isoformat()
        return self.intermediate_format

    def get_file_data(self) -> bytes:
        return self.file_data

class Main:
    # entry point
    def __init__(self) -> None:
        parser = argparse.ArgumentParser(
            prog=f"{PROG_NAME}",
            usage=f"{PROG_NAME} <command> [<args>]",
            description="""possible commands are:
  scan\textract and import metrics from container files into database""",
#  export\texport views on selected metrics from the database""", # [TODO]: implementation missing
#  add user (analyst/examiner info)
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

    # subcommand 'scan'
    def subcmd_scan(self):
        # initialize subcommand parser
        parser = argparse.ArgumentParser(
            prog=f"{PROG_NAME} scan",
            description="scan container files, extract and import metrics into database",
            epilog=None
        )
        parser.add_argument("mongodb",
            type=str,
            metavar="<mongodb>",
            help="mongodb connection string"
        )
        parser.add_argument("paths",
            type=str,
            metavar="<path>",
            nargs="+",
            help="one or more paths to container files/directories"
        )
        parser.add_argument("--recursive",
            action="store_true",
            help="traverse given directories recursively"
        )
        parser.add_argument("--magic",
            action="store_true",
            help="use libmagic to detect initial mime type instead of file extension"
        )
        parser.add_argument("--log",
            type=str,
            choices=["debug", "info", "warning", "error"],
            default="warning",
            help="logging level")

        # display help when no argument given
        if len(sys.argv) <= 2:
            parser.print_help()
            sys.exit(1)

        db_name = f"{datetime.datetime.now().year}-{datetime.datetime.now().month}-{datetime.datetime.now().day}"
        c_name = f"{int((datetime.datetime.now()-datetime.datetime(1970, 1, 1)).total_seconds())}"

        try:
            # subcommand arguments
            args = parser.parse_args(sys.argv[2:])

            # init logger
            StaticLogger.set_logger(PROG_NAME, args.log.upper())
            logger = StaticLogger.get_logger()

            # gather input files
            logger.debug("resolving input paths...")
            path_list = flatten_paths([Path(x).resolve() for x in args.paths], args.recursive)
            logger.info(f"found {len(path_list)} file(s) in total")

            # load 'mime_mapping.json'
            supported_mime_types: dict = {}
            with open(MIME_INFO) as json_handle:
                supported_mime_types = json.loads(json_handle.read())
            logger.info(f"supported mime-types are {', '.join(list(supported_mime_types.keys()))}")

            # test connection to mongo db instance
            logger.debug(f"setting up connection to '{args.mongodb}'...")
            MongoInterface.set_connection(args.mongodb)
            if len(MongoInterface.get_connection()["admin"].list_collection_names()) != 2:
                raise ConnectionError("could not verify mongo db connection")
            logger.info(f"connected to database via '{args.mongodb}'")

            # loop supported files
            with alive_bar(len(path_list), title="scan progress") as pbar:
                for file_path in path_list:
                    logger.info(f"inspecting file '{file_path}'...")

                    # TODO: implement as switch...
                    _int_max_parsing_depth = 10

                    # analysis
                    intermediate_format: IntermediateFormat = IntermediateFormat(file_path, supported_mime_types, _int_max_parsing_depth)

                    intermediate_format_dict: dict = intermediate_format.get_intermediate_format()

                    # insert json structure into database
                    logger.debug(f"storing metrics in database '{db_name}/{c_name}'...")

                    target_db = MongoInterface.get_connection()[db_name]
                    grid_fs = gridfs.GridFS(target_db, "gridfs")
                    grid_fs_id = grid_fs.put(intermediate_format.get_file_data(), filename=file_path.name)

                    # TODO: implement optional parameter to set the collection name (scalability)
                    intermediate_format_dict["meta"]["gridfs"] = grid_fs_id
                    target_collection = MongoInterface.get_connection()[db_name][c_name]
                    target_collection.insert_one(intermediate_format_dict)

                    # TODO: debug print
                    with open("/home/container-metrics/io/_out.json", "w") as f:
                        json.dump(intermediate_format_dict["sections"], f)
                        f.close()

                    pbar(1)
            logger.info("done")
        except Exception as e:
            print(f"##################################################")
            print(f" > ERROR: metric extractor crashed!")
            raise e
            sys.exit(1)

# entry point
if __name__ == "__main__":
    Main()
