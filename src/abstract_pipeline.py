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
        self.pipeline: str = pipeline
        self.document: dict = document
        self.raw: bytes = raw
        self.logger = StaticLogger.get_logger()
        self.output_path: Path = Path(f"./io/_{pipeline}").resolve()
        self.output_path.mkdir(exist_ok=True)
        self.output_id: str = f"{self.document['_id']}_{Path(self.document['meta']['file']['name'])}"

    def process(self) -> None:
        raise NotImplementedError("processing not implemented")

    def get_raw_document(self, hex: bool = False) -> dict:
        _raw_doc: dict = self.document
        # insert fragment data
        for i in range(len(_raw_doc["sections"])):
            s: dict = _raw_doc["sections"][i]["segments"]
            for k in s.keys():
                for j in range(len(s[k])):
                    f: dict = _raw_doc["sections"][i]["segments"][k][j]
                    position: int = _raw_doc["sections"][i]["position"] + f["offset"]
                    end: int = position + f["length"]
                    data: bytes = self.raw[position:end]
                    _raw_doc["sections"][i]["segments"][k][j]["raw"] = data.hex() if hex else f"{data}"

        return _raw_doc
