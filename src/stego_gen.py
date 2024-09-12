"""
stego_gen.py

"""

from alive_progress import alive_bar
import argparse
from pathlib import Path
import os
import subprocess
import sys



class StegoTool():
    def __init__(self, stego_tool: str, executable_path: str, parameters: list[str]) -> None:
        self.__stego_tool: str = stego_tool
        self.__executable_path: Path = Path(executable_path).resolve()
        self.__parameters: list[str] = [f"'{p}'" for p in parameters]

        if not self.__executable_path.exists():
            raise FileNotFoundError()

    @property
    def stego_tool(self) -> str:
        return self.__stego_tool
    @property
    def executable_path(self) -> Path:
        return self.__executable_path
    @property
    def exec_str(self) -> str:
        return " ".join([str(self.__executable_path)] + self.__parameters)
STEGO_TOOLS=[
    StegoTool("jsteg", "/opt/jsteg-linux-amd64", ["hide", "<INPUT>", "<MESSAGE>", "<OUTPUT>"])
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
    help="key string"
)
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
key_string: str = args.key



stego_tool: StegoTool = [i for i in STEGO_TOOLS if i.stego_tool == args.stego_tool][0]
with alive_bar(len(input_files), title=f"stego-gen/{args.stego_tool}") as pbar:
    for i, path in enumerate(input_files):
        exec_str: str = stego_tool.exec_str
        exec_str = exec_str.replace("<INPUT>", str(input_files[i]))
        exec_str = exec_str.replace("<MESSAGE>", str(message_file))
        exec_str = exec_str.replace("<OUTPUT>", str(output_files[i]))
        exec_str = exec_str.replace("<KEY>", key_string)
        try:
            subprocess.check_output(exec_str, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            print(f"{stego_tool.stego_tool}-Error: {e}")
        pbar(1)
