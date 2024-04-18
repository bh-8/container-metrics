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
            # search for end of token
            _token_end = self.find_next_whitespace()
            if _token_end == -1:
                break

            # process token
            _token_data = self.pdf_data[self.tokenizer_position:_token_end]
            self.token_list.append(PdfToken(self.tokenizer_position, _token_data))

            # special treatment for streams
            if _token_data == b"stream":
                self.tokenizer_position = _token_end
                _stream_start = self.find_next_token()
                _stream_end = self.pdf_data.find(b"\x0aendstream", _stream_start)

                self.token_list.append(PdfToken(_stream_start, self.pdf_data[_stream_start:_stream_end].rstrip()))
                self.token_list.append(PdfToken(_stream_end, self.pdf_data[_stream_end + 1:_stream_end + 10]))
                _token_end = _stream_end + 10

            #TODO: special treatment for comments 
            #TODO: special treatment for strings 

            # skip following whitespaces
            self.tokenizer_position = _token_end
            self.tokenizer_position = self.find_next_token()
            if self.tokenizer_position == -1:
                break
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

        _pdf_tokens =  [{"position": i.position, "raw": str(i.raw), "raw_length": len(i.raw)} for i in PdfTokenizer(pd).tokenize()]

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
