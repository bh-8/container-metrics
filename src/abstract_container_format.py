import abc
import json
from pathlib import Path

class AbstractContainerFormat(abc.ABC):
    def __init__(self, file_path: Path, format_id: str) -> None:
        self.file_path: Path = file_path

        # read file bytes
        self.file_data: bytes = None
        with open(self.file_path, "rb") as file_handle:
            self.file_data = file_handle.read()
        
        # read format structure preset
        self.format_structure: dict = None
        with open("./abstract_container_format.json") as json_handle:
            self.format_structure = json.loads(json_handle.read())

        # set format-specific preset
        with open(f"./container_formats/{format_id}.json") as json_handle:
            self.format_structure["container_metrics"] = json.loads(json_handle.read())

        # [TODO] fill values of abstract preset

    def parse(self) -> None:
        raise NotImplementedError("parsing process unimplemented for this file type")

    def get_format_structure(self) -> dict:
        return self.format_structure
