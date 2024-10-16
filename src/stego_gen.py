"""
stego_gen.py

"""

from alive_progress import alive_bar
import argparse
import mp3stego
from pathlib import Path
import os
import shutil
import subprocess
import sys
import time
import json

class ToolMp3StegoLib():
    def __init__(self) -> None:
        self.stego = mp3stego.Steganography(quiet=True)
    def embed(self, cover: Path, stego: Path, message: Path) -> bool:
        try:
            with open(message, "r") as handle:
                self.stego.hide_message(str(cover), str(stego), handle.read())
                handle.close()
                return True
        except:
            return False

class StegoTool():
    def __init__(self, stego_tool: str, executable: str, parameters: list[str], context_path: Path = Path("/home/stego-gen"), outfile_extension: str | None = None) -> None:
        self.__stego_tool: str = stego_tool
        self.__executable: str = executable
        self.__parameters: list[str] = parameters
        self.__context_path: Path = context_path
        self.__outfile_extension: str | None = outfile_extension

        if (self.__executable is not None) and (not Path(self.__executable).exists()):
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
        return " ".join([self.__executable] + [f"\"{p}\"" for p in self.__parameters])
    @property
    def key_required(self) -> bool:
        return "<KEY>" in self.__parameters
    @property
    def internal_tool(self) -> bool:
        return self.executable is None
    @property
    def outfile_extension(self) -> str | None:
        return self.__outfile_extension
STEGO_TOOLS=[
    StegoTool("boobytrappdf", "/home/stego-gen/venv/bin/python3", ["/opt/booby-trap-pdf/booby-trap-PDF.py", "bin", "<INPUT>", "<OUTPUT>", "<MESSAGE>"]),
    StegoTool("f5", "/usr/bin/xvfb-run", ["-a", "/usr/bin/java", "--add-exports", "java.base/sun.security.provider=ALL-UNNAMED", "-mx100M", "Embed", "-e", "<MESSAGE>", "-p", "<KEY>", "<INPUT>", "<OUTPUT>"], context_path=Path("/opt/F5-steganography")),
    StegoTool("hstego", "/home/stego-gen/venv/bin/python3", ["/opt/hstego/hstego.py", "embed", "<MESSAGE>", "<INPUT>", "<OUTPUT>", "<KEY>"], context_path=Path("/opt/hstego")),
    StegoTool("jsteg", "/opt/jsteg-linux-amd64", ["hide", "<INPUT>", "<MESSAGE>", "<OUTPUT>"]),
    StegoTool("mp3stego", "/usr/bin/wine", ["/opt/Encode.exe", "-E", "<MESSAGE>", "-P", "<KEY>", "<INPUT>", "<OUTPUT>"], outfile_extension=".mp3"),
    #StegoTool("mp3stegolib", None, ["<INPUT>", "<OUTPUT>", "<MESSAGE>"]),
    StegoTool("pdfhide", "/opt/pdf_hide/pdf_hide", ["-o", "<OUTPUT>", "-k", "<KEY>", "embed", "<MESSAGE>", "<INPUT>"]),
    StegoTool("pdfstego", "/opt/PDFStego/pdfstego", ["-e", "-c", "<INPUT>", "-m", "<MESSAGE>", "-p", "<KEY>", "-s", "<OUTPUT>"]),
    StegoTool("stegosuite", "/usr/bin/xvfb-run", ["-a", "/usr/bin/stegosuite", "embed", "-o", "<OUTPUT>", "-f", "<MESSAGE>", "-k", "<KEY>", "<INPUT>"]),
    StegoTool("tamp3r", "/opt/tamp3r/tamp3r", ["-s", "<MESSAGE_STR>", "-o", "<OUTPUT>", "<INPUT>"])
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
    Path(args.output).mkdir(parents=True)
message_file: Path = Path(args.message).resolve()
if not message_file.is_file():
    raise FileNotFoundError(f"could not find message file at '{message_file}'")
message_str: str = None
with open(message_file, "r") as handle:
    message_str = handle.read()
    handle.close()

stego_tool: StegoTool = [i for i in STEGO_TOOLS if i.stego_tool == args.stego_tool][0]

if (stego_tool.key_required and args.key is None):
    raise ValueError(f"{stego_tool.stego_tool} requires a key parameter")
if (args.timeout < 3):
    raise ValueError(f"timeout can not be smaller than 3")

log_data: dict = {
    "timestamp": time.time(),
    "stego_tool": stego_tool.stego_tool,
    "message_file": str(message_file),
    "key": args.key if stego_tool.key_required else None,
    "stego_gen": []
}
log_file: Path = Path(args.output).resolve() / f"_{stego_tool.stego_tool}-{log_data['timestamp']}.json"

stego_tool.apply_execution_context()
with alive_bar(len(input_files), title=f"stego-gen/{args.stego_tool}") as pbar:
    for i, path in enumerate(input_files):
        log_item: dict = {
            "cover": str(path),
            "stego": None,
            "error": None
        }

        output_file: str = str(output_files[i]) + ("" if stego_tool.outfile_extension is None else stego_tool.outfile_extension)

        if stego_tool.internal_tool:
            # assuming the only internal tool is ToolMp3StegoLib
            mp3stegolib: ToolMp3StegoLib = ToolMp3StegoLib()
            if mp3stegolib.embed(input_files[i], Path(output_file), message_file) and Path(output_file).is_file() and os.stat(output_file).st_size > 0:
                log_item["stego"] = output_file
            else:
                log_item["error"] = "Output of stego tool was null."
                if args.discard_error_outfile:
                    try:
                        os.remove(output_file)
                    except FileNotFoundError:
                        pass
        else:
            exec_str: str = stego_tool.exec_str
            exec_str = exec_str.replace("<INPUT>", str(input_files[i]))
            exec_str = exec_str.replace("<MESSAGE>", str(message_file))
            exec_str = exec_str.replace("<MESSAGE_STR>", message_str)
            exec_str = exec_str.replace("<OUTPUT>", output_file)
            if args.key is not None:
                exec_str = exec_str.replace("<KEY>", args.key)
            try:
                subprocess.check_output(exec_str, stderr=subprocess.STDOUT, timeout=args.timeout, shell=True)
                if Path(output_file).is_file() and os.stat(output_file).st_size > 0:
                    log_item["stego"] = output_file
                else:
                    stegosuite_path: Path = Path(input_files[i]).parent / f"{Path(input_files[i]).stem}_embed.{Path(input_files[i]).name.split('.')[-1]}"
                    if stegosuite_path.is_file() and os.stat(str(stegosuite_path)).st_size > 0:
                        shutil.move(stegosuite_path, output_file)
                        log_item["stego"] = output_file
                    else:
                        raise FileNotFoundError("Output of stego tool was null.")

            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
                print(f"{stego_tool.stego_tool}-Error: {e}")
                log_item["error"] = str(e)
                if args.discard_error_outfile:
                    try:
                        os.remove(output_file)
                    except FileNotFoundError:
                        pass
                try:
                    os.remove(str(input_files[i]) + ".qdf")
                except FileNotFoundError:
                    pass

        log_data["stego_gen"].append(log_item)
        with open(log_file, "w") as handle:
            json.dump(log_data, handle)
            handle.close()
        pbar(1)
