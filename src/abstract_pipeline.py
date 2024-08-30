"""
abstract_pipeline.py

included in every file in ./container_formats/*
"""

# IMPORTS

import abc
import jmespath
from pathlib import Path
import logging
log = logging.getLogger(__name__)

# ABSTRACT PIPELINE FORMAT

class AbstractPipeline(abc.ABC):
    def __init__(self, pipeline: str, document: dict, raw: bytes, pipeline_parameters: dict) -> None:
        self.__pipeline: str = pipeline
        self.__document: dict = document
        self.__raw: bytes = raw
        self.__pipeline_parameters: dict = pipeline_parameters

    def process(self) -> None:
        raise NotImplementedError("processing not implemented")
    def get_raw_document(self, hex: bool = False) -> dict:
        raw_document: dict = self.__document
        # insert fragment data
        for i in range(len(raw_document["data"])):
            s: dict = raw_document["data"][i]["content"]
            for k in s.keys():
                for j in range(len(s[k])):
                    f: dict = raw_document["data"][i]["content"][k][j]
                    position: int = raw_document["data"][i]["position"] + f["offset"]
                    end: int = position + f["length"]
                    data: bytes = self.__raw[position:end]
                    raw_document["data"][i]["content"][k][j]["raw"] = data.hex() if hex else f"{data}"

        log.debug("inserted raw data to document for further pipelining")
        return raw_document
    def get_outfile_path(self, outid: str) -> str:
        return self.output_path / f"{self.output_id}-{outid}.{self.__pipeline}"
    def jmesq(self, query_str: str) -> dict:
        return jmespath.search(query_str, self.__document)
    def stringify(self, chars: list[str], index: int, data: any) -> str:
        # if index < len(chars):
        if type(data) is list:
            return chars[index].join([(self.stringify(chars, index + 1, i) if index + 1 < len(chars) else f"<{type(i).__name__}>") if (type(i) is dict or type(i) is list) else f"{i}" for i in data])
        if type(data) is dict:
            return chars[index].join([f"{k}={{" + ((self.stringify(chars, index + 1, data[k]) if index + 1 < len(chars) else f"<{type(data[k]).__name__}>") if (type(data[k]) is dict or type(data[k]) is list) else f"{data[k]}") + f"}}" for k in data.keys()])
        return str(data)

    @property
    def document(self) -> dict:
        return self.__document
    @property
    def raw(self) -> dict:
        return self.__raw
    @property
    def pipeline_parameters(self) -> dict:
        return self.__pipeline_parameters
    @property
    def output_id(self) -> str:
        return f"{self.__document['_id']}_{Path(self.__document['meta']['file']['name'])}"
    @property
    def output_path(self) -> Path:
        path: Path = Path(f"./io/_{self.__pipeline}").resolve()
        path.mkdir(exist_ok=True)
        return path
