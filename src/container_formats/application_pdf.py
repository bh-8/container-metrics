from abstract_intermediate_format import AbstractStructureAnalysis, ContainerSection, ContainerSegment, ContainerFragment

class ApplicationPdfAnalysis(AbstractStructureAnalysis):
    def __init__(self) -> None:
        super().__init__()

    def process_section(self, section: ContainerSection):
        return section
