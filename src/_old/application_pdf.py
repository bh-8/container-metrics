from static_utils import StaticLogger
import abc
import re

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Static Objects

logger = None
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

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tokens

class PdfToken():
    def try_utf8_conv(self, raw: bytes) -> str | bytes:
        try:
            return str(raw, "utf-8")
        except:
            return raw
    def __init__(self, position: int, raw: bytes, is_stream: bool = False) -> None:
        self.position: int = position
        self.length: int = len(raw)
        self.type: str | None = "stream" if is_stream else None
        self.raw: bytes = raw
        self.data = self.try_utf8_conv(self.raw)

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
        self.pdf_data: bytes = pdf_data
        self.token_list: list[PdfToken] = []

    # searches for the next whitespace occurance
    def read_token(self, position: int) -> int:
        match = WHITESPACE_PATTERN.search(self.pdf_data, position)
        if match is None:
            return -1
        else:
            return match.start()

    # search for the next non-whitespace character
    def jump_to_next_token(self, position: int) -> int:
        match = WHITESPACE_ANTI_PATTERN.search(self.pdf_data, position)
        if match is None:
            return -1
        else:
            return match.start()

    # process raw data
    def tokenize(self) -> None:
        # output collector
        self.token_list: list[PdfToken] = []

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
            token: bytes = self.pdf_data[pos:pos_end]

            # header
            if token.startswith(b"\x25PDF-") and len(token) >= 8:
                self.token_list.append(PdfToken(pos, token[:8]))   
                pos = pos + 8
                continue

            # stream
            if token == b"stream":
                self.token_list.append(PdfToken(pos, token))

                _stream_start = self.jump_to_next_token(pos_end)
                _stream_end = self.pdf_data.find(b"endstream", _stream_start)

                self.token_list.append(PdfToken(_stream_start, self.pdf_data[_stream_start:_stream_end].rstrip(), True))
                self.token_list.append(PdfToken(_stream_end, self.pdf_data[_stream_end:_stream_end + 9]))
                pos = _stream_end + 9

                continue

            # special treatment for '('
            if token.startswith(DELIMITER_CHARACTERS[0]):
                _parenthesis_position = pos + 1
                _parenthesis_open = 1
                while _parenthesis_open > 0:
                    _next_parenthesis_open = self.pdf_data.find(DELIMITER_CHARACTERS[0], _parenthesis_position)
                    _next_parenthesis_close = self.pdf_data.find(DELIMITER_CHARACTERS[1], _parenthesis_position)

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
                token = self.pdf_data[pos:_parenthesis_position]
                self.token_list.append(PdfToken(pos, token))
                pos = _parenthesis_position
                continue

            # special treatment for '<'
            if token.startswith(DELIMITER_CHARACTERS[2]):
                if token.startswith(b"<<"):
                    token = self.pdf_data[pos:pos + 2]
                    self.token_list.append(PdfToken(pos, token))
                    pos = pos + 2
                else:
                    _hex_string_end = self.pdf_data.find(DELIMITER_CHARACTERS[3], pos) + 1
                    token = self.pdf_data[pos:_hex_string_end]
                    self.token_list.append(PdfToken(pos, token))
                    pos = _hex_string_end
                continue

            # special treatment for '['
            if token.startswith(DELIMITER_CHARACTERS[4]):
                token = self.pdf_data[pos:pos + 1]
                self.token_list.append(PdfToken(pos, token))
                pos = pos + 1
                continue

            # special treatment for '{'
            if token.startswith(DELIMITER_CHARACTERS[6]):
                logger.warn("application_pdf.py: missing implementation to handle '\{'")
                # TODO: implement this ...

            # special treatment for ']'
            check_pos = token.find(b"]")
            if check_pos != -1:
                if check_pos > 0:
                    self.token_list.append(PdfToken(pos, token[:check_pos]))
                self.token_list.append(PdfToken(pos + check_pos, token[check_pos:check_pos + 1]))
                pos = pos + check_pos + 1
                continue

            # special treatment for '/'
            if token.startswith(DELIMITER_CHARACTERS[8]):
                check_pos = token.find(b"/", 1)
                if check_pos == -1:
                    self.token_list.append(PdfToken(pos, token))
                    pos = pos + len(token)
                else:
                    self.token_list.append(PdfToken(pos, token[:check_pos]))
                    pos = pos + check_pos
                continue

            # special treatment for '>>'
            check_pos = token.find(b">>")
            if check_pos != -1:
                if check_pos > 0:
                    self.token_list.append(PdfToken(pos, token[:check_pos]))
                self.token_list.append(PdfToken(pos + check_pos, token[check_pos:check_pos + 2]))
                pos = pos + check_pos + 2
                continue

            # special treatment for '%'
            check_pos = token.find(b"%")
            if check_pos != -1:
                if check_pos > 0:
                    self.token_list.append(PdfToken(pos, token[:check_pos]))

                _line_end = self.pdf_data.find(b"\x0a", pos + check_pos)
                token = self.pdf_data[pos + check_pos:_line_end].rstrip()

                self.token_list.append(PdfToken(pos + check_pos, token))
                pos = _line_end
                continue

            # default token processing
            self.token_list.append(PdfToken(pos, token))
            pos = pos + len(token)

    # results
    def get_token_list(self) -> list[PdfToken]:
        return self.token_list

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Objects

class AbstractObject(abc.ABC):
    def __init__(self, pdf_tokens: list[PdfToken], index: int) -> None:
        self.pdf_tokens: list[PdfToken] = pdf_tokens
        self.index: int = index

        # by default, an object is constructed by one (or more) tokens
        self.object_length: int = 1

        # initialize object stats from first token
        token: PdfToken = self.pdf_tokens[self.index]
        self.container_item: ContainerItem = ContainerItem(token.position, token.length)
        self.container_item.set_attribute("type", token.type)

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
    def get_dict(self) -> dict:
        return self.container_item.get_dict()
class ArbitraryObject(AbstractObject):
    def __init__(self, pt: list[PdfToken], n: int) -> None:
        super().__init__(pt, n)
        self.container_item.set_attribute("data", self.pdf_tokens[self.index].data)
class NumericObject(AbstractObject): # <<<>>>
    def __init__(self, pt: list[PdfToken], n: int) -> None:
        super().__init__(pt, n)

        # check whether enough tokens are available
        if self.index + 4 < len(self.pdf_tokens):
            token_0_current: PdfToken = self.pdf_tokens[self.index]
            token_1_future: PdfToken = self.pdf_tokens[self.index + 1]
            token_2_future: PdfToken = self.pdf_tokens[self.index + 2]
            token_3_future: PdfToken = self.pdf_tokens[self.index + 3]

            self.container_item.set_attribute("len", None)

            # case 1: indirect object (n m obj) (endobj)
            if token_1_future.type == "numeric" and token_2_future.type == "indirect_obj":
                # indirect object frame requires 4 tokens: n m obj endobj
                self.object_length = 4

                # as indirect objects are modeled as numeric objects, the type has to be set manually
                
                self.container_item.set_attribute("type", token_2_future.type)

                # gather numbers
                self.container_item.set_attribute("object_number", token_0_current.data)
                self.container_item.set_attribute("generation_number", token_1_future.data)

                # handle all types which can be encapsulated in an indirect object
                i: int = self.index + 3
                obj = self.determine_object(token_3_future, i)
                if obj is None:
                    logger.critical(f"application_pdf.py: 'IndirectObject' is missing implementation to handle '{token_3_future.type}' (token #{i})")
                    return

                # add token length during recursion
                self.object_length = self.object_length + obj.get_length()

                # set (nested) data
                self.container_item.set_attribute("data", obj.get_dict())

                return
            # case 2: reference object (n m R)
            if token_1_future.type == "numeric" and token_2_future.raw == b"R":
                # reference object requires 3 tokens: n m R
                self.object_length = 3

                # as reference objects are modeled as numeric objects, the type has to be set manually
                self.container_item.set_attribute("type", "reference")

                # gather numbers
                self.container_item.set_attribute("object_number", token_0_current.data)
                self.container_item.set_attribute("generation_number", token_1_future.data)

                return
        # case 3: actual numerical value
        self.container_item.set_attribute("data", self.pdf_tokens[self.index].data)
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
                logger.critical(f"application_pdf.py: 'DictionaryObject' is missing implementation to handle '{dictionary_value.type}' (token #{i})")
                continue

            # skip processed tokens
            i = i + obj.get_length()

            # add tokens
            self.object_length = self.object_length + obj.get_length()

            # add dictionary key
            nested_dict[dictionary_key] = obj.get_dict()

        # if segments available
        if i + 3 < len(self.pdf_tokens):
            token_stream_start: PdfToken = self.pdf_tokens[i + 1]
            token_stream: PdfToken = self.pdf_tokens[i + 2]

            # check for stream element
            if token_stream_start.type == "stream":
                # add tokens
                self.object_length = self.object_length + 3

                # append stream element
                stream_item: ContainerItem = ContainerItem(token_stream.position, token_stream.length)
                stream_item.set_attribute("type", token_stream.type)
                nested_dict["stream"] = stream_item.get_dict()

        self.container_item.set_attribute("len", None)
        self.container_item.set_attribute("data", nested_dict)
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
                logger.critical(f"application_pdf.py: 'ArrayObject' is missing implementation to handle '{token.type}' (token #{i})")
                i = i + 1
                continue

            # skip processed tokens
            i = i + obj.get_length()

            # add tokens
            self.object_length = self.object_length + obj.get_length()

            # add dictionary key
            nested_list.append(obj.get_dict())

        self.container_item.set_attribute("data", nested_list)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Analysis

# TODO: UNITE FOLLOWING CLASSES AS SPECIALIZATION CLASS
"""
class PdfParser():
    def __init__(self, pdf_tokens: list[PdfToken]) -> None:
        self.pdf_tokens: list[PdfToken] = pdf_tokens

        # construct file structure of segments, segments consists of (nested) items
        self.file_structure: dict = {
            "header": None,
            "body": [],
            "xref": [],
            "trailer": [],
            "startxref": [],
            "comments": [],
            "whitespaces": None
        }

    # returns index of the first token which does not belong to the header
    def parse_header(self) -> int:
        i = 0
        while i < len(self.pdf_tokens):
            token: PdfToken = self.pdf_tokens[i]
            if token.type == "_header":
                header_item: ContainerItem = ContainerItem(token.position, token.length)
                header_item.set_attribute("version", float(str(token.raw, "utf-8")[5:8]))
                self.file_structure["header"] = header_item.get_dict()
                return i + 1
            i = i + 1
        return -1

    # returns index of the first token which does not belong to the body
    def parse_body(self, index: int) -> int:
        i: int = index
        while i < len(self.pdf_tokens):
            token: PdfToken = self.pdf_tokens[i]
            match token.type:
                case "numeric":
                    obj = NumericObject(self.pdf_tokens, i)
                    self.file_structure["body"].append(obj.get_dict())
                    i = i + obj.get_length()
                case "_xref" | "_trailer" | "_startxref":
                    return i
                case _:
                    return -1
        return -1

    # returns index of the first token which does not belong to cross-ref-table
    def parse_xref(self, index: int) -> int:
        i: int = index + 1
        while i < len(self.pdf_tokens):
            token: PdfToken = self.pdf_tokens[i]

            match token.type:
                case "numeric":
                    #ref_tab: ContainerItem = ContainerItem(token.position, 0)
                    #ref_tab.set_attribute("len", None)
                    #ref_tab.set_attribute("type", "cross_ref_table")
                    range_offset: int = self.pdf_tokens[i].data
                    cross_ref_entries: int = self.pdf_tokens[i + 1].data

                    i = i + 2
                    c: int = 0
                    #ref_tab_list: list = []
                    while c < cross_ref_entries and i + 3 < len(self.pdf_tokens):
                        ref_tab_entry: ContainerItem = ContainerItem(self.pdf_tokens[i].position, 0)
                        ref_tab_entry.set_attribute("len", None)
                        ref_tab_entry.set_attribute("object_number", range_offset + c)
                        ref_tab_entry.set_attribute("byte_offset", self.pdf_tokens[i].data)
                        ref_tab_entry.set_attribute("generation_number", self.pdf_tokens[i + 1].data)
                        ref_tab_entry.set_attribute("in_use", self.pdf_tokens[i + 2].raw == b"n")
                        #ref_tab_list.append(ref_tab_entry.get_dict())
                        self.file_structure["xref"].append(ref_tab_entry.get_dict())
                        i = i + 3
                        c = c + 1

                    #ref_tab.set_attribute("entries", ref_tab_list)
                    #self.file_structure["xref"].append(ref_tab.get_dict())
                case "_trailer" | "_startxref":
                    return i
                case _:
                    self.file_structure["xref"].append(None)
                    logger.critical(f"application_pdf.py: 'XRefParser' is missing implementation to handle '{token.type}' (token #{i})")
                    i = i + 1
        return -1

    # returns index of the first token which does not belong to trailer
    def parse_trailer(self, index: int) -> int:
        i: int = index + 1
        while i < len(self.pdf_tokens):
            token: PdfToken = self.pdf_tokens[i]

            match token.type:
                case "dictionary":
                    obj = DictionaryObject(self.pdf_tokens, i)
                    self.file_structure["trailer"].append(obj.get_dict())
                    i = i + obj.get_length()
                case "_startxref":
                    return i
                case _:
                    logger.critical(f"application_pdf.py: 'TrailerParser' is missing implementation to handle '{token.type}' (token #{i})")
                    i = i + 1
        return -1

    # parsing process
    def process(self, cf, pl: int, op: int, md: dict) -> None:
        # store comment tokens
        self.file_structure["comments"] = [ContainerItem(c.position, c.length).get_dict() for c in self.pdf_tokens if c.type == "_comment"]

        # remove comment tokens before parsing
        self.pdf_tokens = [t for t in self.pdf_tokens if t.type != "_comment"]

        tokens_processed: int = self.parse_header()

        while tokens_processed < len(self.pdf_tokens):
            _tmp_n: int = tokens_processed
            tokens_processed: int = self.parse_body(tokens_processed)

            if tokens_processed == -1:
                # TODO: code quality is bad
                cf.parse(pl, op + self.pdf_tokens[_tmp_n].position)
                md["len"] = self.pdf_tokens[_tmp_n].position
                break

            # cross-ref
            if self.pdf_tokens[tokens_processed].type == "_xref":
                tokens_processed: int = self.parse_xref(tokens_processed)

            # trailer
            if self.pdf_tokens[tokens_processed].type == "_trailer":
                tokens_processed: int = self.parse_trailer(tokens_processed)

            # entry point and eof
            if self.pdf_tokens[tokens_processed].type == "_startxref":
                numeric_token: PdfToken = self.pdf_tokens[tokens_processed + 1]
                numeric_item: ContainerItem = ContainerItem(numeric_token.position, numeric_token.length)
                numeric_item.set_attribute("len", None)
                numeric_item.set_attribute("ref", numeric_token.data)
                self.file_structure["startxref"].append(numeric_item.get_dict())
                tokens_processed = tokens_processed + 2
            
            if self.pdf_tokens[tokens_processed].type == "_eof":
                tokens_processed = tokens_processed + 1

    def set_whitespaces(self, uncovered_list: list[dict]) -> None:
        self.file_structure["whitespaces"] = uncovered_list

    def get_file_structure(self) -> dict:
        return self.file_structure

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Entrypoint

class ApplicationPdfFormat():
    @staticmethod
    def format_specific_parsing(cf, md: dict, pd: bytes, pl: int, op: int) -> dict:
        global logger
        logger = StaticLogger.get_logger()

        pdf_tokenizer = PdfTokenizer(pd)
        pdf_tokenizer.tokenize()


        pdf_parser = PdfParser(pdf_tokenizer.get_token_list())
        pdf_parser.process(cf, pl, op, md)

        # TODO: check whether this works for eof-appended files
        coverage: Coverage = Coverage([{"pos": t.position, "len": t.length} for t in pdf_tokenizer.get_token_list()], md["len"]) 

        pdf_parser.set_whitespaces(coverage.uncovered_positions())

        # TODO: determine coverage and save white spaces by tokens

        md["structured"] = pdf_parser.get_file_structure()
        return md
"""