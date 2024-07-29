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
    def __init__(self, document: dict, raw: bytes, pipeline_parameters: dict) -> None:
        super().__init__("svg", document, raw, pipeline_parameters)

    def process(self) -> None:
        query_result: list = self.jmesq(self.pipeline_parameters["jmesq"])
        if type(query_result) is list and len(query_result) == 0:
            return
        if type(query_result[0] is not list):
            query_result = [[i] for i in query_result]

        # TODO: prepare plot with pandas

        n = len(query_result[0])
        fig, axs = plt.subplots(n)
        fig.set_figwidth(16)
        fig.set_figheight(3.2 * n)
        #fig.tight_layout()

        ok: bool = True
        x = list(range(len(query_result)))
        for i in range(n):
            y = [s[i] for s in query_result]
            if type(y[0]) is list:
                for j in range(len(y[0])):
                    z = [t[j] if j < len(t) else None for t in y]
                    try:
                        #axs[i].plot(x, z)
                        #axs[i].set_xlabel(self.pipeline_parameters["x_axis"])
                        #axs[i].set_ylabel(self.pipeline_parameters["y_axis"])
                        axs.plot(x, z)
                        axs.set_xlabel(self.pipeline_parameters["x_axis"])
                        axs.set_ylabel(self.pipeline_parameters["y_axis"])
                    except ValueError:
                        ok = False
                        break
                continue
            #axs[i].plot(x, y)
            axs.plot(x, y)

        svg_file: Path = self.get_outfile_path(self.pipeline_parameters['outid'])

        if ok:
            plt.savefig(svg_file)
        plt.close()
