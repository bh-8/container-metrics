"""
arff_pipeline.py

references:
    - 

"""

# IMPORTS

from functools import reduce
from itertools import groupby
import logging
from pathlib import Path
log = logging.getLogger(__name__)

from abstract_pipeline import AbstractPipeline

# GLOBAL STATIC MAPPINGS

ARFF_SEPARATORS = ["\n", ","]

# MODULE ENTRYPOINT

class ArffPipeline(AbstractPipeline):
    def __init__(self, document: dict, raw: bytes, pipeline_parameters: dict) -> None:
        super().__init__("arff", document, raw, pipeline_parameters)

    def __match_arff_type(self, type: str):
        match type:
            case "int" | "float":
                return "NUMERIC"
            case "str":
                return "STRING"
            case _:
                log.warning(f"encountered unsupported type '{type}', can not convert")
                return f"<TYPE_NOT_SUPPORTED ({type})>"

    def __extend_vector(self, size: int, vector: list):
        if len(vector) < size:
            return self.__extend_vector(size, vector + ["?"])
        return vector

    def process(self) -> None:
        query_result: list = self.jmesq(self.pipeline_parameters["jmesq"])
        if type(query_result) is list and len(query_result) == 0:
            return

        arff_str: str = "@RELATION iris"
        attribute_names: list[str] = str(self.pipeline_parameters["header"]).replace(" ", "").split(ARFF_SEPARATORS[1])

        query_result_extended: list = [self.__extend_vector(len(attribute_names), r) for r in query_result]

        for i, attr in enumerate(attribute_names):
            attr_values: list = [q[i] for q in query_result_extended]
            attr_types: list = [self.__match_arff_type(type(v).__name__) for v in attr_values if v != "?"]
            g = groupby(attr_types)
            if next(g, True) and not next(g, False):
                # type is determined
                log.warning(f"could not determine data type of column '{attribute_names[i]}', assume NUMERIC")
                arff_str = f"{arff_str}\n@ATTRIBUTE {attr} {attr_types[0] if len(attr_types) > 0 else 'NUMERIC'}"
            else:
                # type is not unique
                log.warning(f"values in column '{attribute_names[i]}' have distinct types")
                arff_str = f"{arff_str}\n@ATTRIBUTE {attr} <TYPE_NOT_UNIQUE>"

        arff_str = f"{arff_str}\n@DATA\n{self.stringify(ARFF_SEPARATORS, 0, query_result_extended)}"

        # write output
        arff_file: Path = self.get_outfile_path(self.pipeline_parameters['outid'])
        with open(arff_file, "w") as handle:
            log.info(f"writing output to '{arff_file}'...")
            handle.write(arff_str)
            handle.close()
