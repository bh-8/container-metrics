"""
abstract_structure_mapping.py

included in every file in ./container_formats/*
"""

# IMPORTS

import abc
import logging
log = logging.getLogger(__name__)

# STRUCTURE MAPPING COMPONENTS

class ContainerFragment():
    def __init__(self, offset: int, length: int) -> None:
        # use of dictionary enables mapping of nested objects
        self.__attributes: dict = {
            "offset": offset,
            "length": length
        }

    # value has to be JSON-serializable!
    def set_attribute(self, key: str, value: any) -> None:
        if value == None and key in self.__attributes:
            del self.__attributes[key]
        else:
            self.__attributes[key] = value

    @property
    def as_dictionary(self) -> dict:
        return self.__attributes

class ContainerSegment():
    def __init__(self, key: str) -> None:
        self.__key: str = key
        self.__list: list[ContainerFragment] = []

    def add_fragment(self, fragment: ContainerFragment) -> None:
        self.__list.append(fragment)

    @property
    def key(self) -> str:
        return self.__key
    @property
    def to_list(self) -> list[dict]:
        return [f.as_dictionary for f in self.__list]

class ContainerSection():
    def __init__(self, recursive: any, position: int, data: bytes, mime_type: str, analysis_depth: int) -> None:
        self.__recursive: any = recursive # container_metrics.py: StructureMapping instance
        self.__data = data
        self.__attribs: dict = {
            "position": position,
            "length": None,
            "mime_type": mime_type,
            "mime_name": None,
            "analysis_depth": analysis_depth
        }

    def __build_coverage_list(self) -> list:
        if not "content" in self.__attribs:
            return []
        coverage_list: list[dict] = []
        [[coverage_list.append({"o": f["offset"], "l": f["length"]}) for f in self.__attribs["content"][k]] for k in self.__attribs["content"].keys()]
        return coverage_list
    def new_analysis(self, offset: int, length: int | None = None) -> None:
        self.__recursive.queue_analysis(self.__attribs["position"] + offset, self.__attribs["analysis_depth"] + 1, length)
    def new_volatile_analysis(self, volatile_data: bytes) -> None:
        self.__recursive.queue_volatile_analysis(volatile_data, self.__attribs["analysis_depth"] + 1)
    def add_segment(self, segment: ContainerSegment) -> None:
        if not "content" in self.__attribs:
            self.__attribs["content"] = {}
        if not segment.key in self.__attribs["content"]:
            self.__attribs["content"][segment.key] = []
        self.__attribs["content"][segment.key] = self.__attribs["content"][segment.key] + segment.to_list
    def calculate_length(self) -> None:
        _max: int = 0
        for c in self.__build_coverage_list():
            s = c["o"] + c["l"]
            if s > _max:
                _max = s
        self.set_length(_max)
    def set_length(self, length: int) -> None:
        self.__attribs["length"] = length
    def set_mime_name(self, mime_name: str) -> None:
        self.__attribs["mime_name"] = mime_name

    @property
    def data(self) -> bytes:
        return self.__data
    @property
    def length(self) -> int | None:
        return self.__attribs["length"]
    @property
    def as_dictionary(self) -> dict:
        return self.__attribs

# ABSTRACT CONTAINER FORMAT

class AbstractStructureAnalysis(abc.ABC):
    def __init__(self) -> None:
        pass

    def process(self, section: ContainerSection) -> ContainerSection:
        raise NotImplementedError("no implementation available")

class Coverage():
    def __init__(self, identifier: str, data: list[dict], coverage_limit: int | None) -> None:
        if coverage_limit is None:
            raise ValueError("coverage section length is null")

        self.__uncovered_segment: ContainerSegment = ContainerSegment(identifier)

        if len(data) == 0:
            self.__uncovered_segment.add_fragment(ContainerFragment(0, coverage_limit))
            return

        # sort
        coverage_data = sorted(data, key=lambda d: d["o"])
        
        # coverage algorithm
        coverage_offset: int = 0
        for c in coverage_data:
            if c["o"] >= coverage_limit:
                break
            elif coverage_offset == c["o"]:
                coverage_offset = coverage_offset + c["l"]
            elif coverage_offset < c["o"]:
                gap: int = c["o"] - coverage_offset
                self.__uncovered_segment.add_fragment(ContainerFragment(coverage_offset, gap))
                coverage_offset = coverage_offset + gap + c["l"]
            else:
                # case for double-covered segments -> e.g. comments inside indirect objects/dictionaries/arrays/...
                continue

        if coverage_offset < coverage_limit:
            self.__uncovered_segment.add_fragment(ContainerFragment(coverage_offset, coverage_limit - coverage_offset))

    @classmethod
    def from_section(cls, section: ContainerSection):
        coverage_data: list[dict] = []
        if "content" in section.as_dictionary:
            for k in section.as_dictionary["content"].keys():
                for f in section.as_dictionary["content"][k]:
                    coverage_data.append({"o": f["offset"], "l": f["length"]})
        log.info(f"determining coverage for section of {section.length} bytes...")
        return cls("uncovered", coverage_data, section.length)

    @property
    def as_uncovered_segment(self) -> ContainerSegment:
        return self.__uncovered_segment
