"""
image_jpeg.py

references:
    - https://dev.exiv2.org/projects/exiv2/wiki/The_Metadata_in_JPEG_files

"""

# IMPORTS

import logging
log = logging.getLogger(__name__)

from abstract_structure_mapping import *

# GLOBAL STATIC MAPPINGS

SEGMENT_TYPES = {
    192: { #FF C0
        "abbr": "SOF0",
        "name": "Start Of Frame",
        "info": "baseline dct"
    },
    193: { #FF C1
        "abbr": "SOF1",
        "name": "Start Of Frame",
        "info": "extended sequential dct"
    },
    194: { #FF C2
        "abbr": "SOF2",
        "name": "Start Of Frame",
        "info": "progressive dct"
    },
    195: { #FF C3
        "abbr": "SOF3",
        "name": "Start Of Frame",
        "info": "lossless (sequential)"
    },
    196: { #FF C4
        "abbr": "DHT",
        "name": "Define Huffman Table",
        "info": "huffman table definition"
    },
    197: { #FF C5
        "abbr": "SOF5",
        "name": "Start Of Frame",
        "info": "differential sequential dct"
    },
    198: { #FF C6
        "abbr": "SOF6",
        "name": "Start Of Frame",
        "info": "differential progressive dct"
    },
    199: { #FF C7
        "abbr": "SOF7",
        "name": "Start Of Frame",
        "info": "differential lossless (sequential)"
    },
    200: { #FF C8
        "abbr": "JPG",
        "name": "JPEG extension",
        "info": None
    },
    201: { #FF C9
        "abbr": "SOF9",
        "name": "Start Of Frame",
        "info": "extended sequential dct, arithmetic coding"
    },
    202: { #FF CA
        "abbr": "SOF10",
        "name": "Start Of Frame",
        "info": "progressive dct, arithmetic coding"
    },
    203: { #FF CB
        "abbr": "SOF11",
        "name": "Start Of Frame",
        "info": "lossless (sequential), arithmetic coding"
    },
    204: { #FF CC
        "abbr": "DAC",
        "name": "Define Arithmetic Coding",
        "info": "arithmetic coding definition"
    },
    205: { #FF CD
        "abbr": "SOF13",
        "name": "Start Of Frame",
        "info": "differential sequential dct"
    },
    206: { #FF CE
        "abbr": "SOF14",
        "name": "Start Of Frame",
        "info": "differential progressive dct"
    },
    207: { #FF CF
        "abbr": "SOF15",
        "name": "Start Of Frame",
        "info": "differential lossless (sequential)"
    },
    208: { #FF D0
        "abbr": "RST0",
        "name": "Restart Marker 0",
        "info": None
    },
    209: { #FF D1
        "abbr": "RST1",
        "name": "Restart Marker 1",
        "info": None
    },
    210: { #FF D2
        "abbr": "RST2",
        "name": "Restart Marker 2",
        "info": None
    },
    211: { #FF D3
        "abbr": "RST3",
        "name": "Restart Marker 3",
        "info": None
    },
    212: { #FF D4
        "abbr": "RST4",
        "name": "Restart Marker 4",
        "info": None
    },
    213: { #FF D5
        "abbr": "RST5",
        "name": "Restart Marker 5",
        "info": None
    },
    214: { #FF D6
        "abbr": "RST6",
        "name": "Restart Marker 6",
        "info": None
    },
    215: { #FF D7
        "abbr": "RST7",
        "name": "Restart Marker 7",
        "info": None
    },
    216: { #FF D8
        "abbr": "SOI",
        "name": "Start Of Image",
        "info": "magic number"
    },
    217: { #FF D9
        "abbr": "EOI",
        "name": "End Of Image",
        "info": "end of jpeg image data"
    },
    218: { #FF DA
        "abbr": "SOS",
        "name": "Start Of Scan",
        "info": "image data segment"
    },
    219: { #FF DB
        "abbr": "DQT",
        "name": "Define Quantization Tables",
        "info": "quantization table definition"
    },
    220: { #FF DC
        "abbr": "DNL",
        "name": "Define Number of Lines",
        "info": None
    },
    221: { #FF DD
        "abbr": "DRI",
        "name": "Define Restart Interval",
        "info": None
    },
    222: { #FF DE
        "abbr": "DHP",
        "name": "Define Hierarchical Progression",
        "info": None
    },
    223: { #FF DF
        "abbr": "EXP",
        "name": "Expand Reference Component",
        "info": None
    },
    224: { #FF E0
        "abbr": "APP0",
        "name": "Application Segment 0",
        "info": "jfif tag"
    },
    225: { #FF E1
        "abbr": "APP1",
        "name": "Application Segment 1",
        "info": "commonly used for exif-data, thumbnails or adobe xmp profiles"
    },
    226: { #FF E2
        "abbr": "APP2",
        "name": "Application Segment 2",
        "info": "commonly used for icc color profiles"
    },
    227: { #FF E3
        "abbr": "APP3",
        "name": "Application Segment 3",
        "info": "commonly used as jps-tag for stereoscopic jpeg images"
    },
    228: { #FF E4
        "abbr": "APP4",
        "name": "Application Segment 4",
        "info": None
    },
    229: { #FF E5
        "abbr": "APP5",
        "name": "Application Segment 5",
        "info": None
    },
    230: { #FF E6
        "abbr": "APP6",
        "name": "Application Segment 6",
        "info": "commonly used for nitf lossles profiles"
    },
    231: { #FF E7
        "abbr": "APP7",
        "name": "Application Segment 7",
        "info": None
    },
    232: { #FF E8
        "abbr": "APP8",
        "name": "Application Segment 8",
        "info": None
    },
    233: { #FF E9
        "abbr": "APP9",
        "name": "Application Segment 9",
        "info": None
    },
    234: { #FF EA
        "abbr": "APP10",
        "name": "Application Segment 10",
        "info": "commonly used to store activeobjects"
    },
    235: { #FF EB
        "abbr": "APP11",
        "name": "Application Segment 11",
        "info": "commonly used to store helios jpeg resources (opi postscript)"
    },
    236: { #FF EC
        "abbr": "APP12",
        "name": "Application Segment 12",
        "info": "commonly used by photoshop to store ducky tags or picture info"
    },
    237: { #FF ED
        "abbr": "APP13",
        "name": "Application Segment 13",
        "info": "commonly used by photoshop to store irb, 8bim or iptc data"
    },
    238: { #FF EE
        "abbr": "APP14",
        "name": "Application Segment 14",
        "info": "commonly used for copyright information"
    },
    239: { #FF EF
        "abbr": "APP15",
        "name": "Application Segment 15",
        "info": None
    },
    240: { #FF F0
        "abbr": "JPG0",
        "name": "JPEG Extension 0",
        "info": None
    },
    241: { #FF F1
        "abbr": "JPG1",
        "name": "JPEG Extension 1",
        "info": None
    },
    242: { #FF F2
        "abbr": "JPG2",
        "name": "JPEG Extension 2",
        "info": None
    },
    243: { #FF F3
        "abbr": "JPG3",
        "name": "JPEG Extension 3",
        "info": None
    },
    244: { #FF F4
        "abbr": "JPG4",
        "name": "JPEG Extension 4",
        "info": None
    },
    245: { #FF F5
        "abbr": "JPG5",
        "name": "JPEG Extension 5",
        "info": None
    },
    246: { #FF F6
        "abbr": "JPG6",
        "name": "JPEG Extension 6",
        "info": None
    },
    247: { #FF F7
        "abbr": "JPG7",
        "name": "JPEG Extension 7",
        "info": None
    },
    248: { #FF F8
        "abbr": "JPG8",
        "name": "JPEG Extension 8",
        "info": None
    },
    249: { #FF F9
        "abbr": "JPG9",
        "name": "JPEG Extension 9",
        "info": None
    },
    250: { #FF FA
        "abbr": "JPG10",
        "name": "JPEG Extension 10",
        "info": None
    },
    251: { #FF FB
        "abbr": "JPG11",
        "name": "JPEG Extension 11",
        "info": None
    },
    252: { #FF FC
        "abbr": "JPG12",
        "name": "JPEG Extension 12",
        "info": None
    },
    253: { #FF FD
        "abbr": "JPG13",
        "name": "JPEG Extension 13",
        "info": None
    },
    254: { #FF FE
        "abbr": "COM",
        "name": "Comments",
        "info": None
    }
}

# SPECIFIC MEDIA FORMAT PARTS

class JpegSegment():
    def __init__(self, data: bytes, offset: int, id: int) -> None:
        self.__data: bytes = data
        self.__offset: int = offset
        self.__length: int = 2
        self.__id: int = id
        self.__info: dict = SEGMENT_TYPES.get(id, {
            "abbr": "unknown",
            "name": "(unknown segment)",
            "info": "unknown segment"
        })
        self.__payload = None
        if self.__id < 216 or self.__id > 218:
            # TODO: match segments and add detailed attributes to fragment..
            match self.__id:
                case 192 | 193 | 194 | 195: # SOF 0-3
                    pass
                case 196: # DHT
                    pass
                case 197 | 198 | 199: # SOF 5-7
                    pass
                case 200: # JPG
                    pass 
                case 201 | 202 | 203: # SOF 9-11
                    pass
                case 204: # DAC
                    pass
                case 205 | 206 | 207: # SOF 13-15
                    pass
                case 208 | 209 | 210 | 211 | 212 | 213 | 214 | 215: # RST 0-7
                    pass
                # 216-218 already handled!
                case 219: # DQT
                    pass
                case 220: # DNL
                    pass
                case 221: # DRI
                    pass
                case 222: # DHP
                    pass
                case 223: # EXP
                    pass
                case 224 | 225 | 226 | 227 | 228 | 229 | 230 | 231 | 232 | 233 | 234 | 235 | 236 | 237 | 238 | 239: # APP0-15
                    pass
                case 240 | 241 | 242 | 243 | 244 | 245 | 246 | 247 | 248 | 249 | 250 | 251 | 252 | 253: # JPG0-13
                    pass
                case 254: # COM
                    pass
    def calculate_length(self) -> None:
        x: int = self.__offset + 2
        y: int = self.__offset + 3
        if not y < len(self.__data):
            return
        self.__length = 2 + (256 * self.__data[x] + self.__data[y])
    def set_length(self, length: int) -> None:
        self.__length = length
    def set_payload(self, has_length_info: bool = True):
        self.__payload = {
            "o": self.__offset + (4 if has_length_info else 2),
            "l": self.__length - (4 if has_length_info else 2)
        }

    @property
    def length(self) -> int:
        return self.__length
    @property
    def as_fragment(self) -> ContainerFragment:
        fragment: ContainerFragment = ContainerFragment(self.__offset, self.__length)
        fragment.set_attribute("id", self.__id)
        fragment.set_attribute("name", self.__info["abbr"])
        fragment.set_attribute("long_name", self.__info["name"])
        if not self.__payload is None:
            payload_fragment: ContainerFragment = ContainerFragment(self.__payload["o"], self.__payload["l"])
            fragment.set_attribute("payload", payload_fragment.as_dictionary)
        return fragment

# MODULE ENTRYPOINT

class ImageJpegAnalysis(AbstractStructureAnalysis):
    def __init__(self) -> None:
        super().__init__()

    def process(self, section: ContainerSection) -> ContainerSection:
        data: bytes = section.data
        offset: int = 0

        # parse jpeg segments
        jpeg_segs: ContainerSegment = ContainerSegment("jpeg_segments")
        while True:
            ff: int = data.find(b"\xff", offset)
            if (ff < 0) or (not ff + 1 < len(data)) or (data[ff + 1] < 192 or data[ff + 1] > 254):
                break

            id: int = data[ff + 1]
            js: JpegSegment = JpegSegment(data, ff, id)

            # segments without payload
            if id == 216: # \xff\xd8 - Magic Number
                jpeg_segs.add_fragment(js.as_fragment)
                offset = ff + 2
                continue
            if id == 217: # \xff\xd9 - End of Image
                jpeg_segs.add_fragment(js.as_fragment)
                offset = ff + 2
                if offset < len(data):
                    section.new_analysis(offset)
                    section.set_length(offset)
                break
            
            # segments with special payload
            if id == 218: # \xff\xda - Start of Scan
                eoi: int = data.find(b"\xff\xd9", offset)
                if eoi < 0:
                    js.set_length(len(data) - offset)
                else:
                    js.set_length(eoi - offset)
                js.set_payload(False)
                offset = ff + js.length
                jpeg_segs.add_fragment(js.as_fragment)
                continue

            # default segments
            js.calculate_length()
            js.set_payload(True)
            offset = ff + js.length
            jpeg_segs.add_fragment(js.as_fragment)

        section.add_segment(jpeg_segs)
        section.calculate_length()
        return section
