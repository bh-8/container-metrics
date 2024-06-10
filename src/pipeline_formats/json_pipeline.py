from abstract_pipeline import AbstractPipeline
import json
from pathlib import Path

class JsonPipeline(AbstractPipeline):
    def __init__(self, document: dict, gridfsdata: bytes) -> None:
        super().__init__("json", document)
        self.raw: bytes = gridfsdata

    def process(self) -> None:
        out_dict: dict = self.document

        # convert BSON to JSON
        out_dict["_id"] = str(out_dict["_id"])
        #out_dict["_gridfs"] = str(out_dict["_gridfs"])
        del out_dict["_gridfs"]

        # insert fragment data
        for i in range(len(out_dict["sections"])):
            s: dict = out_dict["sections"][i]["segments"]
            for k in s.keys():
                for j in range(len(s[k])):
                    f: dict = out_dict["sections"][i]["segments"][k][j]
                    position: int = out_dict["sections"][i]["position"] + f["offset"]
                    end: int = position + f["length"]
                    data: bytes = self.raw[position:end]
                    out_dict["sections"][i]["segments"][k][j]["raw"] = f"{data}"

        # write output
        with open(self.output_path / f"{self.output_id}.json", "w") as handle:
            json.dump(out_dict, handle)
            handle.close()
