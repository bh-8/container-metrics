"""
abstract_pipeline.py

included in every file in ./container_formats/*
"""

# IMPORTS

import abc
from pathlib import Path
from static_utils import StaticLogger

# ABSTRACT PIPELINE FORMAT

class AbstractPipeline(abc.ABC):
    def __init__(self, pipeline: str, document: dict, raw: bytes) -> None:
        self.logger = StaticLogger.get_logger()
        self.__pipeline: str = pipeline
        self.__document: dict = document
        self.__raw: bytes = raw

    def process(self) -> None:
        raise NotImplementedError("processing not implemented")
    def get_raw_document(self, hex: bool = False) -> dict:
        raw_document: dict = self.__document
        # insert fragment data
        for i in range(len(raw_document["sections"])):
            s: dict = raw_document["sections"][i]["segments"]
            for k in s.keys():
                for j in range(len(s[k])):
                    f: dict = raw_document["sections"][i]["segments"][k][j]
                    position: int = raw_document["sections"][i]["position"] + f["offset"]
                    end: int = position + f["length"]
                    data: bytes = self.__raw[position:end]
                    raw_document["sections"][i]["segments"][k][j]["raw"] = data.hex() if hex else f"{data}"

        return raw_document

    @property
    def document(self) -> dict:
        return self.__document
    @property
    def raw(self) -> dict:
        return self.__raw
    @property
    def output_id(self) -> str:
        return f"{self.__document['_id']}_{Path(self.__document['meta']['file']['name'])}"
    @property
    def output_path(self) -> Path:
        path: Path = Path(f"./io/_{self.__pipeline}").resolve()
        path.mkdir(exist_ok=True)
        return path
