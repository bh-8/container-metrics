"""
application_zlib.py

references:
    - 

"""

# IMPORTS

import logging
log = logging.getLogger(__name__)

from abstract_structure_mapping import *
from io import StringIO
import sys
import zlib

# MODULE ENTRYPOINT

class ApplicationZlibAnalysis(AbstractStructureAnalysis):
    def __init__(self) -> None:
        super().__init__()
    def __c2bip3(self, string):
        if sys.version_info[0] > 2:
            if type(string) == bytes:
                return string
            else:
                return bytes([ord(x) for x in string])
        else:
            return string
    def __flateDecode(self, data):
        try:
            return zlib.decompress(self.__c2bip3(data))
        except:
            if len(data) <= 10:
                raise zlib.error("data too short")
            oDecompress = zlib.decompressobj()
            oStringIO = StringIO()
            count = 0
            for byte in self.__c2bip3(data):
                try:
                    oStringIO.write(oDecompress.decompress(byte))
                    count += 1
                except:
                    break
            if len(data) - count <= 2:
                return oStringIO.getvalue()
            else:
                raise zlib.error("unknown format")

    def process(self, section: ContainerSection) -> ContainerSection:
        data: bytes = section.data
        offset: int = 0

        zlib_content: ContainerSegment = ContainerSegment("zlib")
        zlib_fragment: ContainerFragment = ContainerFragment(offset, len(data))
        try:
            decompressed_data: bytes = self.__flateDecode(data)
            zlib_fragment.set_attribute("volatile_data_length", len(decompressed_data))

            section.new_volatile_analysis(decompressed_data)

            zlib_content.add_fragment(zlib_fragment)
            section.add_segment(zlib_content)
            section.calculate_length()
            return section
        except zlib.error as e:
            log.warning(f"zlib decompression failed: {e}")
            return None
