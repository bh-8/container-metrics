"""
application_pdf.py

references:
    - https://www.iso.org/standard/75839.html
    - https://pdfa.org/resource/iso-32000-2/

"""

# IMPORTS

import abc
from abstract_structure_mapping import *
import re
from static_utils import try_utf8_conv

# GLOBAL STATIC MAPPINGS

WHITESPACE_CHARACTERS: list[bytes] = [
    b"\x00", b"\x09", b"\x0a", b"\x0c", b"\x0d", b"\x20"
]
DELIMITER_CHARACTERS: list[bytes] = [
    b"(", b")",
    b"<", b">",
    b"[", b"]",
    b"{", b"}",
    b"/", b"%"
]
WHITESPACE_PATTERN: re.Pattern[bytes] = re.compile(DELIMITER_CHARACTERS[4] + b"".join([re.escape(wc) for wc in WHITESPACE_CHARACTERS]) + DELIMITER_CHARACTERS[5])
WHITESPACE_ANTI_PATTERN: re.Pattern[bytes] = re.compile(b"[^" + b"".join([re.escape(wc) for wc in WHITESPACE_CHARACTERS]) + DELIMITER_CHARACTERS[5])

# SPECIFIC MEDIA FORMAT PARTS

class PdfToken():
    def __init__(self, offset: int, raw: bytes, is_stream: bool = False) -> None:
        self.offset: int = offset
        self.length: int = len(raw)
        self.type: str | None = "stream" if is_stream else None
        self.raw: bytes = raw
        self.data = try_utf8_conv(self.raw)

        if self.type == None:
            if self.raw.startswith(b"\x25PDF-") and self.length == 8:
                self.type = "_header"
            elif self.raw == b"xref":
                self.type = "_xref"
            elif self.raw == b"trailer":
                self.type = "_trailer"
            elif self.raw == b"startxref":
                self.type = "_startxref"
            elif self.raw == b"\x25\x25EOF":
                self.type = "_eof"
            elif self.raw.startswith(DELIMITER_CHARACTERS[9]):
                self.type = "_comment"
            elif self.raw == b"obj":
                self.type = "indirect_obj"
            elif self.raw == b"stream":
                self.type = "stream"
            elif self.raw == b"true" or self.raw == b"false":
                self.type = "boolean"
                self.data = self.raw == b"true"
            elif self.raw == b"null":
                self.type = "null"
            elif self.raw.startswith(DELIMITER_CHARACTERS[0]) and self.raw.endswith(DELIMITER_CHARACTERS[1]):
                self.type = "literal_str"
            elif self.raw.startswith(DELIMITER_CHARACTERS[2]) and self.raw.endswith(DELIMITER_CHARACTERS[3]):
                self.type = "hex_str"
            elif self.raw.startswith(DELIMITER_CHARACTERS[8]):
                self.type = "name"
            elif self.raw == b"[":
                self.type = "array"
            elif self.raw == b"<<":
                self.type = "dictionary"
            elif isinstance(self.data, str):
                if self.data.replace("-", "", 1).isnumeric():
                    self.type = "numeric"
                    self.data = int(self.data)
                elif self.data.replace(".", "", 1).replace("-", "", 1).isdigit():
                    self.type = "numeric"
                    self.data = float(self.data)
class PdfTokenizer():
    def __init__(self, pdf_data: bytes) -> None:
        self.__pdf_data: bytes = pdf_data
        self.__token_list: list[PdfToken] = []

        # current position of tokenizer
        pos: int = 0

        while True:
            # skip whitespaces
            pos: int = self.jump_to_next_token(pos)
            if pos == -1:
                break

            # search for potential end of token
            pos_end: int = self.read_token(pos)
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

                stream_begin = self.jump_to_next_token(pos_end)
                stream_end = self.__pdf_data.find(b"endstream", stream_begin)

                self.__token_list.append(PdfToken(stream_begin, self.__pdf_data[stream_begin:stream_end].rstrip(), True))
                self.__token_list.append(PdfToken(stream_end, self.__pdf_data[stream_end:stream_end + 9]))
                pos = stream_end + 9

                continue

            # special treatment for '('
            if token.startswith(DELIMITER_CHARACTERS[0]):
                pt_position = pos + 1
                _parenthesis_open = 1
                while _parenthesis_open > 0:
                    pt_open_next = self.__pdf_data.find(DELIMITER_CHARACTERS[0], pt_position)
                    pt_close_next = self.__pdf_data.find(DELIMITER_CHARACTERS[1], pt_position)

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

            # special treatment for '<'
            if token.startswith(DELIMITER_CHARACTERS[2]):
                if token.startswith(b"<<"):
                    token = self.__pdf_data[pos:pos + 2]
                    self.__token_list.append(PdfToken(pos, token))
                    pos = pos + 2
                else:
                    _hex_string_end = self.__pdf_data.find(DELIMITER_CHARACTERS[3], pos) + 1
                    token = self.__pdf_data[pos:_hex_string_end]
                    self.__token_list.append(PdfToken(pos, token))
                    pos = _hex_string_end
                continue

            # special treatment for '['
            if token.startswith(DELIMITER_CHARACTERS[4]):
                token = self.__pdf_data[pos:pos + 1]
                self.__token_list.append(PdfToken(pos, token))
                pos = pos + 1
                continue

            # special treatment for '{'
            if token.startswith(DELIMITER_CHARACTERS[6]):
                pass
                # TODO: implement this ...

            # special treatment for ']'
            check_pos = token.find(b"]")
            if check_pos != -1:
                if check_pos > 0:
                    self.__token_list.append(PdfToken(pos, token[:check_pos]))
                self.__token_list.append(PdfToken(pos + check_pos, token[check_pos:check_pos + 1]))
                pos = pos + check_pos + 1
                continue

            # special treatment for '/'
            if token.startswith(DELIMITER_CHARACTERS[8]):
                check_pos = token.find(b"/", 1)
                if check_pos == -1:
                    self.__token_list.append(PdfToken(pos, token))
                    pos = pos + len(token)
                else:
                    self.__token_list.append(PdfToken(pos, token[:check_pos]))
                    pos = pos + check_pos
                continue

            # special treatment for '>>'
            check_pos = token.find(b">>")
            if check_pos != -1:
                if check_pos > 0:
                    self.__token_list.append(PdfToken(pos, token[:check_pos]))
                self.__token_list.append(PdfToken(pos + check_pos, token[check_pos:check_pos + 2]))
                pos = pos + check_pos + 2
                continue

            # special treatment for '%'
            check_pos = token.find(b"%")
            if check_pos != -1:
                if check_pos > 0:
                    self.__token_list.append(PdfToken(pos, token[:check_pos]))

                _line_end = self.__pdf_data.find(b"\x0a", pos + check_pos)
                if _line_end == -1:
                    break # stop tokenizer when hitting an incomplete line

                token = self.__pdf_data[pos + check_pos:_line_end].rstrip()

                self.__token_list.append(PdfToken(pos + check_pos, token))
                pos = _line_end
                continue

            # default token processing
            self.__token_list.append(PdfToken(pos, token))
            pos = pos + len(token)

    # searches for the next whitespace occurance
    def read_token(self, offset: int) -> int:
        match = WHITESPACE_PATTERN.search(self.__pdf_data, offset)
        if match is None:
            return -1
        else:
            return match.start()

    # search for the next non-whitespace character
    def jump_to_next_token(self, offset: int) -> int:
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
    def __init__(self, pdf_tokens: list[PdfToken], index: int) -> None:
        self.pdf_tokens: list[PdfToken] = pdf_tokens
        self.index: int = index

        # by default, an object is constructed by one (or more) tokens
        self.object_length: int = 1

        # initialize object stats from first token
        token: PdfToken = self.pdf_tokens[self.index]
        self.fragment: ContainerFragment = ContainerFragment(token.offset, token.length)
        self.fragment.set_attribute("type", token.type)

    def determine_object(self, token: PdfToken, i: int):
        match token.type:
            case "numeric":
                return NumericObject(self.pdf_tokens, i)
            case "dictionary":
                return DictionaryObject(self.pdf_tokens, i)
            case "array":
                return ArrayObject(self.pdf_tokens, i)
            case "name" | "null" | "hex_str" | "literal_str" | "boolean":
                return ArbitraryObject(self.pdf_tokens, i)
            case _:
                return None

    # number of tokens used
    def get_length(self) -> int:
        return self.object_length

    # output
    def get_fragment(self) -> ContainerFragment:
        return self.fragment
class ArbitraryObject(AbstractObject):
    def __init__(self, pt: list[PdfToken], n: int) -> None:
        super().__init__(pt, n)
        self.fragment.set_attribute("offset", None)
        self.fragment.set_attribute("length", None)
        self.fragment.set_attribute("data", self.pdf_tokens[self.index].data)
class NumericObject(AbstractObject): # <<<>>>
    def __init__(self, pt: list[PdfToken], n: int) -> None:
        super().__init__(pt, n)

        # check whether enough tokens are available
        if self.index + 4 < len(self.pdf_tokens):
            token_0_current: PdfToken = self.pdf_tokens[self.index]
            token_1_future: PdfToken = self.pdf_tokens[self.index + 1]
            token_2_future: PdfToken = self.pdf_tokens[self.index + 2]
            token_3_future: PdfToken = self.pdf_tokens[self.index + 3]

            # case 1: indirect object (n m obj) (endobj)
            if token_1_future.type == "numeric" and token_2_future.type == "indirect_obj":
                # indirect object frame requires 4 tokens: n m obj endobj
                self.object_length = 4

                # as indirect objects are modeled as numeric objects, the type has to be set manually
                
                self.fragment.set_attribute("type", token_2_future.type)

                # gather numbers
                self.fragment.set_attribute("object_number", token_0_current.data)
                self.fragment.set_attribute("generation_number", token_1_future.data)

                # handle all types which can be encapsulated in an indirect object
                i: int = self.index + 3
                obj = self.determine_object(token_3_future, i)
                if obj is None:
                    # logger.critical(f"application_pdf.py: 'IndirectObject' is missing implementation to handle '{token_3_future.type}' (token #{i})")
                    return

                # add token length during recursion
                self.object_length = self.object_length + obj.get_length()

                # set (nested) data
                self.fragment.set_attribute("data", obj.get_fragment().get_dictionary())

                return
            # case 2: reference object (n m R)
            if token_1_future.type == "numeric" and token_2_future.raw == b"R":
                # reference object requires 3 tokens: n m R
                self.object_length = 3

                # as reference objects are modeled as numeric objects, the type has to be set manually
                self.fragment.set_attribute("offset", None)
                self.fragment.set_attribute("length", None)
                self.fragment.set_attribute("type", "reference")
                self.fragment.set_attribute("object_number", token_0_current.data)
                self.fragment.set_attribute("generation_number", token_1_future.data)

                return
        # case 3: actual numerical value
        self.fragment.set_attribute("offset", None)
        self.fragment.set_attribute("length", None)
        self.fragment.set_attribute("data", self.pdf_tokens[self.index].data)
class DictionaryObject(AbstractObject): # <<<>>>
    def __init__(self, pt: list[PdfToken], n: int) -> None:
        super().__init__(pt, n)

        # dictionaries are always encapsulated in two tokens
        self.object_length = 2

        # collector for nested objects
        nested_dict: dict = {}

        i: int = self.index + 1
        while self.pdf_tokens[i].type == "name":
            # first name is key
            dictionary_key: str = self.pdf_tokens[i].data

            # key is also one token each
            self.object_length = self.object_length + 1

            # increment
            i = i + 1

            # second item is value
            dictionary_value: PdfToken = self.pdf_tokens[i]

            # make sure key exists
            if not dictionary_key in nested_dict:
                nested_dict[dictionary_key] = None

            obj = self.determine_object(dictionary_value, i)
            if obj is None:
                nested_dict[dictionary_key] = None
                # logger.critical(f"application_pdf.py: 'DictionaryObject' is missing implementation to handle '{dictionary_value.type}' (token #{i})")
                continue

            # skip processed tokens
            i = i + obj.get_length()

            # add tokens
            self.object_length = self.object_length + obj.get_length()

            # add dictionary key
            nested_dict[dictionary_key] = obj.get_fragment().get_dictionary()

        # if segments available
        if i + 3 < len(self.pdf_tokens):
            token_stream_start: PdfToken = self.pdf_tokens[i + 1]
            token_stream: PdfToken = self.pdf_tokens[i + 2]

            # check for stream element
            if token_stream_start.type == "stream":
                # add tokens
                self.object_length = self.object_length + 3

                # append stream element
                _stream_fragment: ContainerFragment = ContainerFragment(token_stream.offset, token_stream.length)
                _stream_fragment.set_attribute("type", token_stream.type)

                nested_dict["stream"] = _stream_fragment.get_dictionary()

        self.fragment.set_attribute("offset", None)
        self.fragment.set_attribute("length", None)
        self.fragment.set_attribute("data", nested_dict)
class ArrayObject(AbstractObject): # <<<>>>
    def __init__(self, pt: list[PdfToken], n: int) -> None:
        super().__init__(pt, n)

        # arrays are always encapsulated in two tokens
        self.object_length = 2

        # collector for nested items
        nested_list: list = []

        i: int = self.index + 1
        while i < len(self.pdf_tokens) and self.pdf_tokens[i].raw != DELIMITER_CHARACTERS[5]:
            # access next array element
            token: PdfToken = self.pdf_tokens[i]

            obj = self.determine_object(token, i)
            if obj is None:
                nested_list.append(None)
                # logger.critical(f"application_pdf.py: 'ArrayObject' is missing implementation to handle '{token.type}' (token #{i})")
                i = i + 1
                continue

            # skip processed tokens
            i = i + obj.get_length()

            # add tokens
            self.object_length = self.object_length + obj.get_length()

            # add dictionary key
            nested_list.append(obj.get_fragment().get_dictionary())

        self.fragment.set_attribute("offset", None)
        self.fragment.set_attribute("length", None)
        self.fragment.set_attribute("data", nested_list)

# MODULE ENTRYPOINT

class ApplicationPdfAnalysis(AbstractStructureAnalysis):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def find_next_token_position(tokens: list[PdfToken], input_offset: int) -> int:
        for i in range(len(tokens)):
            if tokens[i].offset >= input_offset:
                return tokens[i + 1].offset
        return input_offset

    def process_section(self, section: ContainerSection) -> ContainerSection:
        pdf_tokenizer: PdfTokenizer = PdfTokenizer(section.get_data())

        tokens_all: list[PdfToken] = pdf_tokenizer.token_list
        tokens_coms: list[PdfToken] = [t for t in pdf_tokenizer.token_list if t.type == "_comment"]
        tokens_func: list[PdfToken] = [t for t in pdf_tokenizer.token_list if t.type != "_comment"]

        i: int = 0

        # header segment
        pdf_header: ContainerSegment = ContainerSegment()
        while i < len(tokens_func):
            token: PdfToken = tokens_func[i]
            if token.type == "_header":
                fragment: ContainerFragment = ContainerFragment(token.offset, self.find_next_token_position(tokens_all, token.offset) - token.offset)
                fragment.set_attribute("version", float(str(token.raw, "utf-8")[5:8]))
                pdf_header.add_fragment(fragment)

                i = i + 1
                break
            i = i + 1
        section.add_segment("header", pdf_header)

        while i < len(tokens_func):
            # body segment
            pdf_body: ContainerSegment = ContainerSegment()
            while i < len(tokens_func):
                token: PdfToken = tokens_func[i]
                match token.type:
                    case "numeric":
                        obj = NumericObject(tokens_func, i)

                        fragment: ContainerFragment = obj.get_fragment()
                        fragment.set_attribute("length", self.find_next_token_position(tokens_all, tokens_func[i + obj.get_length() - 1].offset) - token.offset)
                        pdf_body.add_fragment(fragment)

                        i = i + obj.get_length()
                    case "_xref" | "_trailer" | "_startxref":
                        break
                    case _:
                        section.new_analysis(token.offset)
                        section.set_length(token.offset)
                        i = len(tokens_func) # use condition to abort loop
                        continue
            section.add_segment("body", pdf_body)
            if i == len(tokens_func):
                break

            # xref segment
            pdf_xref_table: ContainerSegment = ContainerSegment()
            if tokens_func[i].type == "_xref":
                # add fragment for xref marker
                fragment: ContainerFragment = ContainerFragment(tokens_func[i].offset, self.find_next_token_position(tokens_all, tokens_func[i].offset) - tokens_func[i].offset)
                pdf_xref_table.add_fragment(fragment)

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
                            # logger.critical(f"application_pdf.py: 'XRefParser' is missing implementation to handle '{token.type}' (token #{i})")
                            i = i + 1
            section.add_segment("xref", pdf_xref_table)

            # trailer segment
            pdf_trailer: ContainerSegment = ContainerSegment()
            if tokens_func[i].type == "_trailer":
                # add fragment for trailer marker
                fragment: ContainerFragment = ContainerFragment(tokens_func[i].offset, self.find_next_token_position(tokens_all, tokens_func[i].offset) - tokens_func[i].offset)
                pdf_trailer.add_fragment(fragment)

                while i < len(tokens_func):
                    token: PdfToken = tokens_func[i]

                    match token.type:
                        case "dictionary":
                            obj = DictionaryObject(tokens_func, i)

                            fragment: ContainerFragment = obj.get_fragment()
                            fragment.set_attribute("offset", token.offset)
                            fragment.set_attribute("length", tokens_func[i + obj.get_length()].offset - token.offset)
                            pdf_trailer.add_fragment(fragment)

                            i = i + obj.get_length()
                        case "_startxref":
                            break
                        case _:
                            # logger.critical(f"application_pdf.py: 'TrailerParser' is missing implementation to handle '{token.type}' (token #{i})")
                            i = i + 1
            section.add_segment("trailer", pdf_trailer)

            # startxref segment
            pdf_startxref: ContainerSegment = ContainerSegment()
            if tokens_func[i].type == "_startxref":
                token: PdfToken = tokens_func[i]
                token_numeric: PdfToken = tokens_func[i + 1]

                fragment: ContainerFragment = ContainerFragment(token.offset, token_numeric.offset - token.offset)
                fragment_numeric: ContainerFragment = ContainerFragment(token_numeric.offset, tokens_func[i + 2].offset - token_numeric.offset)
                fragment_numeric.set_attribute("reference", token_numeric.data)

                pdf_startxref.add_fragment(fragment)
                pdf_startxref.add_fragment(fragment_numeric)

                i = i + 2
            section.add_segment("startxref", pdf_startxref)

            # eof segment
            pdf_eof: ContainerSegment = ContainerSegment()
            if tokens_func[i].type == "_eof":
                token: PdfToken = tokens_func[i]

                token_length: int = (self.find_next_token_position(tokens_all, token.offset) if i + 1 < len(tokens_func) else len(section.get_data())) - token.offset
                #if i + 1 < len(tokens_func):
                #    token_length = self.find_next_token_position(tokens_all, token.offset) - token.offset
                #else:
                #    token_length = len(section.get_data()) - token.offset

                fragment = ContainerFragment(token.offset, token_length)
                pdf_eof.add_fragment(fragment)

                i = i + 1

            section.add_segment("eof", pdf_eof)
            section.calculate_length()

            pdf_comments: ContainerSegment = ContainerSegment()
            for x in [ContainerFragment(t.offset, self.find_next_token_position(tokens_all, t.offset) - t.offset) for t in tokens_coms if t.offset < section.get_length()]:
                pdf_comments.add_fragment(x)

            section.add_segment("comments", pdf_comments)
            pdf_whitespaces: Coverage = Coverage([{"o": t.offset, "l": t.length} for t in tokens_all if t.offset < section.get_length()], section.get_length())
            section.add_segment("whitespaces", pdf_whitespaces.get_uncovered_segment())

        return section
