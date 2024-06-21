from abstract_pipeline import AbstractPipeline
import json
from pathlib import Path
import yara

class YaraPipeline(AbstractPipeline):
    def __init__(self, document: dict, raw: bytes, yara_files: list[str]) -> None:
        super().__init__("yara", document, raw)
        self.rule_files: list[Path] = [Path(p).resolve() for p in yara_files if Path(p).exists()]

    def process(self) -> None:
        yara_externals = {
            "filename": self.document["meta"]["file"]["name"],
            "fileid": str(self.document["_id"])
        }
        yara_rules = [yara.compile(str(rule_file), externals=yara_externals) for rule_file in self.rule_files]
        yara_matches = [yara_rule.match(data=self.raw, timeout=60) for yara_rule in yara_rules]

        match_dict = [{
            self.rule_files[i].name: [
                match.rule for match in yara_matches[i] if "main" in match.tags
            ]
        } for i in range(0, len(yara_matches))]
        for entry in match_dict:
            for key in entry:
                if len(entry[key]) > 0:
                    with open(self.output_path / f"{self.output_id}.json", "w") as handle:
                        json.dump(match_dict, handle)
                        handle.close()
                        return
