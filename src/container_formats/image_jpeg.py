from abstract_container_format import AbstractContainerFormat
from pathlib import Path
from typing import List

class ImageJpegFormat(AbstractContainerFormat):
    def __init__(self, file_path: Path, file_mime_info: List[str], file_mime_type: str) -> None:
        super().__init__(file_path, file_mime_info, file_mime_type)

    def parse(self) -> None:
        #self.file_data
        self.format_structure["container_metrics"]["key"] = "Hello, World!"
