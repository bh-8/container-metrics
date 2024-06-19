from abstract_structure_mapping import *
import math

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
MODE_EXT = {
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

ID3V1_GENRE = {
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

class MpegFrame():
    def __init__(self, data: bytes, offset: int) -> None:
        self._data: bytes = data
        self._header: bytes = data[offset:offset + 4]
        self._offset: int = offset
        self._length: int = 4
        self._version:    float =      VERSION.get((self._header[1] & 0b00011000) >> 3, None)
        self._layer:        int =        LAYER.get((self._header[1] & 0b00000110) >> 1, None)
        self._crc:         bool =          CRC.get((self._header[1] & 0b00000001) >> 0, None)
        self._dbitrate:    dict =      BITRATE.get((self._header[2] & 0b11110000) >> 4, None)
        self._dfrequency:  dict =     SAMPLING.get((self._header[2] & 0b00001100) >> 2, None)
        self._padding:     bool =      PADDING.get((self._header[2] & 0b00000010) >> 1, None)
        self._private:     bool =      PRIVATE.get((self._header[2] & 0b00000001) >> 0, None)
        self._channel_mode: str = CHANNEL_MODE.get((self._header[3] & 0b11000000) >> 6, None)
        self._dmode_ext:   dict =     MODE_EXT.get((self._header[3] & 0b00110000) >> 4, None)
        self._copyright:   bool =    COPYRIGHT.get((self._header[3] & 0b00001000) >> 3, None)
        self._original:    bool =     ORIGINAL.get((self._header[3] & 0b00000100) >> 2, None)
        self._emphasis:     str =     EMPHASIS.get((self._header[3] & 0b00000011) >> 0, None)
        self._bitrate:      int = None
        self._frequency:    int = None
        self._mode_ext:     str = None
        if self._version is None or self._layer is None or self._dbitrate is None:
            return
        self._bitrate: int = 1000 * self._dbitrate.get((int(self._version), self._layer))
        self._frequency: int = self._dfrequency.get(self._version)
        self._mode_ext: str = self._dmode_ext.get(self._layer)
        self._channels: int = 1 if self._channel_mode == "Mono" else 2
        self._samples: int = FRAME_SAMPLES.get(self._layer).get(self._version)
    def is_invalid(self) -> bool:
        return (self._version is None) or (self._layer is None) or (self._bitrate is None) or (self._frequency is None) or (self._samples is None)
    def default_length(self) -> None:
        fl: float = (self._samples * self._bitrate) / (8 * self._frequency)
        if self._padding:
            self._length = math.ceil(fl)
        else:
            self._length = math.floor(fl)
    def get_length(self) -> int:
        return self._length
    def as_fragment(self) -> ContainerFragment:
        fragment: ContainerFragment = ContainerFragment(self._offset, self._length)

        fragment.set_attribute("version", self._version)
        fragment.set_attribute("layer", self._layer)
        fragment.set_attribute("crc", self._crc)
        fragment.set_attribute("bitrate", self._bitrate)
        fragment.set_attribute("frequency", self._frequency)
        fragment.set_attribute("padding", self._padding)
        fragment.set_attribute("private_bit", self._private)
        fragment.set_attribute("channel_mode", self._channel_mode)
        fragment.set_attribute("mode_extension", self._mode_ext)
        fragment.set_attribute("copyright", self._copyright)
        fragment.set_attribute("original", self._original)
        fragment.set_attribute("emphasis", self._emphasis)
        fragment.set_attribute("samples", self._samples)

        return fragment

#class Id3v2Tag():
#    pass # TODO
#class Id3v1Tag():
#    pass # TODO

class AudioMpegAnalysis(AbstractStructureAnalysis):
    def __init__(self) -> None:
        super().__init__()

    def process_section(self, section: ContainerSection) -> ContainerSection:
        #id3v2_tags: ContainerSegment = ContainerSegment()
        mpeg_frames: ContainerSegment = ContainerSegment()
        #id3v1_tags: ContainerSegment = ContainerSegment()
        offset: int = 0

        data: bytes = section.get_data()
        while True:
            ff: int = data.find(b"\xff", offset)
            if (ff < 0) or (not ff + 4 < len(data)) or (data[ff + 1] < 224):
                break

            mpeg_frame: MpegFrame = MpegFrame(data, offset)
            if mpeg_frame.is_invalid():
                break
            mpeg_frame.default_length()

            mpeg_frames.add_fragment(mpeg_frame.as_fragment())

            offset = ff + mpeg_frame.get_length()
        section.add_segment("mpeg_frames", mpeg_frames)

        if offset < len(data):
            section.new_analysis(offset)
            section.set_length(offset)
            return section

        section.calculate_length()
        return section
