import argparse
import json
from pathlib import Path
import sys
from container_formats import *
from static_utils import *
from alive_progress import alive_bar

PROG_NAME = "container-metrics"
MIME_INFO = "./container_formats/mime_mapping.json"

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
            help="use libmagic to detect mime type instead of file extension"
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

            # filter unsupported mime-types
            mime_type_dict = {}
            with open(MIME_INFO) as json_handle:
                mime_type_dict = json.loads(json_handle.read())
            mime_type_determiner = MIMETypeFilter.by_content if args.magic else MIMETypeFilter.by_filename
            filtered_path_list = filter_paths(path_list, list(mime_type_dict.keys()), mime_type_determiner)
            logger.info(f"found {len(filtered_path_list)} file(s) with supported mime-types ({', '.join(list(mime_type_dict.keys()))})")

            # test connection to mongo db instance
            logger.debug(f"setting up connection to '{args.mongodb}'...")
            MongoInterface.set_connection(args.mongodb)
            if len(MongoInterface.get_connection()["admin"].list_collection_names()) != 2:
                raise ConnectionError("could not verify mongo db connection")
            logger.info(f"connected to database via '{args.mongodb}'")

            # go through supported files
            with alive_bar(len(filtered_path_list), title="Scanning", length=25) as pbar:
                for file_path in filtered_path_list:
                    # determine format class by mime-type
                    file_mime_type: str = mime_type_determiner(file_path)
                    file_mime_info: List[str] = mime_type_dict[file_mime_type]

                    # load required format instance
                    class_label = f"{to_camel_case(file_mime_info[0])}Format"
                    logger.debug(f"initializing instance {class_label}({file_path}, {file_mime_type}, {file_mime_info})")
                    format_instance = globals()[class_label](file_path, file_mime_type, file_mime_info)

                    # use specific format class for parsing
                    format_instance.parse()

                    # [TODO] insert json structure into database
                    format_dict: dict = format_instance.get_format_dict()
                    print(f"  > {file_path}:\n\t{format_dict}\n")

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
