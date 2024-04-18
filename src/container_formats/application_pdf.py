import re

WHITESPACE_CHARACTERS: list[bytes] = [b"\x00", b"\x09", b"\x0a", b"\x0c", b"\x0d", b"\x20"]
DELIMITER_CHARACTERS: list[bytes] = [b"\x28", b"\x29", b"\x3c", b"\x3e", b"\x5b", b"\x5d", b"\x7b", b"\x7d", b"\x2f", b"\x25"]

# % comment
# %PDF-n.m
# %%EOF

class PdfToken():
    def __init__(self, position: int, raw: bytes) -> None:
        self.position = position
        self.raw = raw

class PdfTokenizer():
    def __init__(self, pdf_data: bytes) -> None:
        self.pdf_data: bytes = pdf_data
        self.tokenizer_position: int = 0
        self.token_list: list[PdfToken] = []
    def find_next_whitespace(self) -> int:
        #pattern = re.compile(b"|".join([re.escape(wc) for wc in WHITESPACE_CHARACTERS]))
        pattern = re.compile(b"[" + b"".join([re.escape(wc) for wc in WHITESPACE_CHARACTERS]) + b"]")
        match = pattern.search(self.pdf_data, self.tokenizer_position)
        if match is None:
            return -1
        else:
            return match.start()
    def find_next_token(self) -> int:
        pattern = re.compile(b"[^" + b"".join([re.escape(wc) for wc in WHITESPACE_CHARACTERS]) + b"]")
        match = pattern.search(self.pdf_data, self.tokenizer_position)
        if match is None:
            return -1
        else:
            return match.start()
    def tokenize(self) -> list[PdfToken]:
        while True:
            # TODO: check whether token may be a string '(' / '<'
            # TODO: check whether token is 'stream'
            # search for end of token
            _token_end = self.find_next_whitespace()
            if _token_end == -1:
                break

            # process token
            self.token_list.append(PdfToken(self.tokenizer_position, self.pdf_data[self.tokenizer_position:_token_end]))

            # skip following whitespaces
            self.tokenizer_position = _token_end
            self.tokenizer_position = self.find_next_token()
            if self.tokenizer_position == -1:
                break
        return self.token_list

class ApplicationPdfFormat():
    @staticmethod
    def format_specific_parsing(cf, md: dict, pd: bytes, pl: int, op: int) -> dict:
        # step 1: validate header (was mit EOF?)
        # step 2: remove and log comments
        # step 3: 
        # --> token list required
        
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

        _pdf_tokens =  [{"position": i.position, "raw": str(i.raw)} for i in PdfTokenizer(pd).tokenize()]

        #while True:
            # read first 8 bytes (header)
            #if _parser_pos == 0:
            #    _pdf_file_structure["header"] = str(pd[0:8])
            #    _parser_pos = 8
            #    continue

            #_current_char = pd[_parser_pos:_parser_pos+1]

            # skip character if its whitespace
            #if _current_char in WHITESPACE_CHARACTERS:
            #    _parser_pos = _parser_pos + 1
            #    continue

            # skip line if it starts with '%'
            #if _current_char == b"%":
            #    _line_end = pd.find(b"\x0a", _parser_pos)
            #    if _line_end == -1:
            #        raise AssertionError("expected line end for comment")
            #    _parser_pos = _line_end + 1
            #    continue


            # TODO: implement parsing here




            #_pdf_file_structure["finish_pos_debug"] = _parser_pos
            #break

        md["structured"] = {
            "tokens": _pdf_tokens,
            "objects": _pdf_objects,
            "file_structure": _pdf_file_structure,
            "document_structure": _pdf_document_structure,
            "content_streams": _pdf_content_streams
        }
        return md
