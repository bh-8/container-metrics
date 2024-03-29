import abc
import datetime
import json
from pathlib import Path
from typing import List

class AbstractContainerFormat(abc.ABC):
    def __init__(self, file_path: Path, file_mime_type: str, file_mime_info: List[str]) -> None:
        # abstract properties
        self.file_path: Path = file_path
        self.file_mime_type: str = file_mime_type
        self.file_format_id: str = file_mime_info[0]
        self.file_format_name: str = file_mime_info[1]

        # read file bytes
        self.file_data: bytes = None
        with open(self.file_path, "rb") as file_handle:
            self.file_data = file_handle.read()
        
        # read format structure preset
        self.format_dict: dict = None
        with open("./abstract_container_format.json") as json_handle:
            self.format_dict = json.loads(json_handle.read())

        # set format-specific preset
        with open(f"./container_formats/{self.file_format_id}.json") as json_handle:
            self.format_dict["format_structure"] = json.loads(json_handle.read())

        self.format_dict["examination"]["timestamp_t0"] = datetime.datetime.now().isoformat()
        self.format_dict["examination"]["file_name"] = self.file_path.name
        self.format_dict["examination"]["file_size"] = len(self.file_data)
        self.format_dict["examination"]["mime_type"] = self.file_mime_type
        self.format_dict["examination"]["format_name"] = self.file_format_name

    def parse(self) -> None:
        raise NotImplementedError("parsing process unimplemented for this file type")

    def get_format_dict(self) -> dict:
        self.format_dict["examination"]["timestamp_t1"] = datetime.datetime.now().isoformat()
        return self.format_dict
