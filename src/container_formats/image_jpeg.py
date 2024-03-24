from pathlib import Path
from json import loads
from abstract_container_format import AbstractContainerFormat

class ImageJpegFormat(AbstractContainerFormat):
    def __init__(self, file_path: Path, file_format_id: str, file_mime_type: str) -> None:
        super().__init__(file_path, file_format_id, file_mime_type)

    def parse(self) -> None:
        pass

#{
#    "name": "Portable Document Format",
#    "mime_type": "application/pdf"
#}
#{
#    "name": "JPEG File Interchange Format",
#    "mime_type": "image/jpeg"
#}
