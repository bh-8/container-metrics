import abc
from static_utils import StaticLogger

class AbstractPipeline(abc.ABC):
    def __init__(self, document: dict) -> None:
        self.document = document
        self.logger = StaticLogger.get_logger()

    def process(self) -> None:
        raise NotImplementedError("processing not implemented")
