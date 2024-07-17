"""
csv_pipeline.py

references:
    - 

"""

# IMPORTS

import logging
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
log = logging.getLogger(__name__)

from abstract_pipeline import AbstractPipeline

# GLOBAL STATIC MAPPINGS

# MODULE ENTRYPOINT

class SvgPipeline(AbstractPipeline):
    def __init__(self, document: dict, raw: bytes, jmes_query_strings: list[str]) -> None:
        super().__init__("svg", document, raw)
        self.jmes_query_strings: list[str] = jmes_query_strings

    def process(self) -> None:
        for h in range(len(self.jmes_query_strings)):
            query_result: list = self.jmesq(self.jmes_query_strings[h])
            if type(query_result) is list and len(query_result) == 0:
                continue

            n = len(query_result[0])
            fig, axs = plt.subplots(n)
            fig.set_figwidth(16)
            fig.set_figheight(2.4 * n)
            fig.tight_layout()

            x = list(range(len(query_result)))
            for i in range(n):
                y = [s[i] for s in query_result]
                if type(y[0]) is list:
                    for j in range(len(y[0])):
                        z = [t[j] if j < len(t) else None for t in y]
                        axs[i].plot(x, z)
                    continue
                axs[i].plot(x, y)

            svg_file: Path = self.output_path / f"{self.output_id}-{h}.svg"

            plt.savefig(svg_file)
            plt.close()
