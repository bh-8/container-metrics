class ImageJpegFormat():
    @staticmethod
    def format_specific_parsing(cf, pd: bytes, pl: int, op: int) -> dict:
        return {
            "key": f"Hello, World: (pl={pl}, op={op})",
            "raw": str(pd)
        }
