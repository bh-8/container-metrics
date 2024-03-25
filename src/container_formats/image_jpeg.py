from abstract_container_format import AbstractContainerFormat
from pathlib import Path
from typing import List

class ImageJpegFormat(AbstractContainerFormat):
    def __init__(self, file_path: Path, file_mime_type: str, file_mime_info: List[str]) -> None:
        super().__init__(file_path, file_mime_type, file_mime_info)

    def parse(self) -> None:
        #self.file_data
        self.format_dict["format_structure"]["key"] = "Hello, World!"
