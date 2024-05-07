from abstract_intermediate_format import *

class ImageJpegAnalysis(AbstractStructureAnalysis):
    def __init__(self) -> None:
        super().__init__()

    def process_section(self, section: ContainerSection):
        jpeg_segs: ContainerSegment = ContainerSegment()
        offset: int = 0

        section.add_segment("jpeg_segments", jpeg_segs)
        return section
