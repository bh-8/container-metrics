import abc
import json
from pathlib import Path

class AbstractContainerFormat(abc.ABC):
    def __init__(self, file_path: Path, file_format_id: str, file_mime_type: str) -> None:
        # abstract properties
        self.file_path: Path = file_path
        self.file_format_id: str = file_format_id
        self.file_mime_type: str = file_mime_type

        # read file bytes
        self.file_data: bytes = None
        with open(self.file_path, "rb") as file_handle:
            self.file_data = file_handle.read()
        
        # read format structure preset
        self.format_structure: dict = None
        with open("./abstract_container_format.json") as json_handle:
            self.format_structure = json.loads(json_handle.read())

        # set format-specific preset
        with open(f"./container_formats/{self.file_format_id}.json") as json_handle:
            self.format_structure["container_metrics"] = json.loads(json_handle.read())

        # [TODO] fill values of abstract preset
        self.format_structure["file_info"]["name"] = self.file_path.name
        self.format_structure["file_info"]["mime_type"] = self.file_mime_type
        self.format_structure["file_info"]["size"] = len(self.file_data)

    def parse(self) -> None:
        raise NotImplementedError("parsing process unimplemented for this file type")

    def get_format_structure(self) -> dict:
        return self.format_structure
