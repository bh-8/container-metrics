import mimetypes
import magic
from pathlib import Path

class MIMETypeDetector:
    @staticmethod
    def by_filename(path: Path) -> str | None:
        return mimetypes.guess_type(path, False)[0]

    @staticmethod
    def by_content(path: Path) -> str | None:
        return magic.from_file(path, mime=True)
