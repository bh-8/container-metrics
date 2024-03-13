from mime_type_detection import MIMETypeDetector
from pathlib import Path
from typing import Callable

class MetricExtractor:
    def __init__(self, input: Path, output: Path) -> None:
        self.input_path = input
        self.output_path = output
        self.mime_type = None

    def determine_mime_type(self, detect_mime_type: Callable[[Path], str | None]):
        self.mime_type = detect_mime_type(self.input_path)
        if self.mime_type is None:
            raise RuntimeError(f"could not determine mime type of file '{self.input_path}'")
        else:
            # [TODO]: read available mime types dynamically
            if self.mime_type != "image/jpeg":
                raise NotImplementedError(f"mime type '{self.mime_type}' is not supported")

    @staticmethod
    def extract(args):
        print(f"{args}")

        metricExtractor = MetricExtractor(
            Path(args.input.name).resolve(),
            Path(args.output.name).resolve()
        )

        metricExtractor.determine_mime_type(
            MIMETypeDetector.by_content if args.magic else MIMETypeDetector.by_filename
        )
