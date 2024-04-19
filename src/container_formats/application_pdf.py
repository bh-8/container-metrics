import abc
import enum
import re

WHITESPACE_CHARACTERS: list[bytes] = [b"\x00", b"\x09", b"\x0a", b"\x0c", b"\x0d", b"\x20"]
DELIMITER_CHARACTERS: list[bytes] = [b"(", b")", b"<", b">", b"[", b"]", b"{", b"}", b"/", b"%"]

WHITESPACE_PATTERN: re.Pattern[bytes] = re.compile(b"[" + b"".join([re.escape(wc) for wc in WHITESPACE_CHARACTERS]) + b"]")
WHITESPACE_ANTI_PATTERN: re.Pattern[bytes] = re.compile(b"[^" + b"".join([re.escape(wc) for wc in WHITESPACE_CHARACTERS]) + b"]")

class PdfTokenType(enum.Enum):
    NULL = 0                # 7.3.9
    BOOLEAN = 1             # 7.3.2
    NUMERIC = 2             # 7.3.3
    LITERAL_STRING = 3      # 7.3.4
    HEX_STRING = 4          # 7.3.4
    NAME = 5                # 7.3.5
    ARRAY = 6               # 7.3.6
    DICTIONARY = 7          # 7.3.7
    STREAM = 8              # 7.3.8
    INDIRECT_OBJECT = 10    # 7.3.10
    _HEADER = 11            # custom
    _XREF = 12              # custom
    _TRAILER = 13           # custom
    _STARTXREF = 14         # custom
    _EOF = 15               # custom
    _COMMENT = 16           # custom
class PdfToken():
    def __init__(self, token_id: int, position: int, raw: bytes) -> None:
        self.token_id: int = token_id
        self.position: int = position
        self.length: int = len(raw)
        self.type: PdfTokenType = PdfTokenType.NULL
        self.raw: bytes = raw

        if self.length == 8 and self.raw.startswith(b"%PDF-"):
            self.type = PdfTokenType._HEADER
        elif self.raw == b"\x25\x25EOF":
            self.type = PdfTokenType._EOF
        elif self.raw.startswith(b"%"):
            self.type = PdfTokenType._COMMENT
        elif self.raw == b"xref":
            self.type = PdfTokenType._XREF
        elif self.raw == b"trailer":
            self.type = PdfTokenType._TRAILER
        elif self.raw == b"startxref":
            self.type = PdfTokenType._STARTXREF
        elif self.raw == b"[":
            self.type = PdfTokenType.ARRAY
        elif self.raw == b"<<":
            self.type = PdfTokenType.DICTIONARY
        elif self.raw == b"obj":
            self.type = PdfTokenType.INDIRECT_OBJECT
        elif self.raw == b"stream":
            self.type = PdfTokenType.STREAM
        elif self.raw == b"true" or self.raw == b"false":
            self.type = PdfTokenType.BOOLEAN
        elif self.raw.startswith(b"<") and self.raw.endswith(b">"):
            self.type = PdfTokenType.HEX_STRING
        elif self.raw.startswith(b"(") and self.raw.endswith(b")"):
            self.type = PdfTokenType.LITERAL_STRING
        elif self.raw.startswith(b"/"):
            self.type = PdfTokenType.NAME
        else:
            try:
                token_str: str = str(self.raw, "utf-8")
                if token_str.isnumeric():
                    self.type = PdfTokenType.NUMERIC
            except:
                pass
class PdfTokenizer():
    def __init__(self, pdf_data: bytes) -> None:
        self.pdf_data: bytes = pdf_data
        self.token_list: list[PdfToken] = []
    def find_next_whitespace(self, position: int) -> int:
        match = WHITESPACE_PATTERN.search(self.pdf_data, position)
        if match is None:
            return -1
        else:
            return match.start()
    def find_next_token(self, position: int) -> int:
        match = WHITESPACE_ANTI_PATTERN.search(self.pdf_data, position)
        if match is None:
            return -1
        else:
            return match.start()
    def tokenize(self) -> None:
        self.token_list: list[PdfToken] = []
        _tokenizer_position: int = 0

        c: int = 0
        while True:
            _token_id: int = c
            c: int = c + 1

            # skip whitespaces
            _tokenizer_position = self.find_next_token(_tokenizer_position)
            if _tokenizer_position == -1:
                break

            # search for end of token
            _token_end = self.find_next_whitespace(_tokenizer_position)
            if _token_end == -1:
                break

            # read new token
            _token_data = self.pdf_data[_tokenizer_position:_token_end]

            # special treatment for literal strings
            if _token_data.startswith(b"("):
                _parenthesis_position = _tokenizer_position + 1
                _parenthesis_open = 1
                while _parenthesis_open > 0:
                    _next_parenthesis_open = self.pdf_data.find(b"(", _parenthesis_position)
                    _next_parenthesis_close = self.pdf_data.find(b")", _parenthesis_position)

                    if _next_parenthesis_close != -1 and _next_parenthesis_open != -1:
                        if _next_parenthesis_close < _next_parenthesis_open:
                            _parenthesis_open = _parenthesis_open - 1
                            _parenthesis_position = _next_parenthesis_close + 1
                            continue
                        if _next_parenthesis_open < _next_parenthesis_close:
                            _parenthesis_open = _parenthesis_open + 1
                            _parenthesis_position = _next_parenthesis_open + 1
                            continue
                    if _next_parenthesis_close != -1:
                        _parenthesis_open = _parenthesis_open - 1
                        _parenthesis_position = _next_parenthesis_close + 1
                        continue
                    break
                _token_data = self.pdf_data[_tokenizer_position:_parenthesis_position]
                self.token_list.append(PdfToken(_token_id, _tokenizer_position, _token_data))
                _tokenizer_position = _parenthesis_position
                continue
            # atomize '['
            if _token_data.startswith(b"[") and _token_data != b"[":
                self.token_list.append(PdfToken(_token_id, _tokenizer_position, b"["))
                self.token_list.append(PdfToken(_token_id, _tokenizer_position + 1, _token_data[1:]))
                _tokenizer_position = _tokenizer_position + len(_token_data)
                continue
            # atomize ']'
            if _token_data.find(b"]") != -1 and _token_data != b"]":
                self.token_list.append(PdfToken(_token_id, _tokenizer_position, _token_data[:-1]))
                self.token_list.append(PdfToken(_token_id, _tokenizer_position + len(_token_data) - 1, b"]"))
                _tokenizer_position = _tokenizer_position + len(_token_data)
                continue
            # special treatment for ? TODO
            if _token_data.startswith(b"{"):
                #print(f"{_token_data}")
                pass
            # special treatment for strings (hex)
            if _token_data.startswith(b"<") and _token_data != b"<<":
                _hex_string_end = self.pdf_data.find(b">", _tokenizer_position) + 1
                _token_data = self.pdf_data[_tokenizer_position:_hex_string_end]
                _token_data = re.sub(WHITESPACE_PATTERN, b"", _token_data)
                self.token_list.append(PdfToken(_token_id, _tokenizer_position, _token_data))
                _tokenizer_position = _hex_string_end
                continue
            # special treatment for streams
            if _token_data == b"stream":
                _stream_start = self.find_next_token(_token_end)
                _stream_end = self.pdf_data.find(b"\x0aendstream", _stream_start)

                self.token_list.append(PdfToken(_token_id, _stream_start, self.pdf_data[_tokenizer_position:_token_end]))
                self.token_list.append(PdfToken(_token_id, _stream_start, self.pdf_data[_stream_start:_stream_end].rstrip()))
                self.token_list.append(PdfToken(_token_id, _stream_end, self.pdf_data[_stream_end + 1:_stream_end + 10]))
                _tokenizer_position = _stream_end + 10
                continue
            # special treatment for comments
            _comment = _token_data.find(b"\x25", 0)
            if _comment != -1:
                if _comment > 0: # if token prior '%'
                    self.token_list.append(PdfToken(_token_id, _tokenizer_position, self.pdf_data[_tokenizer_position:_tokenizer_position+_comment]))
                _line_end = self.pdf_data.find(b"\x0a", _tokenizer_position+_comment)
                _token_data = self.pdf_data[_tokenizer_position+_comment:_line_end].rstrip()
                self.token_list.append(PdfToken(_token_id, _tokenizer_position+_comment, _token_data))
                _tokenizer_position = _line_end
                continue

            # default token processing
            self.token_list.append(PdfToken(_token_id, _tokenizer_position, _token_data))
            _tokenizer_position = _tokenizer_position + len(_token_data)
    def get_token_list(self) -> list[PdfToken]:
        return self.token_list

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# TODO: accumulate lengths of objects in tokens!

class AbstractObject(abc.ABC):
    def __init__(self, pdf_tokens: list[PdfToken], token_index_offset: int) -> None:
        self.pdf_tokens: list[PdfToken] = pdf_tokens
        self.token_index_offset: int = token_index_offset

        offset_token = self.pdf_tokens[self.token_index_offset]
        self.object_dict = {
            "position": offset_token.position,
            "type": str(offset_token.type).split(".")[1].lower(),
            "data": None
        }
        self.object_length = 1
    def get_dict(self) -> dict:
        return self.object_dict
    def get_length(self) -> int:
        return self.object_length
class NameObject(AbstractObject):
    def __init__(self, pt: list[PdfToken], tio: int) -> None:
        super().__init__(pt, tio)
        self.object_dict["data"] = str(self.pdf_tokens[self.token_index_offset].raw, "utf-8")
class NumericObject(AbstractObject):
    def __init__(self, pt: list[PdfToken], tio: int) -> None:
        super().__init__(pt, tio)

        can_lookahead: bool = self.token_index_offset + 3 < len(self.pdf_tokens)

        if can_lookahead:
            current_token_0: PdfToken = self.pdf_tokens[self.token_index_offset]
            future_token_1: PdfToken = self.pdf_tokens[self.token_index_offset + 1]
            future_token_2: PdfToken = self.pdf_tokens[self.token_index_offset + 2]
            future_token_3: PdfToken = self.pdf_tokens[self.token_index_offset + 3]
            
            # case 1: indirect object (n m obj)
            if future_token_1.type == PdfTokenType.NUMERIC and future_token_2.type == PdfTokenType.INDIRECT_OBJECT:
                self.object_length = 4 # n m obj endobj

                object_number: int = int(str(current_token_0.raw, "utf-8"))
                generation_number: int = int(str(future_token_1.raw, "utf-8"))

                self.object_dict["type"] = str(future_token_2.type).split(".")[1].lower()
                self.object_dict["object_number"] = object_number
                self.object_dict["generation_number"] = generation_number

                match future_token_3.type:
                    case PdfTokenType.DICTIONARY:
                        obj = DictionaryObject(self.pdf_tokens, self.token_index_offset + 3)
                        self.object_length = self.object_length + obj.get_length()
                        self.object_dict["data"] = obj.get_dict()
                    case _:
                        self.object_dict["data"] = str(future_token_3.type)
                return

            # case 2: reference object (n m R)
            if future_token_1.type == PdfTokenType.NUMERIC and future_token_2.raw == b"R":
                self.object_length = 3

                object_number: int = int(str(current_token_0.raw, "utf-8"))
                generation_number: int = int(str(future_token_1.raw, "utf-8"))

                self.object_dict["type"] = "reference"
                del self.object_dict["data"]

                self.object_dict["object_number"] = object_number
                self.object_dict["generation_number"] = generation_number

                return

        # case 3: actual numerical value
        self.object_dict["data"] = int(str(self.pdf_tokens[self.token_index_offset].raw, "utf-8"))
class DictionaryObject(AbstractObject):
    def __init__(self, pt: list[PdfToken], tio: int) -> None:
        super().__init__(pt, tio)

        self.object_length = 2

        dictionary_object = {}

        current_token_index = self.token_index_offset + 1
        while self.pdf_tokens[current_token_index].type == PdfTokenType.NAME:
            dictionary_key: str = str(self.pdf_tokens[current_token_index].raw, "utf-8")
            current_token_index = current_token_index + 1
            dictionary_value = self.pdf_tokens[current_token_index]
            if not dictionary_key in dictionary_object:
                self.object_length = self.object_length + 1
                match dictionary_value.type:
                    case PdfTokenType.NAME:
                        obj = NameObject(self.pdf_tokens, current_token_index)
                        current_token_index = current_token_index + obj.get_length()
                        self.object_length = self.object_length + obj.get_length()
                        dictionary_object[dictionary_key] = obj.get_dict()
                    case PdfTokenType.NUMERIC:
                        obj = NumericObject(self.pdf_tokens, current_token_index)
                        current_token_index = current_token_index + obj.get_length()
                        self.object_length = self.object_length + obj.get_length()
                        dictionary_object[dictionary_key] = obj.get_dict()
                    case _:
                        dictionary_object[dictionary_key] = str(dictionary_value.type)

        self.object_dict["data"] = dictionary_object

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class PdfParser():
    def __init__(self, pdf_tokens: list[PdfToken]) -> None:
        self.pdf_tokens: list[PdfToken] = pdf_tokens
        self.file_structure: dict = {
            "header": None,
            "body": [],
            "comments": [],
            "whitespaces": None
        }
    def parse_header(self) -> int:
        i = 0
        while i < len(self.pdf_tokens):
            token: PdfToken = self.pdf_tokens[i]
            if token.type == PdfTokenType._HEADER:
                self.file_structure["header"] = {
                    "position": token.position,
                    "length": token.length,
                    "raw": str(token.raw, "utf-8"),
                    "pdf_version": float(str(token.raw, "utf-8")[5:8])
                }
                return i + 1
            i = i + 1
        return -1
    def parse_body(self, token_index_offset: int):
        i = token_index_offset
        _debug_abort = 10000
        while i < len(self.pdf_tokens):
            _debug_abort = _debug_abort - 1
            if _debug_abort == 0:
                break
            token: PdfToken = self.pdf_tokens[i]

            match token.type:
                case PdfTokenType.NUMERIC:
                    obj = NumericObject(self.pdf_tokens, i)
                    self.file_structure["body"].append(obj.get_dict())
                    i = i + obj.get_length()
                case PdfTokenType._XREF:
                    return i + 1 #TODO i has to be updated!
                case _:
                    self.file_structure["body"].append(str(token.type))
                    i = i + 1
        return -1

    def process(self) -> None:
        # copy comment tokens
        self.file_structure["comments"] = [{
            "position": c.position,
            "length": c.length,
            "data": str(c.raw)
        } for c in self.pdf_tokens if c.type == PdfTokenType._COMMENT]
        
        # remove comment tokens
        self.pdf_tokens = [t for t in self.pdf_tokens if t.type != PdfTokenType._COMMENT]

        # TODO: remove later!
        self.file_structure["debug_tokens"] = [{
            "token_id": t.token_id,
            "position": t.position,
            "length": t.length,
            "type": str(t.type).split(".")[1].lower(),
            "data": str(t.raw)
        } for t in self.pdf_tokens]

        tokens_processed: int = self.parse_header()
        tokens_processed: int = self.parse_body(tokens_processed)
        #trailer_index = self.parse_cross_ref_table(xref_index + 1)
        #eof_index = self.parse_trailer(trailer_index + 1)
        # TODO: call methods above!
    def get_file_structure(self) -> dict:
        return self.file_structure

class ApplicationPdfFormat():
    @staticmethod
    def format_specific_parsing(cf, md: dict, pd: bytes, pl: int, op: int) -> dict:
        pdf_tokenizer = PdfTokenizer(pd)
        pdf_tokenizer.tokenize()

        pdf_parser = PdfParser(pdf_tokenizer.get_token_list())
        pdf_parser.process()

        # TODO: determine coverage and save white spaces

        # TODO: process token list
        #   as in figure 1 'PDF file components'
        #       objects
        #       file structure
        #       document structure
        #       content streams
        #   as in figure 2 'Initial structure of a PDF file'
        #       header
        #       n bodies
        #       n cross-ref tables
        #       n trailers

        ########################################
        # TODO: validate header (was mit EOF?)
        # TODO: remove and log comments
        # TODO: read data to last %%EOF appearence, if data left, init rec parsing

        md["structured"] = pdf_parser.get_file_structure()
        return md
