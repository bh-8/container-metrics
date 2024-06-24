"""
csv_pipeline.py

references:
    - 

"""

# IMPORTS

from abstract_pipeline import AbstractPipeline
import logging
log = logging.getLogger(__name__)

# GLOBAL STATIC MAPPINGS

SEPARATOR = ","
NEWLINE = "\n"

# MODULE ENTRYPOINT

class CsvPipeline(AbstractPipeline):
    def __init__(self, document: dict, raw: bytes, selections: list[str]) -> None:
        super().__init__("csv", document, raw)
        self.selections: list[str] = selections

    def process(self) -> None:
        raw_document: bytes = self.get_raw_document(hex=True)

        for selection in self.selections:
            s: list[str] = selection.split(":")
            mime_type: str = s[0]
            segment: str = s[1]
            attributes: list[str] = s[2].split(",")

            # TODO: nested attributes (pdf dictionary)

            # loop sections which correspond to given mimetype
            for section in [section for section in raw_document["sections"] if section["mime_type"] == mime_type]:
                if segment in section["segments"]:
                    csv_str: str = NEWLINE.join([s[2]] + [SEPARATOR.join([(str(fragment[attribute]) if attribute in fragment.keys() else "n/a") for attribute in attributes]) for fragment in section["segments"][segment]])
                    # write output
                    with open(self.output_path / f"{self.output_id}_{section['position']}-{segment}.csv", "w") as handle:
                        handle.write(csv_str)
                        log.info(f"output stored in './io/{self.output_path.name}/{self.output_id}_{section['position']}-{segment}.csv'")
                        handle.close()
                else:
                    self.logger.critical(f"could not access segment '{segment}' in mimetype section '{mime_type}'")
                    continue

    """
    def general_select(self, sel_path: list[str], i: int, sel_current: dict) -> dict:
        if not i < len(sel_path):
            return sel_current # path resolved completely
        elif type(sel_current) is list:
            if sel_path[i].isdigit() and int(sel_path[i]) < len(sel_current): # selection by index
                return self.general_select(sel_path, i+1, sel_current[int(sel_path[i])])
            if sel_path[i] == "*":
                return [self.general_select(sel_path, i+1, item) for item in sel_current]
            if sel_path[i] == "?": # return first match
                return [i for i in [self.general_select(sel_path, i+1, item) for item in sel_current] if i is not None][0]
        if sel_path[i] in sel_current: # selection by key name
            return self.general_select(sel_path, i+1, sel_current[sel_path[i]])
        else:
            return None
    """
