"""
csv_pipeline.py

references:
    - 

"""

# IMPORTS

import logging
from pathlib import Path
log = logging.getLogger(__name__)

from abstract_pipeline import AbstractPipeline

# GLOBAL STATIC MAPPINGS

CSV_SEPARATORS = ["\n", ",", ";", ":"]

# MODULE ENTRYPOINT

class CsvPipeline(AbstractPipeline):
    def __init__(self, document: dict, raw: bytes, pipeline_parameters: dict) -> None:
        super().__init__("csv", document, raw, pipeline_parameters)

    def process(self) -> None:
        query_result: list = self.jmesq(self.pipeline_parameters["jmesq"])
        if type(query_result) is list and len(query_result) == 0:
            return

        csv_str: str = self.pipeline_parameters["header"]  + "\n" + self.stringify(CSV_SEPARATORS, 0, query_result)

        # write output
        csv_file: Path = self.get_outfile_path(self.pipeline_parameters['outid'])
        with open(csv_file, "w") as handle:
            log.info(f"writing output to '{csv_file}'...")
            handle.write(csv_str)
            handle.close()
