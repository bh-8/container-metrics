from abstract_structure_mapping import *

class ExampleAnalysis(AbstractStructureAnalysis):
    def __init__(self) -> None:
        super().__init__()

    def process_section(self, section: ContainerSection):
        return section
