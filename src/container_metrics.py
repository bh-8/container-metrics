import argparse
import sys

from pathlib import Path
from metric_extractor import MetricExtractor

class Main:
    def __init__(self) -> None:
        parser = argparse.ArgumentParser(
            prog="container_metrics",
            usage=f"container_metrics <command> [<args>]",
            description="""possible commands are:
\textract       extract metrics of a given container file
\tview          create formatted views of selected metrics
\t<abs.path>    auto mode""",
            epilog="", # [TODO]: credits o.a.
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        # display help when no argument given
        if len(sys.argv) <= 1:
            parser.print_help()
            sys.exit(1)

        parser.add_argument("command", help="subcommand to run")
        args = parser.parse_args(sys.argv[1:2])

        # check whether this class contains a method for the requested command
        if not hasattr(self, args.command):
            if Path(args.command).is_absolute() and Path(args.command).exists() and Path(args.command).is_file():
                print("ABSOLUTE PATH GIVEN AND EXISTS AND IS FILE!") # [TODO]: auto mode
                return
            else:
                parser.print_help()
                sys.exit(1)

        # call command method
        getattr(self, args.command)()
    def extract(self):
        parser = argparse.ArgumentParser(
            prog="container_metrics extract",
            description="extract metrics of a given container file",
            epilog=""
        )

        parser.add_argument("-i", "--input",
            type=argparse.FileType("rb"),
            required=True
        )
        parser.add_argument("-o", "--output",
            type=argparse.FileType("wb"),
            required=True
        )
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
    def view(self):
        # [TODO]: implementation missing
        raise NotImplementedError("command view not implemented yet")

if __name__ == "__main__":
    Main()
