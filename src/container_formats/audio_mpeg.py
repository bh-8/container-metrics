"""
audio_mpeg.py

references:
    - http://www.mp3-tech.org/programmer/docs/mp3_theory.pdf
    - https://github.com/tomershay100/mp3-steganography-lib
    - https://sourceforge.net/p/mp3filestructureanalyser
    - https://mutagen-specs.readthedocs.io/en/latest/id3/id3v2.4.0-structure.html
    - https://mutagen-specs.readthedocs.io/en/latest/id3/id3v2.4.0-frames.html

"""

# IMPORTS

from bitarray import bitarray
from bitarray.util import ba2int
from enum import Enum
from functools import reduce
import logging
import math
log = logging.getLogger(__name__)

from abstract_structure_mapping import *
from static_utils import try_utf8_conv, convert_unicode_str

# GLOBAL STATIC MAPPINGS

ID3_1_TAG = b"TAG"
ID3_2_TAG = b"ID3"
FRAME_SAMPLES = { # L x V -> Samples
    1: { 1:  384, 2:  384 },
    2: { 1: 1152, 2: 1152 },
    3: { 1: 1152, 2:  576 }
}
VERSION = {
    0: 2.5,
    1: None,
    2: 2,
    3: 1
}
LAYER = {
    0: None,
    1: 3,
    2: 2,
    3: 1
}
CRC = {
    0: True,
    1: False
}
BITRATE = { # B x (V, L) -> Bitrate
     0: { (1, 1): None, (1, 2): None, (1, 3): None, (2, 1): None, (2, 2): None, (2, 3): None },
     1: { (1, 1):   32, (1, 2):   32, (1, 3):   32, (2, 1):   32, (2, 2):    8, (2, 3):    8 },
     2: { (1, 1):   64, (1, 2):   48, (1, 3):   40, (2, 1):   48, (2, 2):   16, (2, 3):   16 },
     3: { (1, 1):   96, (1, 2):   56, (1, 3):   48, (2, 1):   56, (2, 2):   24, (2, 3):   24 },
     4: { (1, 1):  128, (1, 2):   64, (1, 3):   56, (2, 1):   64, (2, 2):   32, (2, 3):   32 },
     5: { (1, 1):  160, (1, 2):   80, (1, 3):   64, (2, 1):   80, (2, 2):   40, (2, 3):   40 },
     6: { (1, 1):  192, (1, 2):   96, (1, 3):   80, (2, 1):   96, (2, 2):   48, (2, 3):   48 },
     7: { (1, 1):  224, (1, 2):  112, (1, 3):   96, (2, 1):  112, (2, 2):   56, (2, 3):   56 },
     8: { (1, 1):  256, (1, 2):  128, (1, 3):  112, (2, 1):  128, (2, 2):   64, (2, 3):   64 },
     9: { (1, 1):  288, (1, 2):  160, (1, 3):  128, (2, 1):  144, (2, 2):   80, (2, 3):   80 },
    10: { (1, 1):  320, (1, 2):  192, (1, 3):  160, (2, 1):  160, (2, 2):   96, (2, 3):   96 },
    11: { (1, 1):  352, (1, 2):  224, (1, 3):  192, (2, 1):  176, (2, 2):  112, (2, 3):  112 },
    12: { (1, 1):  384, (1, 2):  256, (1, 3):  224, (2, 1):  192, (2, 2):  128, (2, 3):  128 },
    13: { (1, 1):  416, (1, 2):  320, (1, 3):  256, (2, 1):  224, (2, 2):  144, (2, 3):  144 },
    14: { (1, 1):  448, (1, 2):  384, (1, 3):  320, (2, 1):  256, (2, 2):  160, (2, 3):  160 },
    15: { (1, 1): None, (1, 2): None, (1, 3): None, (2, 1): None, (2, 2): None, (2, 3): None }
}
SAMPLING = { # F x V -> Frequency
    0: { 1: 44100, 2: 22050, 2.5: 11025 },
    1: { 1: 48000, 2: 24000, 2.5: 12000 },
    2: { 1: 32000, 2: 16000, 2.5: 8000  },
    3: { 1:  None, 2:  None, 2.5: None  }
}
PADDING = {
    0: False,
    1: True
}
PRIVATE = {
    0: False,
    1: True
}
CHANNEL_MODE = {
    0: "Stereo",
    1: "JointStereo",
    2: "DualChannel",
    3: "Mono"
}
MODE_EXT = { # ME x L -> Mode Extension
    0: { 1: "bands 4 to 31",  2: "bands 4 to 31",  3: { "intensity_stereo": False, "ms_stereo": False } },
    1: { 1: "bands 8 to 31",  2: "bands 8 to 31",  3: { "intensity_stereo":  True, "ms_stereo": False } },
    2: { 1: "bands 12 to 31", 2: "bands 12 to 31", 3: { "intensity_stereo": False, "ms_stereo":  True } },
    3: { 1: "bands 16 to 31", 2: "bands 16 to 31", 3: { "intensity_stereo":  True, "ms_stereo":  True } }
}
COPYRIGHT = {
    0: False,
    1: True
}
ORIGINAL = {
    0: False,
    1: True
}
EMPHASIS = {
    0: "None",
    1: "50/15 ms",
    2: "reserved",
    3: "CCIT J.17"
}
ID3V1_GENRES = {
    0: 'Blues', 1: 'Classic Rock', 2: 'Country', 3: 'Dance', 4: 'Disco',
    5: 'Funk', 6: 'Grunge', 7: 'Hip-Hop', 8: 'Jazz', 9: 'Metal',
    10: 'New Age', 11: 'Oldies', 12: 'Other', 13: 'Pop', 14: 'R&B',
    15: 'Rap', 16: 'Reggae', 17: 'Rock', 18: 'Techno', 19: 'Industrial',
    20: 'Alternative', 21: 'Ska', 22: 'Death Metal', 23: 'Pranks', 24: 'Soundtrack',
    25: 'Euro-Techno', 26: 'Ambient', 27: 'Trip-Hop', 28: 'Vocal', 29: 'Jazz+Funk',
    30: 'Fusion', 31: 'Trance', 32: 'Classical', 33: 'Instrumental', 34: 'Acid',
    35: 'House', 36: 'Game', 37: 'Sound Clip', 38: 'Gospel', 39: 'Noise',
    40: 'Alternative Rock', 41: 'Bass', 42: 'Soul', 43: 'Punk', 44: 'Space',
    45: 'Meditative', 46: 'Instrumental Pop', 47: 'Instrumental Rock', 48: 'Ethnic', 49: 'Gothic',
    50: 'Darkwave', 51: 'Techno-Industrial', 52: 'Electronic', 53: 'Pop-Folk', 54: 'Eurodance',
    55: 'Dream', 56: 'Southern Rock', 57: 'Comedy', 58: 'Cult', 59: 'Gangsta Rap',
    60: 'Top 40', 61: 'Christian Rap', 62: 'Pop/Funk', 63: 'Jungle', 64: 'Native American',
    65: 'Cabaret', 66: 'New Wave', 67: 'Psychedelic', 68: 'Rave', 69: 'Showtunes',
    70: 'Trailer', 71: 'Lo-Fi', 72: 'Tribal', 73: 'Acid Punk', 74: 'Acid Jazz',
    75: 'Polka', 76: 'Retro', 77: 'Musical', 78: 'Rock & Roll', 79: 'Hard Rock',
    80: 'Folk', 81: 'Folk/Rock', 82: 'National Folk', 83: 'Swing', 84: 'Fast-Fusion',
    85: 'Bebop', 86: 'Latin', 87: 'Revival', 88: 'Celtic', 89: 'Bluegrass',
    90: 'Avantgarde', 91: 'Gothic Rock', 92: 'Progressive Rock', 93: 'Psychedelic Rock', 94: 'Symphonic Rock',
    95: 'Slow Rock', 96: 'Big Band', 97: 'Chorus', 98: 'Easy Listening', 99: 'Acoustic',
    100: 'Humour', 101: 'Speech', 102: 'Chanson', 103: 'Opera', 104: 'Chamber Music',
    105: 'Sonata', 106: 'Symphony', 107: 'Booty Bass', 108: 'Primus', 109: 'Porn Groove',
    110: 'Satire', 111: 'Slow Jam', 112: 'Club', 113: 'Tango', 114: 'Samba',
    115: 'Folklore', 116: 'Ballad', 117: 'Power Ballad', 118: 'Rhythmic Soul', 119: 'Freestyle',
    120: 'Duet', 121: 'Punk Rock', 122: 'Drum Solo', 123: 'A Cappella', 124: 'Euro-House',
    125: 'Dance Hall', 126: 'Goa', 127: 'Drum & Bass', 128: 'Club-House', 129: 'Hardcore',
    130: 'Terror', 131: 'Indie', 132: 'BritPop', 133: 'Negerpunk', 134: 'Polsk Punk',
    135: 'Beat', 136: 'Christian Gangsta Rap', 137: 'Heavy Metal', 138: 'Black Metal', 139: 'Crossover',
    140: 'Contemporary Christian', 141: 'Christian Rock', 142: 'Merengue', 143: 'Salsa', 144: 'Thrash Metal',
    145: 'Anime', 146: 'JPop', 147: 'Synthpop', 148: 'Christmas', 149: 'Art Rock',
    150: 'Baroque', 151: 'Bhangra', 152: 'Big Beat', 153: 'Breakbeat', 154: 'Chillout',
    155: 'Downtempo', 156: 'Dub', 157: 'EBM', 158: 'Eclectic', 159: 'Electro',
    160: 'Electroclash', 161: 'Emo', 162: 'Experimental', 163: 'Garage', 164: 'Global',
    165: 'IDM', 166: 'Illbient', 167: 'Industro-Goth', 168: 'Jam Band', 169: 'Krautrock',
    170: 'Leftfield', 171: 'Lounge', 172: 'Math rock', 173: 'New Romantic', 174: 'Nu-Breakz',
    175: 'Post-Punk', 176: 'Post-Rock', 177: 'Psytrance', 178: 'Shoegaze', 179: 'Space Rock',
    180: 'Trop Rock', 181: 'World Music', 182: 'Neoclassical', 183: 'Audiobook', 184: 'Audio Theatre',
    185: 'Neue Deutsche Welle', 186: 'Podcast', 187: 'Indie-Rock', 188: 'G-Funk', 189: 'Dubstep',
    190: 'Garage Rock ', 191: 'Psybient', 255: 'None'
}
SLEN = [
    [0, 0], [0, 1], [0, 2], [0, 3], [3, 0], [1, 1], [1, 2], [1, 3],
    [2, 1], [2, 2], [2, 3], [3, 1], [3, 2], [3, 3], [4, 2], [4, 3]
]

# SPECIFIC MEDIA FORMAT PARTS

class FrameHeader():
    def __init__(self, header: bytes) -> None:
        self.__raw = header
        self.__version:       float =      VERSION.get((self.__raw[1] & 0b00011000) >> 3, None)
        self.__layer:           int =        LAYER.get((self.__raw[1] & 0b00000110) >> 1, None)
        self.__crc:            bool =          CRC.get((self.__raw[1] & 0b00000001) >> 0, None)
        self.__dbitrate:       dict =      BITRATE.get((self.__raw[2] & 0b11110000) >> 4, None)
        self.__dfrequency:     dict =     SAMPLING.get((self.__raw[2] & 0b00001100) >> 2, None)
        self.__padding:        bool =      PADDING.get((self.__raw[2] & 0b00000010) >> 1, None)
        self.__private:        bool =      PRIVATE.get((self.__raw[2] & 0b00000001) >> 0, None)
        self.__channel_mode:    str = CHANNEL_MODE.get((self.__raw[3] & 0b11000000) >> 6, None)
        self.__dmode_ext:      dict =     MODE_EXT.get((self.__raw[3] & 0b00110000) >> 4, None)
        self.__copyright:      bool =    COPYRIGHT.get((self.__raw[3] & 0b00001000) >> 3, None)
        self.__original:       bool =     ORIGINAL.get((self.__raw[3] & 0b00000100) >> 2, None)
        self.__emphasis:        str =     EMPHASIS.get((self.__raw[3] & 0b00000011) >> 0, None)
        self.__bitrate:         int =         None
        self.__frequency:       int =         None
        self.__mode_extension:  str =         None
        self.__samples:         int =         None
        self.__validated:      bool =        False

        # check whether frame is invalid
        if self.__version is None or self.__layer is None or self.__dbitrate is None or self.__dfrequency is None or self.__dmode_ext is None:
            return
        elif self.__dbitrate.get((int(self.__version), self.__layer)) is None:
            return
        elif self.__dfrequency.get(self.__version) is None:
            return

        self.__validated:      bool =         True
        self.__channels:        int = 1 if self.__channel_mode == CHANNEL_MODE[3] else 2
        self.__bitrate:         int = 1000 * self.__dbitrate.get((int(self.__version), self.__layer))
        self.__frequency:       int =      self.__dfrequency.get(self.__version)
        self.__mode_extension:  str =       self.__dmode_ext.get(self.__layer)
        self.__samples:         int =          FRAME_SAMPLES.get(self.__layer).get(int(self.__version))

    @property
    def version(self) -> float:
        return self.__version
    @property
    def layer(self) -> int:
        return self.__layer
    @property
    def crc(self) -> bool:
        return self.__crc
    @property
    def bitrate(self) -> int:
        return self.__bitrate
    @property
    def frequency(self) -> int:
        return self.__frequency
    @property
    def padding(self) -> bool:
        return self.__padding
    @property
    def private(self) -> bool:
        return self.__private
    @property
    def channel_mode(self) -> str:
        return self.__channel_mode
    @property
    def mode_extension(self) -> str:
        return self.__mode_extension
    @property
    def copyright(self) -> bool:
        return self.__copyright
    @property
    def original(self) -> bool:
        return self.__original
    @property
    def emphasis(self) -> str:
        return self.__emphasis

    @property
    def samples(self) -> int:
        return self.__samples
    @property
    def channels(self) -> int:
        return self.__channels
    @property
    def is_validated(self) -> bool:
        return self.__validated
    @property
    def as_dictionary(self) -> dict:
        return {
            "version": self.__version,
            "layer": self.__layer,
            "crc": self.__crc,
            "bitrate": self.__bitrate,
            "frequency": self.__frequency,
            "padding": self.__padding,
            "private": self.__private,
            "channel_mode": self.__channel_mode,
            "mode_extension": self.__mode_extension,
            "copyright": self.__copyright,
            "original": self.__original,
            "emphasis": self.__emphasis,
            "samples": self.__samples
        }

class SideInformation():
    def __init__(self, side_info: bytes, header: FrameHeader) -> None:
        self.__is_mono: bool = header.channels == 1
        self.__raw: bytes = side_info[0:17 if self.__is_mono else 32]
        self.__raw_bits: bitarray = bitarray(endian="big")
        self.__raw_bits.frombytes(self.__raw)

        _bit_offset: int = 0

        # read side info fields
        self.__main_data_begin: int = ba2int(self.__raw_bits[_bit_offset:_bit_offset + 9])
        _bit_offset = _bit_offset + 9

        self.__private_bits: int = ba2int(self.__raw_bits[_bit_offset:_bit_offset + (5 if self.__is_mono else 3)])
        _bit_offset = _bit_offset + (5 if self.__is_mono else 3)

        self.__scfsi: list[list[bool]] = [[ba2int(self.__raw_bits[_bit_offset + 4 * c + i:_bit_offset + 4 * c + i + 1]) == 1 for i in range(4)] for c in range(header.channels)]
        _bit_offset = _bit_offset + 4 * header.channels

        # allocating matrices for granule info
        self.__part2_3_length:               list[list[int]] = [[None for x in range(header.channels)] for y in range(2)]
        self.__big_values:                   list[list[int]] = [[None for x in range(header.channels)] for y in range(2)]
        self.__global_gain:                  list[list[int]] = [[None for x in range(header.channels)] for y in range(2)]
        self.__scalefac_compress:            list[list[int]] = [[None for x in range(header.channels)] for y in range(2)]
        self.__slen1:                        list[list[int]] = [[None for x in range(header.channels)] for y in range(2)]
        self.__slen2:                        list[list[int]] = [[None for x in range(header.channels)] for y in range(2)]
        self.__windows_switching_flag:      list[list[bool]] = [[None for x in range(header.channels)] for y in range(2)]
        self.__block_type:                   list[list[int]] = [[None for x in range(header.channels)] for y in range(2)]
        self.__mixed_block_flag:            list[list[bool]] = [[None for x in range(header.channels)] for y in range(2)]
        self.__table_select:           list[list[list[int]]] = [[[None for x in range(3)] for y in range(header.channels)] for z in range(2)]
        self.__subblock_gain:          list[list[list[int]]] = [[[None for x in range(3)] for y in range(header.channels)] for z in range(2)]
        self.__region0_count:                list[list[int]] = [[None for x in range(header.channels)] for y in range(2)]
        self.__region1_count:                list[list[int]] = [[None for x in range(header.channels)] for y in range(2)]
        self.__preflag:                     list[list[bool]] = [[None for x in range(header.channels)] for y in range(2)]
        self.__scalefac_scale:              list[list[bool]] = [[None for x in range(header.channels)] for y in range(2)]
        self.__count1table_select:          list[list[bool]] = [[None for x in range(header.channels)] for y in range(2)]

        # granule info
        for granule in range(2):
            # 1 channel if mono otherwise 2 channels
            for channel in range(header.channels):
                self.__part2_3_length[granule][channel] = ba2int(self.__raw_bits[_bit_offset:_bit_offset + 12])
                _bit_offset = _bit_offset + 12
                self.__big_values[granule][channel] = ba2int(self.__raw_bits[_bit_offset:_bit_offset + 9])
                _bit_offset = _bit_offset + 9
                self.__global_gain[granule][channel] = ba2int(self.__raw_bits[_bit_offset:_bit_offset + 8])
                _bit_offset = _bit_offset + 8
                self.__scalefac_compress[granule][channel] = ba2int(self.__raw_bits[_bit_offset:_bit_offset + 4])
                self.__slen1[granule][channel] = SLEN[self.__scalefac_compress[granule][channel]][0]
                self.__slen2[granule][channel] = SLEN[self.__scalefac_compress[granule][channel]][1]
                _bit_offset = _bit_offset + 4
                self.__windows_switching_flag[granule][channel] = ba2int(self.__raw_bits[_bit_offset:_bit_offset + 1]) == 1
                _bit_offset = _bit_offset + 1

                if self.__windows_switching_flag[granule][channel]:
                    self.__block_type[granule][channel] = ba2int(self.__raw_bits[_bit_offset:_bit_offset + 2])
                    _bit_offset = _bit_offset + 2
                    self.__mixed_block_flag[granule][channel] = ba2int(self.__raw_bits[_bit_offset:_bit_offset + 1]) == 1
                    _bit_offset = _bit_offset + 1

                    for region in range(2):
                        self.__table_select[granule][channel][region] = ba2int(self.__raw_bits[_bit_offset:_bit_offset + 5])
                        _bit_offset = _bit_offset + 5
                    for window in range(3):
                        self.__subblock_gain[granule][channel][window] = ba2int(self.__raw_bits[_bit_offset:_bit_offset + 3])
                        _bit_offset = _bit_offset + 3
                    self.__region0_count[granule][channel] = 8 if self.__block_type[granule][channel] == 2 else 7
                    self.__region1_count[granule][channel] = 20 - self.__region0_count[granule][channel]
                else:
                    self.__block_type[granule][channel] = 0
                    self.__mixed_block_flag[granule][channel] = False

                    for region in range(3):
                        self.__table_select[granule][channel][region] = ba2int(self.__raw_bits[_bit_offset:_bit_offset + 5])
                        _bit_offset = _bit_offset + 5
                    self.__subblock_gain[granule][channel] = None

                    self.__region0_count[granule][channel] = ba2int(self.__raw_bits[_bit_offset:_bit_offset + 4])
                    _bit_offset = _bit_offset + 4
                    self.__region1_count[granule][channel] = ba2int(self.__raw_bits[_bit_offset:_bit_offset + 3])
                    _bit_offset = _bit_offset + 3

                self.__preflag[granule][channel] = ba2int(self.__raw_bits[_bit_offset:_bit_offset + 1]) == 1
                _bit_offset = _bit_offset + 1
                self.__scalefac_scale[granule][channel] = ba2int(self.__raw_bits[_bit_offset:_bit_offset + 1]) == 1
                _bit_offset = _bit_offset + 1
                self.__count1table_select[granule][channel] = ba2int(self.__raw_bits[_bit_offset:_bit_offset + 1]) == 1
                _bit_offset = _bit_offset + 1

    @property
    def main_data_begin(self) -> int:
        return self.__main_data_begin
    @property
    def private_bits(self) -> int:
        return self.__private_bits
    @property
    def scfsi(self) -> list[list[bool]]:
        return self.__scfsi
    @property
    def part2_3_length(self) -> list[list[int]]:
        return self.__part2_3_length
    @property
    def big_values(self) -> list[list[int]]:
        return self.__big_values
    @property
    def global_gain(self) -> list[list[int]]:
        return self.__global_gain
    @property
    def scalefac_compress(self) -> list[list[int]]:
        return self.__scalefac_compress
    @property
    def slen1(self) -> list[list[int]]:
        return self.__slen1
    @property
    def slen2(self) -> list[list[int]]:
        return self.__slen2
    @property
    def windows_switching_flag(self) -> list[list[bool]]:
        return self.__windows_switching_flag
    @property
    def block_type(self) -> list[list[int]]:
        return self.__block_type
    @property
    def mixed_block_flag(self) -> list[list[bool]]:
        return self.__mixed_block_flag
    @property
    def table_select(self) -> list[list[list[int]]]:
        return self.__table_select
    @property
    def subblock_gain(self) -> list[list[list[int]]]:
        return self.__subblock_gain
    @property
    def region0_count(self) -> list[list[int]]:
        return self.__region0_count
    @property
    def region1_count(self) -> list[list[int]]:
        return self.__region1_count
    @property
    def preflag(self) -> list[list[bool]]:
        return self.__preflag
    @property
    def scalefac_scale(self) -> list[list[bool]]:
        return self.__scalefac_scale
    @property
    def count1table_select(self) -> list[list[bool]]:
        return self.__count1table_select
    @property
    def as_dictionary(self) -> dict:
        return {
            "main_data_begin": self.__main_data_begin,
            "private_bits": self.__private_bits,
            "scfsi": self.__scfsi,
            "granule_info": [
                {
                    "part2_3_length": self.__part2_3_length[granule],
                    "big_values": self.__big_values[granule],
                    "global_gain": self.__global_gain[granule],
                    "scalefac_compress": self.__scalefac_compress[granule],
                    "slen1": self.__slen1[granule],
                    "slen2": self.__slen2[granule],
                    "windows_switching_flag": self.__windows_switching_flag[granule],
                    "block_type": self.__block_type[granule],
                    "mixed_block_flag": self.__mixed_block_flag[granule],
                    "table_select": self.__table_select[granule],
                    "subblock_gain": self.__subblock_gain[granule],
                    "region0_count": self.__region0_count[granule],
                    "region1_count": self.__region1_count[granule],
                    "preflag": self.__preflag[granule],
                    "scalefac_scale": self.__scalefac_scale[granule],
                    "count1table_select": self.__count1table_select[granule]
                } for granule in range(2)
            ]
        }

class Id3v1():
    def __init__(self, id3v1: bytes, offset: int):
        self.__offset: int = offset
        self.__title = id3v1[3:33].rstrip(b"\x00\x20").decode(errors = "ignore")
        self.__artist = id3v1[33:63].rstrip(b"\x00\x20").decode(errors = "ignore")
        self.__album = id3v1[63:93].rstrip(b"\x00\x20").decode(errors = "ignore")
        self.__year = id3v1[93:97].decode(errors = "ignore")
        self.__comment = id3v1[97:125].rstrip(b"\x00\x20").decode(errors = "ignore")
        self.__track = None if id3v1[125:127] == b"\x00\x00" else ord(id3v1[126:127])
        self.__genre = ID3V1_GENRES.get(id3v1[127], None)
    @property
    def title(self) -> str:
        return self.__title
    @property
    def artist(self) -> str:
        return self.__artist
    @property
    def album(self) -> str:
        return self.__album
    @property
    def year(self) -> str:
        return self.__year
    @property
    def comment(self) -> str:
        return self.__comment
    @property
    def track(self) -> int:
        return self.__track
    @property
    def genre(self) -> str:
        return self.__genre
    @property
    def as_fragment(self) -> ContainerFragment:
        fragment: ContainerFragment = ContainerFragment(self.__offset, 128)
        fragment.set_attribute("title", self.__title)
        fragment.set_attribute("artist", self.__artist)
        fragment.set_attribute("album", self.__album)
        fragment.set_attribute("year", self.__year)
        fragment.set_attribute("comment", self.__comment)
        fragment.set_attribute("track", self.__track)
        fragment.set_attribute("genre", self.__genre)
        return fragment

class Id3v2Frame():
    def __init__(self, data: bytes, offset: int, section: ContainerSection) -> None:
        self.__data: bytes = data
        self.__offset: int = offset
        i = offset
        self.__frame_id: str = try_utf8_conv(self.__data[i:i+4])
        i = i + 4
        self.__frame_size: int = int.from_bytes(self.__data[i:i+4], byteorder="big")
        i = i + 4
        self.__tag_alter_preservation_flag:   bool = ((self.__data[i+0] & 0b01000000) >> 6) == 1
        self.__file_alter__preservation_flag: bool = ((self.__data[i+0] & 0b00100000) >> 5) == 1
        self.__read_only_flag:                bool = ((self.__data[i+0] & 0b00010000) >> 4) == 1
        self.__grouping_identity_flag:        bool = ((self.__data[i+1] & 0b01000000) >> 6) == 1
        self.__compression_flag:              bool = ((self.__data[i+1] & 0b00001000) >> 3) == 1
        self.__encryption_flag:               bool = ((self.__data[i+1] & 0b00000100) >> 2) == 1
        self.__unsynchronisation_flag:        bool = ((self.__data[i+1] & 0b00000010) >> 1) == 1
        self.__data_length_indicator_flag:    bool = ((self.__data[i+1] & 0b00000001) == 1)
        self.__validated:                     bool = ((self.__data[i+0] & 0b10001111) == 0) and ((self.__data[i+1] & 0b10110000) == 0) and type(self.__frame_id) is str
        self.__length: int = 10 + self.__frame_size
        i = i + 2
        self.__data_formatted = None
        if self.__validated:
            self.__recursive = section.new_analysis
            self.__data_formatted: any = self.__format_data(self.__data[i:i+self.__frame_size])

    def __format_data(self, data: bytes) -> any:
            try:
                match self.__frame_id:
                    case "APIC":
                        mime_type_end: int = data.find(b"\x00", 1)
                        description_end: int = data.find(b"\x00", mime_type_end+2)

                        self.__recursive(self.__offset + description_end + 11, self.__length - description_end - 11)
                        return {
                            "encoding": data[0],
                            "mime_type": data[1:mime_type_end].decode("utf-8", errors="ignore"),
                            "picture_type": data[mime_type_end+1],
                            "description": data[mime_type_end+2:description_end].decode("utf-8", errors="ignore")
                        }
                    #fields to decode (text fields)
                    case "TPE1" | "TPE2" | "TCOP" | "TPOS" | "TPUB" | "TCON" | "TCOM" | "TIT2" | "TALB" | "COMM" | "TRCK" | "TYER":
                        return data.strip(b"\x00").decode(errors = "ignore") if data.find(b"\xff\xfe") == -1 else convert_unicode_str(data)
                    #fields to decode to int (number fields)
                    case "TLEN":
                        return int(data.strip(b"\x00").decode(errors = "ignore") if data.find(b"\xff\xfe") == -1 else convert_unicode_str(data))
                    case _:
                        return None
            except TypeError:
                return None

    @property
    def is_valid(self) -> bool:
        return self.__validated
    @property
    def length(self) -> int:
        return self.__length
    @property
    def as_fragment(self) -> ContainerFragment:
        fragment: ContainerFragment = ContainerFragment(self.__offset, self.__length)

        fragment.set_attribute("frame_id", self.__frame_id)
        fragment.set_attribute("tag_alter_preservation_flag", self.__tag_alter_preservation_flag)
        fragment.set_attribute("file_alter__preservation_flag", self.__file_alter__preservation_flag)
        fragment.set_attribute("read_only_flag", self.__read_only_flag)
        fragment.set_attribute("grouping_identity_flag", self.__grouping_identity_flag)
        fragment.set_attribute("compression_flag", self.__compression_flag)
        fragment.set_attribute("encryption_flag", self.__encryption_flag)
        fragment.set_attribute("unsynchronisation_flag", self.__unsynchronisation_flag)
        fragment.set_attribute("data_length_indicator_flag", self.__data_length_indicator_flag)
        fragment.set_attribute("frame_size", self.__frame_size)
        if not self.__data_formatted is None:
            fragment.set_attribute("content", self.__data_formatted)
        return fragment

class Id3v2Header():
    def __init__(self, id3v2header: bytes, offset: int) -> None:
        self.__data: bytes = id3v2header
        self.__offset: int = offset
        self.__version: str = f"2.{self.__data[3]}.{self.__data[4]}"
        self.__flag_unsynchronisation:      bool = ((self.__data[5] & 0b10000000) >> 7) == 1
        self.__flag_extended_header:        bool = ((self.__data[5] & 0b01000000) >> 6) == 1
        self.__flag_experimental_indicator: bool = ((self.__data[5] & 0b00100000) >> 5) == 1
        self.__flag_footer_present:         bool = ((self.__data[5] & 0b00010000) >> 4) == 1
        self.__validated:                   bool = ((self.__data[5] & 0b00001111)) == 0
        self.__length: int = 10
        if self.__validated:
            self.__tag_size: int = 10 + self.__char2int(self.__data[6:10])

            # TODO: handle extended header and footer later with sample files!
            self.__extended_header_size: int = self.__char2int(self.__data[10:14]) if self.__flag_extended_header else 0
            self.__footer_size: int = 10 if self.__flag_footer_present else 0

    @staticmethod
    def __char2int(four_bytes: bytes) -> int:
        # required to convert sync save integers
        num = 0x00
        for i in range(4):
            num = (num << 7) + four_bytes[i]
        return int(num)

    @property
    def is_valid(self) -> bool:
        return self.__validated
    @property
    def length(self) -> int:
        return self.__length
    @property
    def tag_size(self) -> int:
        return self.__tag_size
    @property
    def as_fragment(self) -> ContainerFragment:
        fragment: ContainerFragment = ContainerFragment(self.__offset, self.__length)

        fragment.set_attribute("version", self.__version)
        fragment.set_attribute("unsynchronisation_flag", self.__flag_unsynchronisation)
        fragment.set_attribute("extended_header_flag", self.__flag_extended_header)
        fragment.set_attribute("experimental_indicator_flag", self.__flag_experimental_indicator)
        fragment.set_attribute("footer_present_flag", self.__flag_footer_present)
        fragment.set_attribute("tag_size", self.__tag_size)

        return fragment

class MpegFrame():
    def __init__(self, data: bytes, offset: int) -> None:
        self.__offset:                int = offset
        self.__length:                int = 4
        self.__header:        FrameHeader = FrameHeader(data[self.__offset:self.__offset + 4])
        if self.__header.is_validated:
            self.__side_info: SideInformation = SideInformation(data[self.__offset + 4:self.__offset + 4 + 32], self.__header)
    def calculate_length(self) -> None:
        fl: float = (self.__header.samples * self.__header.bitrate) / (8 * self.__header.frequency)
        if self.__header.padding:
            self.__length = math.ceil(fl)
        else:
            self.__length = math.floor(fl)

    @property
    def header(self) -> FrameHeader:
        return self.__header
    @property
    def side_info(self) -> SideInformation:
        return self.__side_info
    @property
    def length(self) -> int:
        return self.__length
    @property
    def is_valid(self) -> bool:
        return self.__header.is_validated
    @property
    def as_fragment(self) -> ContainerFragment:
        fragment: ContainerFragment = ContainerFragment(self.__offset, self.__length)

        fragment.set_attribute("header", self.__header.as_dictionary)
        fragment.set_attribute("side_info", self.__side_info.as_dictionary)

        return fragment

# MODULE ENTRYPOINT

class AudioMpegAnalysis(AbstractStructureAnalysis):
    def __init__(self) -> None:
        super().__init__()

    def process(self, section: ContainerSection) -> ContainerSection:
        data: bytes = section.data
        offset: int = 0

        # id3v2
        if (offset + 10 < len(data)) and (data[0:3] == ID3_2_TAG):
            id3v2: ContainerSegment = ContainerSegment("id3v2")

            # id3v2 header
            id3v2header: Id3v2Header = Id3v2Header(data[offset:offset + 10], offset)
            if id3v2header.is_valid:
                id3v2.add_fragment(id3v2header.as_fragment)
                offset = offset + id3v2header.length

                # id3v2
                while (offset < id3v2header.tag_size) and reduce(lambda a, b: a and b, [chr(c).isupper() or chr(c).isdigit() for c in data[offset:offset+4]], True):
                    id3v2frame: Id3v2Frame = Id3v2Frame(data, offset, section)
                    if id3v2frame.is_valid:
                        id3v2.add_fragment(id3v2frame.as_fragment)
                        offset = offset + id3v2frame.length
                        continue
                    break

                # check for padding
                padding: int = id3v2header.tag_size - offset
                if padding > 0 and padding * b"\x00" == data[offset:id3v2header.tag_size]:
                    id3v2.add_fragment(ContainerFragment(offset, padding))
                offset = offset + padding

            section.add_segment(id3v2)

        # mpeg frames
        mpeg_frames: ContainerSegment = ContainerSegment("mpeg_frames")
        while True:
            ff: int = data.find(b"\xff", offset)
            if (ff < 0) or (not ff + 4 + 32 < len(data)) or (data[ff + 1] < 224):
                break

            mpeg_frame: MpegFrame = MpegFrame(data, offset)
            if mpeg_frame.is_valid:
                mpeg_frame.calculate_length()
                mpeg_frames.add_fragment(mpeg_frame.as_fragment)

                offset = ff + mpeg_frame.length
                continue
            break
        section.add_segment(mpeg_frames)

        # id3v1
        if (offset + 128 <= len(data)) and (data[offset:offset + 3] == ID3_1_TAG):
            id3v1: ContainerSegment = ContainerSegment("id3v1")
            id3v1_tag: Id3v1 = Id3v1(data[offset:offset + 128], offset)
            id3v1.add_fragment(id3v1_tag.as_fragment)

            offset = offset + 128
            section.add_segment(id3v1)

        # check whether data left
        if offset < len(data):
            section.new_analysis(offset)
            section.set_length(offset)
            return section

        section.calculate_length()
        return section
