from pathlib import Path
from json import loads
from abstract_container_format import AbstractContainerFormat

class ImageJpegFormat(AbstractContainerFormat):
    def __init__(self, file_path: Path) -> None:
        super().__init__(file_path, "image_jpeg")

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
