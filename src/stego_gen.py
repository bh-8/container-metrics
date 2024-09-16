"""
stego_gen.py

"""

from alive_progress import alive_bar
import argparse
from pathlib import Path
import os
import subprocess
import sys
import time



class StegoTool():
    def __init__(self, stego_tool: str, executable: str, parameters: list[str], context_path: Path = Path("/home/stego-gen"), outfile_extension: str | None = None) -> None:
        self.__stego_tool: str = stego_tool
        self.__executable: str = executable
        self.__parameters: list[str] = parameters
        self.__context_path: Path = context_path
        self.__outfile_extension: str | None = outfile_extension

        if not Path(self.__executable).exists():
            raise FileNotFoundError("executable path does not exist")
        if not self.__context_path.exists():
            raise FileNotFoundError("context path does not exist")

    def apply_execution_context(self) -> None:
        os.chdir(self.__context_path)

    @property
    def stego_tool(self) -> str:
        return self.__stego_tool
    @property
    def executable(self) -> str:
        return self.__executable
    @property
    def exec_str(self) -> str:
        return " ".join([self.__executable] + [f"'{p}'" for p in self.__parameters])
    @property
    def key_required(self) -> bool:
        return "<KEY>" in self.__parameters
    @property
    def outfile_extension(self) -> str | None:
        return self.__outfile_extension
STEGO_TOOLS=[
    StegoTool("boobytrappdf", "/home/stego-gen/venv/bin/python3", ["/opt/booby-trap-pdf/booby-trap-PDF.py", "bin", "<INPUT>", "<OUTPUT>", "<MESSAGE>"]),
    StegoTool("f5", "/usr/bin/xvfb-run", ["-a", "/usr/bin/java", "--add-exports", "java.base/sun.security.provider=ALL-UNNAMED", "-mx100M", "Embed", "-e", "<MESSAGE>", "-p", "<KEY>", "<INPUT>", "<OUTPUT>"], context_path=Path("/opt/F5-steganography")),
    StegoTool("hstego", "/home/stego-gen/venv/bin/python3", ["/opt/hstego/hstego.py", "embed", "<MESSAGE>", "<INPUT>", "<OUTPUT>", "<KEY>"], context_path=Path("/opt/hstego")),
    StegoTool("jsteg", "/opt/jsteg-linux-amd64", ["hide", "<INPUT>", "<MESSAGE>", "<OUTPUT>"]),
    StegoTool("mp3stego", "/usr/bin/wine", ["/opt/Encode.exe", "-E", "<MESSAGE>", "-P", "<KEY>", "<INPUT>", "<OUTPUT>"], outfile_extension=".mp3"),
    StegoTool("pdfhide", "/opt/pdf_hide/pdf_hide", ["-o", "<OUTPUT>", "-k", "<KEY>", "embed", "<MESSAGE>", "<INPUT>"]),
    StegoTool("pdfstego", "/opt/PDFStego/pdfstego", ["-e", "-c", "<INPUT>", "-m", "<MESSAGE>", "-p", "<KEY>", "-s", "<OUTPUT>"]),
]

parser = argparse.ArgumentParser(
    prog=f"stego-gen",
    epilog=None, # [TODO]: credits o.a.
    formatter_class=argparse.RawDescriptionHelpFormatter
)
parser.add_argument("stego_tool",
    type=str,
    metavar="<stego_tool>",
    choices=[i.stego_tool for i in STEGO_TOOLS],
    help="can either be " + ', '.join(f"'{i.stego_tool}'" for i in STEGO_TOOLS)
)
parser.add_argument("input",
    type=str,
    metavar="<input>",
    help="input directory path"
)
parser.add_argument("output",
    type=str,
    metavar="<output>",
    help="output directory path"
)
parser.add_argument("message",
    type=str,
    metavar="<message>",
    help="message file path"
)
parser.add_argument("key",
    type=str,
    metavar="<key>",
    nargs='?',
    help="key string; optional for some tools"
)
parser.add_argument("-deo", "--discard-error-outfile", action="store_true", help="remove output file when stego tool throws error")
parser.add_argument("-t", "--timeout", type=int, required=False, default=30, help="maximum seconds per stegogram creation, default is 30")
args = parser.parse_args(sys.argv[1:])

@staticmethod
def flatten_paths(path_list: list[Path], recursive: bool = False) -> list[Path]:
    flattened_list = []
    for p in path_list:
        if not p.exists():
            continue

        if p.is_file():
            flattened_list.append(p)

        elif p.is_dir():
            t1 = len(flattened_list)

            if recursive:
                flattened_list.extend([
                    q for q in p.rglob("*") if q.is_file()
                ])
            else:
                flattened_list.extend([
                    q for q in p.glob("*") if q.is_file()
                ])

            t2 = len(flattened_list)
            if t2 - t1 == 0:
                continue

    if len(flattened_list) == 0:
        raise FileNotFoundError(f"could not find any file at given position(s)")

    return list(dict.fromkeys(flattened_list))

if not Path(args.input).is_dir():
    raise NotADirectoryError(f"could not find input directory at '{Path(args.input).resolve()}'")
input_files: list[Path] = flatten_paths([Path(args.input).resolve()], True)
output_files: list[Path] = [Path(args.output).resolve() / f"{args.stego_tool}-{i.name}" for i in input_files]
if not Path(args.output).is_dir():
    os.makedirs(args.output)
if not Path(args.output).is_dir():
    raise IOError(f"could not create directory '{Path(args.output).resolve()}'")
message_file: Path = Path(args.message).resolve()
if not message_file.is_file():
    raise FileNotFoundError(f"could not find message file at '{message_file}'")

stego_tool: StegoTool = [i for i in STEGO_TOOLS if i.stego_tool == args.stego_tool][0]

if (stego_tool.key_required and args.key is None):
    raise ValueError(f"{stego_tool.stego_tool} requires a key parameter")
if (args.timeout < 3):
    raise ValueError(f"timeout can not be smaller than 3")

stego_tool.apply_execution_context()

with alive_bar(len(input_files), title=f"stego-gen/{args.stego_tool}") as pbar:
    for i, path in enumerate(input_files):
        exec_str: str = stego_tool.exec_str
        output_file: str = str(output_files[i]) + ("" if stego_tool.outfile_extension is None else stego_tool.outfile_extension)
        exec_str = exec_str.replace("<INPUT>", str(input_files[i]))
        exec_str = exec_str.replace("<MESSAGE>", str(message_file))
        exec_str = exec_str.replace("<OUTPUT>", output_file)
        if args.key is not None:
            exec_str = exec_str.replace("<KEY>", args.key)
        try:
            subprocess.check_output(exec_str, stderr=subprocess.STDOUT, timeout=args.timeout, shell=True)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"{stego_tool.stego_tool}-Error: {e}")
            if args.discard_error_outfile:
                try:
                    os.remove(output_file)
                except FileNotFoundError:
                    pass
                try:
                    os.remove(output_file + ".qdf")
                except FileNotFoundError:
                    pass

        pbar(1)
