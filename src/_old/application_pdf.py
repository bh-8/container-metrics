
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Objects

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Analysis

# TODO: UNITE FOLLOWING CLASSES AS SPECIALIZATION CLASS

class PdfParser():
    def __init__(self, pdf_tokens: list[PdfToken]) -> None:
        self.pdf_tokens: list[PdfToken] = pdf_tokens

        # construct file structure of segments, segments consists of (nested) items
        self.file_structure: dict = {
            "xref": [],
            "trailer": [],
            "startxref": [],
            "comments": [],
            "whitespaces": None
        }

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

        


        pdf_parser = PdfParser(pdf_tokenizer.get_token_list())
        pdf_parser.process(cf, pl, op, md)

        # TODO: check whether this works for eof-appended files
        coverage: Coverage = Coverage([{"pos": t.position, "len": t.length} for t in pdf_tokenizer.get_token_list()], md["len"]) 

        pdf_parser.set_whitespaces(coverage.uncovered_positions())

        # TODO: determine coverage and save white spaces by tokens

        md["structured"] = pdf_parser.get_file_structure()
        return md
