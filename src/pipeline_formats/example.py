from abstract_pipeline import AbstractPipeline

class ExamplePipeline(AbstractPipeline):
    def __init__(self, document: dict) -> None:
        super().__init__(document)

    def process(self) -> None:
        print(self.document["meta"]["file"]["name"])
