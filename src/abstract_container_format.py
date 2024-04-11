from container_formats import *
import datetime
from pathlib import Path
from static_utils import *
from typing import List

class AbstractContainerFormat():
    def __init__(self, mime_type_dict: dict) -> None:
        # abstract properties
        self.logger = StaticLogger.get_logger()
        self.file_path: Path = None
        self.file_data: bytes = None
        self.mime_type_dict: dict = mime_type_dict

        # read format structure preset
        self.format_dict: dict = {
            "meta": {
                "file_name": None,
                "file_size": None,
                "timestamp_t0": None,
                "timestamp_t1": None
            },
            "data": {}
        }

        # set start timestamp
        self.format_dict["meta"]["timestamp_t0"] = datetime.datetime.now().isoformat()

    def read_file(self, file_path: Path):
        self.logger.debug(f"reading file...")

        self.file_path = file_path
        self.format_dict["meta"]["file_name"] = self.file_path.name

        with open(self.file_path, "rb") as file_handle:
            self.file_data = file_handle.read()
            file_handle.close()

            self.format_dict["meta"]["file_size"] = len(self.file_data)

    def parse(self, parsing_layer: int, position: int = 0, length: int = None) -> None:
        if self.file_data is None:
            raise AssertionError("file data uninitialized")
        if parsing_layer >= 3: # TODO: implement switch to set maximum depth
            self.logger.warn(f"maximum parsing depth exceeded")
            return

        # if no length is given use all available data
        if length is None:
            length = len(self.file_data) - position
            if length < 0:
                raise AssertionError("can not parse a negative amount of bytes")

        _data: bytes = self.file_data[position:position+length]
        self.logger.debug(f"parsing of {len(_data)} bytes initiated at file position {position}")

        # determine mime info
        _mime_type: str = MIMEDetector.from_bytes_by_magic(_data)

        _parsing_dict = {
            "position": position,
            "length": length,
            "mime_type": _mime_type,
            "raw": str(_data)
        }

        # quit parsing if mime type not supported
        if not _mime_type in self.mime_type_dict:
            if not "unsupported" in self.format_dict["data"]:
                self.format_dict["data"]["unsupported"] = []
            self.format_dict["data"]["unsupported"].append(_parsing_dict)
            self.logger.warn(f"no mapping information available for mime-type '{_mime_type}'")
            return

        _mime_type_info: List[str] = self.mime_type_dict[_mime_type]
        _mime_id: str = _mime_type_info[0]

        # check existence of required implementation
        _class_label: str = f"{to_camel_case(_mime_id)}Format"
        if not _class_label in globals():
            self.logger.error(f"could not find class '{_class_label}', expected definition in '{_mime_id}.py'")
            return

        # load required format parser
        _format_specific_instance = globals()[_class_label]()
        self.logger.debug(f"accessing specific implementation in class '{_class_label}'")
        _parsing_dict["structure"] = _format_specific_instance.format_specific_parsing(self, _data, parsing_layer, position)

        if not _mime_id in self.format_dict["data"]:
            self.format_dict["data"][_mime_id] = []
        self.format_dict["data"][_mime_id].append(_parsing_dict)
        self.logger.debug(f"appended results to dictionary")

    def get_format_dict(self) -> dict:
        # set end timestamp
        self.format_dict["meta"]["timestamp_t1"] = datetime.datetime.now().isoformat()
        return self.format_dict
