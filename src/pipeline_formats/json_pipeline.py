from abstract_pipeline import AbstractPipeline
import json
from pathlib import Path

class JsonPipeline(AbstractPipeline):
    def __init__(self, document: dict, gridfsdata) -> None:
        super().__init__(document)
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
        output_path: Path = Path("./io/_json").resolve()
        output_path.mkdir(exist_ok=True)
        output_file: str = f"{out_dict['_id']}_{out_dict['meta']['file']['name']}.json"
        with open(output_path / output_file, "w") as handle:
            json.dump(out_dict, handle)
            handle.close()
