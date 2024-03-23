import argparse
import sys

from pathlib import Path
from metric_extractor import MetricExtractor

HELP_PROG = "./container-metrics"

class Main:
    def __init__(self) -> None:
        parser = argparse.ArgumentParser(
            prog=f"{HELP_PROG}",
            usage=f"{HELP_PROG} <command> [<args>]",
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

        parser.add_argument("command", help="subcommand to run")
        args = parser.parse_args(sys.argv[1:2])

        # check whether this class contains a method for the requested command
        if not hasattr(self, f"cmd_{args.command}"):
            parser.print_help()
            sys.exit(1)

        # call command method
        getattr(self, f"cmd_{args.command}")()
    def cmd_scan(self):
        parser = argparse.ArgumentParser(
            prog=f"{HELP_PROG} scan",
            description="scan container files, extract and import metrics into database",
            epilog=None
        )

        parser.add_argument("-i", "--input",
            type=argparse.FileType("rb"),
            required=True
        )
        parser.add_argument("-o", "--output",
            type=argparse.FileType("wb"),
            required=True
        )
        #[TODO]: output not needed, replace with db connect string
        parser.add_argument("--magic",
            action="store_true",
            help="use libmagic to detect mime type instead of file extension"
        )

        # display help when no argument given
        if len(sys.argv) <= 2:
            parser.print_help()
            sys.exit(1)

        try:
            args = parser.parse_args(sys.argv[2:])
            MetricExtractor.extract(args)
        except Exception as e:
            print(f"##################################################")
            print(f" > ERROR: metric extractor crashed!")
            raise e
            sys.exit(1)

if __name__ == "__main__":
    Main()
