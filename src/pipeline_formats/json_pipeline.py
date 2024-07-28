"""
json_pipeline.py

references:
    - 

"""

# IMPORTS

import json
import logging
from pathlib import Path
log = logging.getLogger(__name__)

from abstract_pipeline import AbstractPipeline

# MODULE ENTRYPOINT

class JsonPipeline(AbstractPipeline):
    def __init__(self, document: dict, raw: bytes, pipeline_parameters: dict) -> None:
        super().__init__("json", document, raw, pipeline_parameters)

    def process(self) -> None:
        out_dict: dict = self.get_raw_document()

        # convert BSON to JSON
        out_dict["_id"] = str(out_dict["_id"])
        del out_dict["_gridfs"]

        # write output
        json_file: Path = self.get_outfile_path(self.pipeline_parameters['outid'])
        with open(json_file, "w") as handle:
            log.info(f"writing output to '{json_file}'...")
            json.dump(out_dict, handle)
            handle.close()
