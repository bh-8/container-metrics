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
    def __init__(self, document: dict, raw: bytes, jmes_query_strings: list[str]) -> None:
        super().__init__("csv", document, raw)
        self.jmes_query_strings: list[str] = jmes_query_strings

    """
    def __json_select(self, sel_path: list[str], i: int, sel_current: dict) -> dict:
        # path resolved completely
        if not i < len(sel_path):
            return sel_current

        if type(sel_current) is list:
            # return match by index
            if sel_path[i].isdigit() and int(sel_path[i]) < len(sel_current): # selection by index
                return self.__json_select(sel_path, i+1, sel_current[int(sel_path[i])])

            # return all matches as wrapped in list
            if sel_path[i] == "*":
                return [self.__json_select(sel_path, i+1, item) for item in sel_current]

            # return first match which is not None
            if sel_path[i] == "?":
                return [i for i in [self.__json_select(sel_path, i+1, item) for item in sel_current] if i is not None][0]

        if type(sel_current) is dict and sel_path[i] in sel_current:
            # selection by key name
            return self.__json_select(sel_path, i+1, sel_current[sel_path[i]])

        return None
    def __csv_format(self, char: str, input: any) -> str:
        if type(input) is list:
            return char.join([(f"<{type(s).__name__}>" if char == SEPARATOR2 else self.__csv_format(SEPARATOR2, s)) if (type(s) is dict or type(s) is list) else f"{s}" for s in input])
        if type(input) is dict:
            return char.join([f"{{{k}=" + ((f"<{type(input[k]).__name__}>}}" if char == SEPARATOR2 else self.__csv_format(SEPARATOR2, input[k])) if (type(input[k]) is dict or type(input[k]) is list) else f"{input[k]}}}") for k in input.keys()])
        return str(input)
    """

    def process(self) -> None:
        for selection in self.jmes_query_strings:
            query_result: list = self.jmesq(selection)
            if type(query_result) is list and len(query_result) == 0:
                return

            csv_str: str = self.stringify(CSV_SEPARATORS, 0, query_result)
            csv_file: Path = self.output_path / f"{self.output_id}.csv"

            # write output
            with open(csv_file, "w") as handle:
                log.info(f"writing output to '{csv_file}'...")
                handle.write(csv_str)
                handle.close()

            """
            s: list[str] = selection.split(":")
            mime_type: str = s[0]
            segment: str = s[1]
            queries: list[str] = s[2].split(",")

            # loop sections which correspond to given mimetype
            for section in [section for section in raw_document["sections"] if section["mime_type"] == mime_type]:
                if segment in section["segments"]:
                    csv_str: str = NEWLINE.join([s[2]] + [SEPARATOR0.join([self.__csv_format(SEPARATOR1, self.__json_select(query.split("."), 0, fragment)) for query in queries]) for fragment in section["segments"][segment]])
                    # write output
                    with open(self.output_path / f"{self.output_id}_{section['position']}-{segment}.csv", "w") as handle:
                        log.info(f"writing output to './io/{self.output_path.name}/{self.output_id}_{section['position']}-{segment}.csv'...")
                        handle.write(csv_str)
                        handle.close()
                else:
                    self.logger.critical(f"could not access segment '{segment}' in mimetype section '{mime_type}'")
                    continue
            """
