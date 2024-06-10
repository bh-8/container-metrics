import abc
from pathlib import Path
from static_utils import StaticLogger

class AbstractPipeline(abc.ABC):
    def __init__(self, pipeline: str, document: dict) -> None:
        self.pipeline: str = pipeline
        self.document: dict = document
        self.logger = StaticLogger.get_logger()
        self.output_path: Path = Path(f"./io/_{pipeline}").resolve()
        self.output_path.mkdir(exist_ok=True)
        self.output_id: str = f"{self.document['_id']}_{Path(self.document['meta']['file']['name'])}"

    def process(self) -> None:
        raise NotImplementedError("processing not implemented")
