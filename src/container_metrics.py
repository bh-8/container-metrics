import argparse
import sys

from pathlib import Path
from static_utils import *

PROG_NAME = "container-metrics"

class Main:
    def __init__(self) -> None:
        # entry point

        parser = argparse.ArgumentParser(
            prog=f"{PROG_NAME}",
            usage=f"{PROG_NAME} <command> [<args>]",
            description="""possible commands are:
  scan\textract and import metrics from container files into database""",
#  export\texport views on selected metrics from the database""", # [TODO]: implementation missing
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
            path_list = flatten_paths(
                [Path(x).resolve() for x in args.paths],
                args.recursive
            )
            logger.info(f"found {len(path_list)} file(s) in total")

            # filter unsupported mime-types
            mime_types = get_supported_mime_types()
            filtered_path_list = filter_mime_types(
                path_list,
                mime_types,
                MIMETypeFilter.by_content if args.magic else MIMETypeFilter.by_filename
            )
            logger.info(f"found {len(filtered_path_list)} file(s) with supported mime-types ({', '.join(mime_types)})")

            # test connection to mongo db instance
            logger.debug(f"setting up connection to '{args.mongodb}'...")
            MongoInterface.set_connection(args.mongodb)
            if len(MongoInterface.get_connection()["admin"].list_collection_names()) != 2:
                raise ConnectionError("could not verify mongo db connection")
            logger.info(f"connected to database via '{args.mongodb}'")

        except Exception as e:
            print(f"##################################################")
            print(f" > ERROR: metric extractor crashed!")
            raise e
            sys.exit(1)

# entry point
if __name__ == "__main__":
    Main()