import re

WHITESPACE_CHARACTERS: list[bytes] = [b"\x00", b"\x09", b"\x0a", b"\x0c", b"\x0d", b"\x20"]
DELIMITER_CHARACTERS: list[bytes] = [b"(", b")", b"<", b">", b"[", b"]", b"{", b"}", b"/", b"%"]

WHITESPACE_PATTERN: re.Pattern[bytes] = re.compile(b"[" + b"".join([re.escape(wc) for wc in WHITESPACE_CHARACTERS]) + b"]")
WHITESPACE_ANTI_PATTERN: re.Pattern[bytes] = re.compile(b"[^" + b"".join([re.escape(wc) for wc in WHITESPACE_CHARACTERS]) + b"]")

class PdfToken():
    def __init__(self, position: int, raw: bytes) -> None:
        self.position: int = position
        self.raw: bytes = raw
        self.length: int = len(raw)

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
    def tokenize(self) -> list[PdfToken]:
        _tokenizer_position: int = 0
        _debug = 10000

        while _debug > 0:
            _debug = _debug - 1

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
                self.token_list.append(PdfToken(_tokenizer_position, _token_data))
                _tokenizer_position = _parenthesis_position
                continue
            # atomize '['
            if _token_data.startswith(b"[") and _token_data != b"[":
                self.token_list.append(PdfToken(_tokenizer_position, b"["))
                self.token_list.append(PdfToken(_tokenizer_position + 1, _token_data[1:]))
                _tokenizer_position = _tokenizer_position + len(_token_data)
                continue
            # atomize ']'
            if _token_data.find(b"]") != -1 and _token_data != b"]":
                self.token_list.append(PdfToken(_tokenizer_position, _token_data[:-1]))
                self.token_list.append(PdfToken(_tokenizer_position + len(_token_data) - 1, b"]"))
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
                self.token_list.append(PdfToken(_tokenizer_position, _token_data))
                _tokenizer_position = _hex_string_end
                continue
            # special treatment for streams
            if _token_data == b"stream":
                _stream_start = self.find_next_token(_token_end)
                _stream_end = self.pdf_data.find(b"\x0aendstream", _stream_start)

                self.token_list.append(PdfToken(_stream_start, self.pdf_data[_tokenizer_position:_token_end]))
                self.token_list.append(PdfToken(_stream_start, self.pdf_data[_stream_start:_stream_end].rstrip()))
                self.token_list.append(PdfToken(_stream_end, self.pdf_data[_stream_end + 1:_stream_end + 10]))
                _tokenizer_position = _stream_end + 10
                continue
            # special treatment for comments
            _comment = _token_data.find(b"\x25", 0)
            if _comment != -1:
                if _comment > 0: # if token prior '%'
                    self.token_list.append(PdfToken(_tokenizer_position, self.pdf_data[_tokenizer_position:_tokenizer_position+_comment]))
                _line_end = self.pdf_data.find(b"\x0a", _tokenizer_position+_comment)
                _token_data = self.pdf_data[_tokenizer_position+_comment:_line_end].rstrip()
                self.token_list.append(PdfToken(_tokenizer_position+_comment, _token_data))
                _tokenizer_position = _line_end
                continue

            # default token processing
            self.token_list.append(PdfToken(_tokenizer_position, _token_data))
            _tokenizer_position = _tokenizer_position + len(_token_data)
        return self.token_list

class ApplicationPdfFormat():
    @staticmethod
    def format_specific_parsing(cf, md: dict, pd: bytes, pl: int, op: int) -> dict:
        _pdf_objects = []
        _pdf_file_structure = None#{
            #"header": None,
            #"body": None,
            #"cross_references": None,
            #"trailer": None
        #}
        _pdf_document_structure = []
        _pdf_content_streams = []

        # TODO: read data to last %%EOF appearence, if data left, init rec parsing

        _pdf_tokens =  [{"position": i.position, "raw": str(i.raw), "length": i.length} for i in PdfTokenizer(pd).tokenize()]

        # TODO: extract objects etc.. from tokens

        # TODO: validate header (was mit EOF?)
        # TODO: remove and log comments

        md["structured"] = {
            "tokens": _pdf_tokens,
            "objects": _pdf_objects,
            "file_structure": _pdf_file_structure,
            "document_structure": _pdf_document_structure,
            "content_streams": _pdf_content_streams
        }
        return md
