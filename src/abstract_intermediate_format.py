import abc

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
class ContainerSection():
    def __init__(self, position: int, mime_type: str, analysis_depth: int) -> None:
        self._section: dict = {
            "position": position,
            "length": None,
            "mime_type": mime_type,
            "mime_name": None,
            "analysis_depth": analysis_depth
        }

    def set_length(self, length: int) -> None:
        self._section["length"] = length

    def set_mime_name(self, mime_name: str) -> None:
        self._section["mime_name"] = mime_name

    def set_segment(self, key: str, segment: ContainerSegment) -> None:
        self._section[key] = segment.get_list()

    def get_section(self) -> dict:
        return self._section

class AbstractStructureAnalysis(abc.ABC):
    def __init__(self) -> None:
        pass

    def process_section(self, section: ContainerSection) -> ContainerSection:
        raise NotImplementedError("no implementation available")