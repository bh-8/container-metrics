from abstract_pipeline import AbstractPipeline

SEPARATOR = ","
NEWLINE = "\n"

class CsvPipeline(AbstractPipeline):
    def __init__(self, document: dict, gridfsdata: bytes, selections: list[str]) -> None:
        super().__init__("csv", document)
        self.raw: bytes = gridfsdata
        self.selections: list[str] = selections

    def general_select(self, sel_path: list[str], i: int, sel_current: dict) -> dict:
        if not i < len(sel_path):
            return sel_current # path resolved completely
        elif type(sel_current) is list:
            if sel_path[i].isdigit() and int(sel_path[i]) < len(sel_current): # selection by index
                return self.general_select(sel_path, i+1, sel_current[int(sel_path[i])])
            if sel_path[i] == "*":
                return [self.general_select(sel_path, i+1, item) for item in sel_current]
                #return [x for x in [self.general_select(sel_path, i+1, item) for item in sel_current] if x is not None]
        if sel_path[i] in sel_current: # selection by key name
            return self.general_select(sel_path, i+1, sel_current[sel_path[i]])
        else:
            return None
        #self.logger.warn(f"selection could only be resolved until '{sel_path[i]}' ({'.'.join(sel_path[0:i])})")

    def process(self) -> None:
        sel_current: dict = self.document
        csv_columns: list = [self.general_select(s.split("."), 0, sel_current) for s in self.selections]
        # TODO: check column uniformity
        csv_rows = [self.selections] + [list(x) for x in zip(*csv_columns)]

        csv_str: str = f"{NEWLINE.join([SEPARATOR.join([str(v) for v in row]) for row in csv_rows])}{NEWLINE}"

        # write output
        with open(self.output_path / f"{self.output_id}.csv", "w") as handle:
            handle.write(csv_str)
            handle.close()
