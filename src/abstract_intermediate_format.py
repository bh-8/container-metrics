import abc

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
    def __init__(self, position: int, mime_type: str) -> None:
        self._section: dict = {
            "position": position,
            "length": None,
            "mime_type": mime_type,
            "parsing_depth": None
        }

    def set_length(self, length: int) -> None:
        self._section["length"] = length

    def set_parsing_depth(self, parsing_depth: int) -> None:
        self._section["parsing_depth"] = parsing_depth

    def set_segment(self, key: str, segment: ContainerSegment) -> None:
        self._section[key] = segment.get_list()

    def get_dictionary(self) -> dict:
        return self._section

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Abstract Structure Analyzer / Parser

# each format has to be implemented by a specialized instance -> StructureAnalyzer builds a ContainerSection
class AbstractStructureAnalyzer(abc.ABC):
    # TODO: length is unknown!!! -> length has to be handled manually get_parsing_end_pos()
    def __init__(self, position: int, length: int, mime_type: str, parsing_depth: int) -> None:
        self._section: ContainerSection = ContainerSection(position, mime_type)
        self._section.set_length(length)
        self._section.set_parsing_depth(parsing_depth)

    def analyze(self) -> None:
        raise NotImplementedError("member function 'analyze' not implemented")

    def get_structure(self) -> dict:
        return self._section.get_dictionary()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# IntermediateFormat consists of one or more ContainerSections plus MetaData;
# it also decides which implementation to use for a specific mime-type (abstract_container_format/AbstractContainerFormat)

class IntermediateFormat():
    def __init__(self) -> None:
        pass
