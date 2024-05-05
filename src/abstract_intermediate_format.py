import abc
from pathlib import Path
from static_utils import StaticLogger, MIMEDetector, to_camel_case
import hashlib
import datetime
import os

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Intermediate Format Description

# replaces static_utils/ContainerItem
class ContainerFragment():
    def __init__(self, offset: int, length: int) -> None:
        # use of dictionary enables mapping of nested objects
        self._fragment: dict = {
            "offset": offset,
            "length": length
        }

    # value has to be JSON-serializable!
    def set_attribute(self, key: str, value: any) -> None:
        if value == None and key in self._fragment:
            del self._fragment[key]
        else:
            self._fragment[key] = value

    def get_dictionary(self) -> dict:
        return self._fragment
class ContainerSegment():
    def __init__(self) -> None:
        self._segment: list[ContainerFragment] = []

    def add_fragment(self, fragment: ContainerFragment) -> None:
        self._segment.append(fragment)

    def get_offset(self) -> int | None:
        if len(self._segment) < 1:
            return None
        return self._segment[0].get_dictionary()["offset"]

    def get_length(self) -> int | None:
        if len(self._segment) < 1:
            return None
        _f: dict = self._segment[-1].get_dictionary()
        return (_f["offset"] + _f["length"]) - self.get_offset()

    def get_list(self) -> list[dict]:
        return [f.get_dictionary() for f in self._segment]
class ContainerSection(): # section contains data with a specific mime-type
    def __init__(self, position: int, mime_type: str, analysis_depth: int) -> None:
        self._section: dict = {
            "position": position,
            "length": None,
            "mime_type": mime_type,
            "analysis_depth": analysis_depth
        }

    def set_length(self, length: int) -> None:
        self._section["length"] = length

    def set_segment(self, key: str, segment: ContainerSegment) -> None:
        self._section[key] = segment.get_list()

    def get_section(self) -> dict:
        return self._section

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Abstract Structure Analyzer / Parser
class AbstractStructureAnalysis(abc.ABC):
    def __init__(self) -> None:
        pass

    def process_section(self, section: ContainerSection) -> ContainerSection:
        return section

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# IntermediateFormat consists of one or more ContainerSections plus MetaData;
# it also decides which implementation to use for a specific mime-type (abstract_container_format/AbstractContainerFormat)

class IntermediateFormat():
    def __init__(self, file_path: Path, supported_mime_types: dict, analysis_depth_cap: int) -> None:
        self.logger: StaticLogger = StaticLogger.get_logger()
        self.file_path: Path = file_path
        self.supported_mime_types: dict = supported_mime_types
        self.analysis_depth_cap: int = analysis_depth_cap

        self.intermediate_format: dict = {
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
            "sections": []
        }

        self.file_data: bytes = None
        with open(file_path, "rb") as _fhandle:
            self.file_data = _fhandle.read()
        if self.file_data == None:
            raise IOError(f"could not read file '{file_path}'")

        # init analysis queue with initial entry
        self.analysis_queue: list[dict] = []
        self.queue_analysis(0)

        self.init_investigation_meta()
        self.file_structure_analysis()

    def queue_analysis(self, position: int, length: int | None = None, depth: int = 0) -> None:
        self.analysis_queue.append({
            "position": position,
            "length": length,
            "depth": depth
        })

    def init_investigation_meta(self) -> None:
        self.intermediate_format["meta"]["investigation"]["started"] = datetime.datetime.now().isoformat()

        self.intermediate_format["meta"]["file_name"] = self.file_path.name #TODO: remove later
        self.intermediate_format["meta"]["file"]["name"] = self.file_path.name
        self.intermediate_format["meta"]["file"]["size"] = len(self.file_data)
        self.intermediate_format["meta"]["file"]["type"]["magic"] = MIMEDetector.from_bytes_by_magic(self.file_data)
        self.intermediate_format["meta"]["file"]["type"]["extension"] = MIMEDetector.from_path_by_filename(self.file_path)
        self.intermediate_format["meta"]["file"]["sha256"] = hashlib.sha256(self.file_data).hexdigest()
        self.intermediate_format["meta"]["file"]["created"] = datetime.datetime.fromtimestamp(os.path.getctime(self.file_path)).isoformat()
        self.intermediate_format["meta"]["file"]["modified"] = datetime.datetime.fromtimestamp(os.path.getmtime(self.file_path)).isoformat()

    def file_structure_analysis(self) -> None:
        while len(self.analysis_queue) > 0:
            # read analysis parameters
            _analysis_position: int = self.analysis_queue[0]["position"]
            _analysis_length: int = len(self.file_data) - _analysis_position if self.analysis_queue[0]["length"] == None else self.analysis_queue[0]["length"]
            _analysis_depth: int = self.analysis_queue[0]["depth"]
            self.analysis_queue.pop(0)

            # abort at maximum structure analysis depth
            if _analysis_depth > self.analysis_depth_cap:
                continue

            # decide mime-type of data section
            _analysis_data: bytes = self.file_data[_analysis_position:_analysis_position+_analysis_length]
            _mime_type: str = MIMEDetector.from_bytes_by_magic(_analysis_data)

            # PDF special case
            _pdf_tag: int = self.file_data.find(b"\x25PDF-", _analysis_position)
            if not _mime_type in self.supported_mime_types and _pdf_tag > _analysis_position:
                self.queue_analysis(_pdf_tag)
                _analysis_length = _pdf_tag - _analysis_position
                _analysis_data: bytes = self.file_data[_analysis_position:_analysis_position+_analysis_length]

            _section: ContainerSection = ContainerSection(_analysis_position, _mime_type, _analysis_depth)

            # decide specialized analysis
            if _mime_type in self.supported_mime_types:
                _mime_type_info: list[str] = self.supported_mime_types[_mime_type]
                _mime_id: str = _mime_type_info[0]
                _mime_name: str = _mime_type_info[1]
                
                # check existence of required implementation
                _class_label: str = f"{to_camel_case(_mime_id)}Analysis"
                if not _class_label in globals():
                    raise NotImplementedError(f"could not find class '{_class_label}', expected definition in '{_mime_id}.py'")

                # initiate format specific analysis
                _format_specific_analysis = globals()[_class_label]()
                _section = _format_specific_analysis.process_section(_section)
            else:
                _section.set_length(_analysis_length)

            self.intermediate_format["sections"].append(_section.get_section())

    def get_intermediate_format(self) -> dict:
        self.intermediate_format["meta"]["investigation"]["finished"] = datetime.datetime.now().isoformat()
        return self.intermediate_format

    def get_file_data(self) -> bytes:
        return self.file_data
