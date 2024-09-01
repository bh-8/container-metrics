"""
application_pdf.py

references:
    - https://www.iso.org/standard/75839.html
    - https://pdfa.org/resource/iso-32000-2/

"""

# IMPORTS

import abc
import logging
import re
log = logging.getLogger(__name__)

from abstract_structure_mapping import *
from static_utils import try_utf8_conv, try_utf16_conv

# GLOBAL STATIC MAPPINGS

WHITESPACE_CHARACTERS: list[bytes] = [
    b"\x00", b"\x09", b"\x0a", b"\x0c", b"\x0d", b"\x20"
]
DELIMITER_CHARACTERS: list[bytes] = [
    b"{", b"(", b"<", b"[", b"/", b"%", b"]", b">", b")", b"}"
]
WHITESPACE_PATTERN: re.Pattern[bytes] = re.compile(b"[" + b"".join([re.escape(wc) for wc in WHITESPACE_CHARACTERS]) + b"]")
WHITESPACE_ANTI_PATTERN: re.Pattern[bytes] = re.compile(b"[^" + b"".join([re.escape(wc) for wc in WHITESPACE_CHARACTERS]) + b"]")

# SPECIFIC MEDIA FORMAT PARTS

class PdfToken():
    def __init__(self, offset: int, raw: bytes, is_stream: bool = False) -> None:
        self.__offset: int = offset
        self.__length: int = len(raw)
        self.__type: str | None = "stream" if is_stream else None
        self.__raw: bytes = raw
        self.__data = try_utf8_conv(self.__raw)

        if self.__type == None:
            if self.__raw.startswith(b"\x25PDF-") and self.__length == 8:
                self.__type = "_header"
            elif self.__raw == b"xref":
                self.__type = "_xref"
            elif self.__raw == b"trailer":
                self.__type = "_trailer"
            elif self.__raw == b"startxref":
                self.__type = "_startxref"
            elif self.__raw == b"\x25\x25EOF":
                self.__type = "_eof"
            elif self.__raw.startswith(b"\x25"):
                self.__type = "_comment"
            elif self.__raw == b"obj":
                self.__type = "indirect_obj"
            elif self.__raw == b"stream":
                self.__type = "stream"
            elif self.__raw == b"true" or self.__raw == b"false":
                self.__type = "boolean"
                self.__data = self.__raw == b"true"
            elif self.__raw == b"null":
                self.__type = "null"
            elif self.__raw.startswith(b"(") and self.__raw.endswith(b")"):
                self.__type = "literal_str"
                if isinstance(self.__data, bytes):
                    self.__data = try_utf16_conv(self.__data[1:-1])
            elif self.__raw.startswith(b"<") and self.__raw.endswith(b">"):
                self.__type = "hex_str"
            elif self.__raw.startswith(b"/"):
                self.__type = "name"
            elif self.__raw == b"[":
                self.__type = "array"
            elif self.__raw == b"<<":
                self.__type = "dictionary"
            elif isinstance(self.__data, str):
                if self.__data.replace("-", "", 1).isnumeric():
                    self.__type = "numeric"
                    self.__data = int(self.__data)
                elif self.__data.replace(".", "", 1).replace("-", "", 1).isdigit():
                    self.__type = "numeric"
                    self.__data = float(self.__data)

    @property
    def offset(self) -> int:
        return self.__offset
    @property
    def length(self) -> int:
        return self.__length
    @property
    def type(self) -> str | None:
        return self.__type
    @property
    def raw(self) -> bytes:
        return self.__raw
    @property
    def data(self) -> str | bytes:
        return self.__data

class PdfTokenizer():
    def __init__(self, pdf_data: bytes) -> None:
        self.__pdf_data: bytes = pdf_data
        self.__token_list: list[PdfToken] = []

        # current position of tokenizer
        pos: int = 0

        while True:
            # skip whitespaces
            pos: int = self.__jump_to_next_token(pos)
            if pos == -1:
                break

            # search for potential end of token
            pos_end: int = self.__read_token(pos)
            if pos_end == -1:
                break

            # read new token
            token: bytes = self.__pdf_data[pos:pos_end]

            # header
            if token.startswith(b"\x25PDF-") and len(token) >= 8:
                self.__token_list.append(PdfToken(pos, token[:8]))   
                pos = pos + 8
                continue

            # stream
            if token == b"stream":
                self.__token_list.append(PdfToken(pos, token))

                stream_begin = self.__jump_to_next_token(pos_end)
                stream_end = self.__pdf_data.find(b"endstream", stream_begin)

                self.__token_list.append(PdfToken(stream_begin, self.__pdf_data[stream_begin:stream_end].rstrip(), True))
                self.__token_list.append(PdfToken(stream_end, self.__pdf_data[stream_end:stream_end + 9]))
                pos = stream_end + 9

                continue

            if token.startswith(b"obj"):
                self.__token_list.append(PdfToken(pos, token[:3]))
                pos = pos + 3
                continue

            if token.startswith(b"endobj"):
                self.__token_list.append(PdfToken(pos, token[:6]))
                pos = pos + 6
                continue

            # list of special token characters
            matrix_distances = [(t, token.find(t)) for t in DELIMITER_CHARACTERS[0:8]]
            matrix_distances = [i for i in sorted(matrix_distances, key=lambda t: t[1]) if i[1] != -1]

            if len(matrix_distances) == 0:
                # default handling, if no special token character is found
                self.__token_list.append(PdfToken(pos, token))
                pos = pos + len(token)
                continue

            tuple_nearest: tuple[bytes, int] = matrix_distances[0]
            token_special: bytes = tuple_nearest[0]
            token_special_pos: int = tuple_nearest[1]
            
            match token_special:
                case b"[" | b"]":
                    if token_special_pos > 0: # case 'contains'
                        self.__token_list.append(PdfToken(pos, token[:token_special_pos]))

                    # case 'startswith'
                    self.__token_list.append(PdfToken(pos+token_special_pos, token[token_special_pos:token_special_pos+1]))
                    pos = pos + token_special_pos + 1

                    continue
                case b"(": # '(' and ')'
                    if token_special_pos == 0: # case 'startswith'
                        pt_position = pos + 1
                        _parenthesis_open = 1
                        while _parenthesis_open > 0:
                            pt_open_next = self.__pdf_data.find(b"(", pt_position)
                            pt_close_next = self.__pdf_data.find(b")", pt_position)

                            if pt_close_next != -1 and pt_open_next != -1:
                                if pt_close_next < pt_open_next:
                                    _parenthesis_open = _parenthesis_open - 1
                                    pt_position = pt_close_next + 1
                                    continue
                                if pt_open_next < pt_close_next:
                                    _parenthesis_open = _parenthesis_open + 1
                                    pt_position = pt_open_next + 1
                                    continue
                            if pt_close_next != -1:
                                _parenthesis_open = _parenthesis_open - 1
                                pt_position = pt_close_next + 1
                                continue
                            break
                        token = self.__pdf_data[pos:pt_position]
                        self.__token_list.append(PdfToken(pos, token))
                        pos = pt_position
                        continue
                    else: # case 'contains'
                        log.critical(f"'PdfTokenizer' is missing implementation to handle '{str(token_special, encoding='ascii', errors='ignore')}'")
                        pos = pos + 1
                case b"<": # '<' and '>' and '<<'
                    if token_special_pos > 0: # case 'contains'
                        self.__token_list.append(PdfToken(pos, token[:token_special_pos]))
                        pos = pos + token_special_pos
                        continue

                    # case 'startswith
                    check_pos = token.find(b"<<")
                    if check_pos == -1: # case hex string
                        _hex_string_end = self.__pdf_data.find(b">", pos) + 1
                        if _hex_string_end == -1:
                            log.warning(f"hex string in pdf file has no closing bracket")
                            pos = pos + len(token)
                            continue
                        self.__token_list.append(PdfToken(pos, self.__pdf_data[pos:_hex_string_end]))
                        pos = _hex_string_end
                        continue

                    # case dictionary
                    self.__token_list.append(PdfToken(pos, token[:2]))
                    pos = pos + 2

                    continue
                case b"/":
                    if token_special_pos > 0: # case 'contains'
                        self.__token_list.append(PdfToken(pos, token[:token_special_pos]))
                        pos = pos + token_special_pos
                        continue

                    # case 'startswith'
                    check_pos = [(t, token.find(t, 1)) for t in DELIMITER_CHARACTERS[0:8]]
                    check_pos = [i for i in sorted(check_pos, key=lambda t: t[1]) if i[1] != -1]

                    if len(check_pos) == 0:
                        self.__token_list.append(PdfToken(pos, token))
                        pos = pos + len(token)
                    else:
                        self.__token_list.append(PdfToken(pos, token[:check_pos[0][1]]))
                        pos = pos + check_pos[0][1]
                    continue
                case b"%":
                    if token_special_pos > 0: # case 'contains'
                        self.__token_list.append(PdfToken(pos, token[:token_special_pos]))

                    # case 'startswith'
                    _line_end = self.__pdf_data.find(b"\x0a", pos+token_special_pos)
                    if _line_end == -1:
                        log.warning(f"comment in pdf file has no end of line-marker")
                        pos = pos + len(token)
                        continue

                    # add comment token
                    token = self.__pdf_data[pos+token_special_pos:_line_end].rstrip()
                    
                    self.__token_list.append(PdfToken(pos + token_special_pos, token))
                    pos = _line_end
                case b">":
                    if token_special_pos > 0: # case 'contains'
                        self.__token_list.append(PdfToken(pos, token[:token_special_pos]))
                        pos = pos + token_special_pos
                        continue

                    # case 'startswith'
                    check_pos = token.find(b">>")
                    if check_pos == -1: # case hex string
                        self.__token_list.append(PdfToken(pos, token[:1]))
                        pos = pos + 1
                        continue

                    # case dictionary
                    self.__token_list.append(PdfToken(pos, token[:2]))
                    pos = pos + 2

                    continue
                case _:
                    log.critical(f"'PdfTokenizer' is missing implementation to handle '{str(token_special, encoding='ascii', errors='ignore')}'")
                    pos = pos + 1
            continue

    # searches for the next whitespace occurance
    def __read_token(self, offset: int) -> int:
        match = WHITESPACE_PATTERN.search(self.__pdf_data, offset)
        if match is None:
            return -1
        else:
            return match.start()

    # search for the next non-whitespace character
    def __jump_to_next_token(self, offset: int) -> int:
        match = WHITESPACE_ANTI_PATTERN.search(self.__pdf_data, offset)
        if match is None:
            return -1
        else:
            return match.start()

    # results
    @property
    def token_list(self) -> list[PdfToken]:
        return self.__token_list

class AbstractObject(abc.ABC):
    def __init__(self, section: ContainerSection, pdf_tokens: list[PdfToken], index: int) -> None:
        self._section = section
        self._pdf_tokens: list[PdfToken] = pdf_tokens
        self._index: int = index

        # by default, an object is constructed by one (or more) tokens
        self._token_length: int = 1

        # initialize object stats from first token
        token: PdfToken = self._pdf_tokens[self._index]
        self._fragment: ContainerFragment = ContainerFragment(token.offset, token.length)
        self._fragment.set_attribute("type", token.type)
    def _determine_object(self, token: PdfToken, i: int):
        match token.type:
            case "numeric":
                return NumericObject(self._section, self._pdf_tokens, i)
            case "dictionary":
                return DictionaryObject(self._section, self._pdf_tokens, i)
            case "array":
                return ArrayObject(self._section, self._pdf_tokens, i)
            case "name" | "null" | "hex_str" | "literal_str" | "boolean":
                return ArbitraryObject(self._section, self._pdf_tokens, i)
            case _:
                return None

    # number of tokens used
    @property
    def token_length(self) -> int:
        return self._token_length
    @property
    def as_fragment(self) -> ContainerFragment:
        return self._fragment

class ArbitraryObject(AbstractObject):
    def __init__(self, s: ContainerSection, pt: list[PdfToken], n: int) -> None:
        super().__init__(s, pt, n)
        self._fragment.set_attribute("offset", None)
        self._fragment.set_attribute("length", None)
        self._fragment.set_attribute("value", str(self._pdf_tokens[self._index].data) if isinstance(self._pdf_tokens[self._index].data, bytes) else self._pdf_tokens[self._index].data) 

class NumericObject(AbstractObject): # <<<>>>
    def __init__(self, s: ContainerSection, pt: list[PdfToken], n: int) -> None:
        super().__init__(s, pt, n)

        # check whether enough tokens are available
        if self._index + 4 < len(self._pdf_tokens):
            token_0_current: PdfToken = self._pdf_tokens[self._index]
            token_1_future: PdfToken = self._pdf_tokens[self._index + 1]
            token_2_future: PdfToken = self._pdf_tokens[self._index + 2]
            token_3_future: PdfToken = self._pdf_tokens[self._index + 3]

            # case 1: indirect object (n m obj) (endobj)
            if token_1_future.type == "numeric" and token_2_future.type == "indirect_obj":
                # indirect object frame requires 4 tokens: n m obj endobj
                self._token_length = 4

                # as indirect objects are modeled as numeric objects, the type has to be set manually
                
                self._fragment.set_attribute("type", token_2_future.type)

                # gather numbers
                self._fragment.set_attribute("object_number", token_0_current.data)
                self._fragment.set_attribute("generation_number", token_1_future.data)

                # handle all types which can be encapsulated in an indirect object
                i: int = self._index + 3
                obj = self._determine_object(token_3_future, i)
                if obj is None:
                    log.critical(f"'NumericObject' is missing implementation to handle '{token_3_future.type}' (token #{i})")
                    return

                # add token length during recursion
                self._token_length = self._token_length + obj.token_length

                # set (nested) data
                self._fragment.set_attribute("data", obj.as_fragment.as_dictionary)

                return
            # case 2: reference object (n m R)
            if token_1_future.type == "numeric" and token_2_future.raw == b"R":
                # reference object requires 3 tokens: n m R
                self._token_length = 3

                # as reference objects are modeled as numeric objects, the type has to be set manually
                self._fragment.set_attribute("offset", None)
                self._fragment.set_attribute("length", None)
                self._fragment.set_attribute("type", "reference")
                self._fragment.set_attribute("object_number", token_0_current.data)
                self._fragment.set_attribute("generation_number", token_1_future.data)

                return
        # case 3: actual numerical value
        self._fragment.set_attribute("offset", None)
        self._fragment.set_attribute("length", None)
        self._fragment.set_attribute("value", self._pdf_tokens[self._index].data)

class DictionaryObject(AbstractObject): # <<<>>>
    def __init__(self, s: ContainerSection, pt: list[PdfToken], n: int) -> None:
        super().__init__(s, pt, n)

        # dictionaries are always encapsulated in two tokens
        self._token_length = 2

        # collector for nested objects
        nested_dict: dict = {}

        i: int = self._index + 1
        while self._pdf_tokens[i].type == "name":
            # first name is key
            dictionary_key: str = self._pdf_tokens[i].data

            # key is also one token each
            self._token_length = self._token_length + 1

            # increment
            i = i + 1

            # second item is value
            dictionary_value: PdfToken = self._pdf_tokens[i]

            # make sure key exists
            if not dictionary_key in nested_dict:
                nested_dict[dictionary_key] = None

            obj = self._determine_object(dictionary_value, i)
            if obj is None:
                nested_dict[dictionary_key] = None
                log.critical(f"'DictionaryObject' is missing implementation to handle '{dictionary_value.type}' (token #{i})")
                continue

            # skip processed tokens
            i = i + obj.token_length

            # add tokens
            self._token_length = self._token_length + obj.token_length

            # add dictionary key
            nested_dict[dictionary_key] = obj.as_fragment.as_dictionary

        # if segments available
        if i + 3 < len(self._pdf_tokens):
            token_stream_start: PdfToken = self._pdf_tokens[i + 1]
            token_stream: PdfToken = self._pdf_tokens[i + 2]

            # check for stream element
            if token_stream_start.type == "stream":
                # add tokens
                self._token_length = self._token_length + 3

                # append stream element
                _stream_fragment: ContainerFragment = ContainerFragment(token_stream.offset, token_stream.length)
                _stream_fragment.set_attribute("type", token_stream.type)

                nested_dict["stream"] = _stream_fragment.as_dictionary

                # recursive analysis: check for image in stream
                if ("/Filter" in nested_dict) and ("value" in nested_dict["/Filter"]):
                    match nested_dict["/Filter"]["value"]:
                        case "/FlateDecode":
                            self._section.new_analysis(token_stream.offset, token_stream.length)
                        case _:
                            log.warning(f"pdf stream on position {token_stream.offset} is encoded by an unsupported filter: '{nested_dict['/Filter']['value']}'")

        self._fragment.set_attribute("offset", None)
        self._fragment.set_attribute("length", None)
        self._fragment.set_attribute("dict", nested_dict)

class ArrayObject(AbstractObject): # <<<>>>
    def __init__(self, s: ContainerSection, pt: list[PdfToken], n: int) -> None:
        super().__init__(s, pt, n)

        # arrays are always encapsulated in two tokens
        self._token_length = 2

        # collector for nested items
        nested_list: list = []

        i: int = self._index + 1
        while i < len(self._pdf_tokens) and self._pdf_tokens[i].raw != b"]":
            # access next array element
            token: PdfToken = self._pdf_tokens[i]

            obj = self._determine_object(token, i)
            if obj is None:
                nested_list.append(None)
                log.critical(f"'ArrayObject' is missing implementation to handle '{token.type}' (token #{i})")
                i = i + 1
                continue

            # skip processed tokens
            i = i + obj.token_length

            # add tokens
            self._token_length = self._token_length + obj.token_length

            # add dictionary key
            nested_list.append(obj.as_fragment.as_dictionary)

        self._fragment.set_attribute("offset", None)
        self._fragment.set_attribute("length", None)
        self._fragment.set_attribute("array", nested_list)

# MODULE ENTRYPOINT

class ApplicationPdfAnalysis(AbstractStructureAnalysis):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def __find_next_token_position(tokens: list[PdfToken], input_offset: int) -> int:
        for i in range(len(tokens)):
            if tokens[i].offset >= input_offset:
                return tokens[i + 1].offset
        return input_offset

    def process(self, section: ContainerSection) -> ContainerSection:
        pdf_tokenizer: PdfTokenizer = PdfTokenizer(section.data)

        tokens_all: list[PdfToken] = pdf_tokenizer.token_list
        tokens_coms: list[PdfToken] = [t for t in pdf_tokenizer.token_list if t.type == "_comment"]
        tokens_func: list[PdfToken] = [t for t in pdf_tokenizer.token_list if t.type != "_comment"]

        i: int = 0

        # header segment
        pdf_header: ContainerSegment = ContainerSegment("header")
        while i < len(tokens_func):
            token: PdfToken = tokens_func[i]
            if token.type == "_header":
                fragment: ContainerFragment = ContainerFragment(token.offset, self.__find_next_token_position(tokens_all, token.offset) - token.offset)
                fragment.set_attribute("version", float(str(token.raw, "utf-8")[5:8]))
                pdf_header.add_fragment(fragment)

                i = i + 1
                break
            i = i + 1
        section.add_segment(pdf_header)

        while i < len(tokens_func):
            # body segment
            pdf_body: ContainerSegment = ContainerSegment("body")
            while i < len(tokens_func):
                token: PdfToken = tokens_func[i]
                match token.type:
                    case "numeric":
                        obj = NumericObject(section, tokens_func, i)

                        fragment: ContainerFragment = obj.as_fragment
                        fragment.set_attribute("length", self.__find_next_token_position(tokens_all, tokens_func[i + obj.token_length - 1].offset) - token.offset)
                        pdf_body.add_fragment(fragment)

                        i = i + obj.token_length
                    case "_xref" | "_trailer" | "_startxref":
                        break
                    case _:
                        section.new_analysis(token.offset)
                        section.set_length(token.offset)
                        i = len(tokens_func) # use condition to abort loop
                        continue
            section.add_segment(pdf_body)
            if i == len(tokens_func):
                break

            # xref segment
            pdf_xref_table: ContainerSegment = ContainerSegment("xref")
            if tokens_func[i].type == "_xref":
                # add fragment for xref marker
                fragment: ContainerFragment = ContainerFragment(tokens_func[i].offset, self.__find_next_token_position(tokens_all, tokens_func[i].offset) - tokens_func[i].offset)
                pdf_xref_table.add_fragment(fragment)

                i = i + 1
                while i < len(tokens_func):
                    token: PdfToken = tokens_func[i]

                    match token.type:
                        case "numeric":
                            range_offset: int = token.data
                            cross_ref_entries: int = tokens_func[i + 1].data

                            # add fragment for xref table segment
                            fragment: ContainerFragment = ContainerFragment(token.offset, tokens_func[i + 2].offset - token.offset)
                            pdf_xref_table.add_fragment(fragment)

                            i = i + 2
                            c: int = 0
                            while c < cross_ref_entries and i + 3 < len(tokens_func):
                                # add fragment for each xref table entry
                                token: PdfToken = tokens_func[i]
                                fragment: ContainerFragment = ContainerFragment(token.offset, tokens_func[i + 3].offset - token.offset)
                                fragment.set_attribute("object_number", range_offset + c)
                                fragment.set_attribute("byte_offset", token.data)
                                fragment.set_attribute("generation_number", tokens_func[i + 1].data)
                                fragment.set_attribute("in_use", tokens_func[i + 2].raw == b"n")

                                pdf_xref_table.add_fragment(fragment)
                                i = i + 3
                                c = c + 1
                        case "_trailer" | "_startxref":
                            break
                        case _:
                            log.critical(f"'XRefParser' is missing implementation to handle '{token.type}' (token #{i})")
                            i = i + 1
            section.add_segment(pdf_xref_table)

            # trailer segment
            pdf_trailer: ContainerSegment = ContainerSegment("trailer")
            if tokens_func[i].type == "_trailer":
                # add fragment for trailer marker
                fragment: ContainerFragment = ContainerFragment(tokens_func[i].offset, self.__find_next_token_position(tokens_all, tokens_func[i].offset) - tokens_func[i].offset)
                pdf_trailer.add_fragment(fragment)

                i = i + 1
                while i < len(tokens_func):
                    token: PdfToken = tokens_func[i]

                    match token.type:
                        case "dictionary":
                            obj = DictionaryObject(section, tokens_func, i)

                            fragment: ContainerFragment = obj.as_fragment
                            fragment.set_attribute("offset", token.offset)
                            fragment.set_attribute("length", tokens_func[i + obj.token_length].offset - token.offset)
                            pdf_trailer.add_fragment(fragment)

                            i = i + obj.token_length
                        case "_startxref":
                            break
                        case _:
                            log.critical(f"'TrailerParser' is missing implementation to handle '{token.type}' (token #{i})")
                            i = i + 1
            section.add_segment(pdf_trailer)

            # startxref segment
            pdf_startxref: ContainerSegment = ContainerSegment("startxref")
            if tokens_func[i].type == "_startxref":
                token: PdfToken = tokens_func[i]
                token_numeric: PdfToken = tokens_func[i + 1]

                fragment: ContainerFragment = ContainerFragment(token.offset, token_numeric.offset - token.offset)
                fragment_numeric: ContainerFragment = ContainerFragment(token_numeric.offset, tokens_func[i + 2].offset - token_numeric.offset)
                fragment_numeric.set_attribute("reference", token_numeric.data)

                pdf_startxref.add_fragment(fragment)
                pdf_startxref.add_fragment(fragment_numeric)

                i = i + 2
            section.add_segment(pdf_startxref)

            # eof segment
            pdf_eof: ContainerSegment = ContainerSegment("eof")
            if tokens_func[i].type == "_eof":
                token: PdfToken = tokens_func[i]

                token_length: int = (self.__find_next_token_position(tokens_all, token.offset) if i + 1 < len(tokens_func) else len(section.data)) - token.offset

                fragment = ContainerFragment(token.offset, token_length)
                pdf_eof.add_fragment(fragment)

                i = i + 1

            section.add_segment(pdf_eof)
            section.calculate_length()

            pdf_comments: ContainerSegment = ContainerSegment("comments")
            for x in [ContainerFragment(t.offset, self.__find_next_token_position(tokens_all, t.offset) - t.offset) for t in tokens_coms if t.offset < section.length]:
                pdf_comments.add_fragment(x)

            section.add_segment(pdf_comments)
            pdf_whitespaces: Coverage = Coverage("whitespaces", [{"o": t.offset, "l": t.length} for t in tokens_all if t.offset < section.length], section.length)
            section.add_segment(pdf_whitespaces.as_uncovered_segment)

        return section
