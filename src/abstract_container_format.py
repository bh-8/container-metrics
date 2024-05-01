from container_formats import *
import datetime
import hashlib
import os
from pathlib import Path
from static_utils import *
import time
from typing import List

# class AbstractFileAnalyzer():

# class AbstractParser():

# aufbau der beschreibungen aus einheitlichen klassen, um coverage abstrakt zu lösen

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
                "file": {
                    "name": None,
                    "size": None,
                    "type": {
                        "magic": None,
                        "extension": None
                    },
                    "sha256": None,
                    "created": None,
                    "modified": None
                },
                "investigation": {
                    "started": None,
                    "finished": None
                },
                "gridfs": None
            },
            "data": {}
        }

        # set start timestamp
        self.format_dict["meta"]["investigation"]["started"] = datetime.datetime.now().isoformat()

    def read_file(self, file_path: Path):
        self.logger.debug(f"reading file...")

        self.file_path = file_path
        self.format_dict["meta"]["file_name"] = self.file_path.name
        self.format_dict["meta"]["file"]["name"] = self.file_path.name
        self.format_dict["meta"]["file"]["type"]["extension"] = MIMEDetector.from_path_by_filename(self.file_path)
        self.format_dict["meta"]["file"]["created"] = datetime.datetime.fromtimestamp(os.path.getctime(self.file_path)).isoformat()
        self.format_dict["meta"]["file"]["modified"] = datetime.datetime.fromtimestamp(os.path.getmtime(self.file_path)).isoformat()

        with open(self.file_path, "rb") as file_handle:
            self.file_data = file_handle.read()
            file_handle.close()

            self.format_dict["meta"]["file"]["size"] = len(self.file_data)
            self.format_dict["meta"]["file"]["sha256"] = hashlib.sha256(self.file_data).hexdigest()
            self.format_dict["meta"]["file"]["type"]["magic"] = MIMEDetector.from_bytes_by_magic(self.file_data)

    def parse(self, parsing_layer: int, position: int = 0, length: int = None) -> None:
        if self.file_data is None:
            raise AssertionError("file data uninitialized")
        if parsing_layer >= 3: # TODO: implement switch to set maximum depth
            self.logger.critical(f"maximum parsing depth exceeded")
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

        if not _mime_type in self.mime_type_dict and self.file_data.find(b"\x25PDF-", position) > -1:
            _mime_type = "application/pdf"

        _media_dict = {
            "pos": position,
            "len": length,
            "depth": parsing_layer,
            "mime_type": _mime_type
            #"raw": str(self.file_data[position:position+length]) #TODO
        }

        # quit parsing if mime type not supported
        if not _mime_type in self.mime_type_dict:
            if not "unknown" in self.format_dict["data"]:
                self.format_dict["data"]["unknown"] = []
            self.format_dict["data"]["unknown"].append(_media_dict)
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
        _media_dict = _format_specific_instance.format_specific_parsing(self, _media_dict, _data, parsing_layer + 1, position)

        if not _mime_id in self.format_dict["data"]:
            self.format_dict["data"][_mime_id] = []
        self.format_dict["data"][_mime_id].append(_media_dict)
        self.logger.debug(f"appended results to dictionary")

    def get_format_dict(self) -> dict:
        # set end timestamp
        self.format_dict["meta"]["investigation"]["finished"] = datetime.datetime.now().isoformat()
        return self.format_dict

    def get_file_data(self) -> bytes:
        return self.file_data
