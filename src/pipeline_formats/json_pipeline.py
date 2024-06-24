"""
json_pipeline.py

references:
    - 

"""

# IMPORTS

import json
import logging
log = logging.getLogger(__name__)

from abstract_pipeline import AbstractPipeline

# MODULE ENTRYPOINT

class JsonPipeline(AbstractPipeline):
    def __init__(self, document: dict, raw: bytes, dummy: any) -> None:
        super().__init__("json", document, raw)

    def process(self) -> None:
        out_dict: dict = self.get_raw_document()

        # convert BSON to JSON
        out_dict["_id"] = str(out_dict["_id"])
        del out_dict["_gridfs"]

        # write output
        with open(self.output_path / f"{self.output_id}.json", "w") as handle:
            json.dump(out_dict, handle)
            log.info(f"output stored in './io/{self.output_path.name}/{self.output_id}.json'")
            handle.close()
