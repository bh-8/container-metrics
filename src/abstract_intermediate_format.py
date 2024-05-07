import abc
from static_utils import StaticLogger

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
    def __init__(self, recursive: any, position: int, data: bytes, mime_type: str, analysis_depth: int) -> None:
        self._recursive = recursive
        self._data = data
        self._section: dict = {
            "position": position,
            "length": None,
            "mime_type": mime_type,
            "mime_name": None,
            "analysis_depth": analysis_depth
        }

    def new_analysis(self, offset: int, length: int | None = None) -> None:
        self._recursive.queue_analysis(self._section["position"] + offset, self._section["analysis_depth"] + 1, length)

    def get_position(self) -> int:
        return self._section["position"]

    def get_length(self) -> int | None:
        return self._section["length"]

    def set_length(self, length: int) -> None:
        self._section["length"] = length

    def set_mime_name(self, mime_name: str) -> None:
        self._section["mime_name"] = mime_name

    def add_segment(self, key: str, segment: ContainerSegment) -> None:
        if not "segments" in self._section:
            self._section["segments"] = {}
        if not key in self._section["segments"]:
            self._section["segments"][key] = []
        self._section["segments"][key] = self._section["segments"][key] + segment.get_list()

    def get_data(self) -> bytes:
        return self._data

    def get_section(self) -> dict:
        return self._section

    def get_coverage_list(self) -> list:
        if not "segments" in self._section:
            return []
        coverage_list: list[dict] = []
        [[coverage_list.append({"offset": f["offset"], "length": f["length"]}) for f in self._section["segments"][k]] for k in self._section["segments"].keys()]
        return coverage_list

    def calculate_length(self) -> None:
        _max: int = 0
        for c in self.get_coverage_list():
            s = c["offset"] + c["length"]
            if s > _max:
                _max = s
        self.set_length(_max)

class AbstractStructureAnalysis(abc.ABC):
    def __init__(self) -> None:
        self.logger = StaticLogger.get_logger()

    def process_section(self, section: ContainerSection) -> ContainerSection:
        raise NotImplementedError("no implementation available")

class Coverage():
    def __init__(self, data: list[dict], position: int, coverage_limit: int | None) -> None:
        if coverage_limit is None:
            raise ValueError("coverage section length is null")

        self._segment: ContainerSegment = ContainerSegment()

        if len(data) == 0:
            self._segment.add_fragment(ContainerFragment(position, coverage_limit))
            return

        # sort
        _coverage_data = sorted(data, key=lambda d: d["o"])
        
        # coverage algorithm
        coverage_offset: int = 0
        for c in _coverage_data:
            if c["o"] >= coverage_limit:
                break
            elif coverage_offset == c["o"]:
                coverage_offset = coverage_offset + c["l"]
            elif coverage_offset < c["o"]:
                _gap: int = c["o"] - coverage_offset
                self._segment.add_fragment(ContainerFragment(coverage_offset, _gap))
                coverage_offset = coverage_offset + _gap + c["l"]
            else:
                # case for double-covered segments -> e.g. comments inside indirect objects/dictionaries/arrays/...
                continue

        if coverage_offset < coverage_limit:
            self._segment.add_fragment(ContainerFragment(coverage_offset, coverage_limit - coverage_offset))

    @classmethod
    def from_section(cls, section: ContainerSection):
        _coverage_data: list[dict] = []
        if "segments" in section.get_section():
            for k in section.get_section()["segments"].keys():
                for f in section.get_section()["segments"][k]:
                    _coverage_data.append({"o": f["offset"], "l": f["length"]})
        return cls(_coverage_data, section.get_position(), section.get_length())

    def get_uncovered_segment(self) -> ContainerSegment:
        return self._segment
