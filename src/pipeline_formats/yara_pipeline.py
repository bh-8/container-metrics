"""
yara_pipeline.py

references:
    - 

"""

# IMPORTS

import json
import logging
from pathlib import Path
import yara
log = logging.getLogger(__name__)

from abstract_pipeline import AbstractPipeline

# MODULE ENTRYPOINT

class YaraPipeline(AbstractPipeline):
    def __init__(self, document: dict, raw: bytes, pipeline_parameters: dict) -> None:
        super().__init__("yara", document, raw, pipeline_parameters)

    def process(self) -> None:
        yara_externals = {
            "mdb_url": self.pipeline_parameters["mongodb"],
            "mdb_pjt": self.pipeline_parameters["project"],
            "mdb_set": self.pipeline_parameters["set"],
            "mdb_oid": str(self.document["_id"])
        }
        rule_files = [Path(self.pipeline_parameters["rule_file"])]
        yara_rules = [yara.compile(str(rule_file), externals=yara_externals) for rule_file in rule_files]
        yara_matches = [yara_rule.match(data=self.raw, timeout=60) for yara_rule in yara_rules]

        match_dict = [{
            rule_files[i].name: [
                match.rule for match in yara_matches[i] if "main" in match.tags
            ]
        } for i in range(0, len(yara_matches))]

        for entry in match_dict:
            for key in entry:
                if len(entry[key]) > 0:
                    json_file: Path = self.get_outfile_path(self.pipeline_parameters['outid'])
                    with open(json_file, "w") as handle:
                        log.info(f"writing output to '{json_file}'...")
                        json.dump(match_dict, handle)
                        handle.close()
                        return
