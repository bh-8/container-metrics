"""
csv_pipeline.py

references:
    - 

"""

# IMPORTS

from collections import Counter
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

        if not type(query_result) is list:
            return

        if len(query_result) == 0:
            return

        if str(self.pipeline_parameters["diagram"]).lower() == "plot":
            if type(query_result[0]) is list and type(query_result[0][0]) is list:
                # create n diagrams with m plots each
                n: int = len(query_result[0])
                m: int = len(query_result[0][0])

                fig, axs = plt.subplots(n)
                fig.set_figwidth(self.pipeline_parameters["width"])
                fig.set_figheight(self.pipeline_parameters["height"])
                #fig.tight_layout()

                x: list[int] = list(range(len(query_result)))
                for j in range(n):
                    for i in range(m):
                        y: list = [q[j][i] if j < len(q) and i < len(q[j]) else None for q in query_result]
                        axs[j].plot(x, y)
                    axs[j].set_xlabel(self.pipeline_parameters["x_axis"])
                    axs[j].set_ylabel(self.pipeline_parameters["y_axis"])

                svg_file: Path = self.get_outfile_path(self.pipeline_parameters['outid'])
                plt.savefig(svg_file)
                plt.close()
            elif type(query_result[0]) is list:
                # create 1 diagram with m plots
                n: int = 1
                m: int = len(query_result[0])

                fig, axs = plt.subplots(n)
                fig.set_figwidth(self.pipeline_parameters["width"])
                fig.set_figheight(self.pipeline_parameters["height"])
                #fig.tight_layout()

                x: list[int] = list(range(len(query_result)))
                for i in range(m):
                    y: list = [q[i] if i < len(q) else None for q in query_result]
                    axs.plot(x, y)
                axs.set_xlabel(self.pipeline_parameters["x_axis"])
                axs.set_ylabel(self.pipeline_parameters["y_axis"])

                svg_file: Path = self.get_outfile_path(self.pipeline_parameters['outid'])
                plt.savefig(svg_file)
                plt.close()
            else:
                log.critical(f"could not create svg plot: expected 2-dimensional list")
                return

        elif str(self.pipeline_parameters["diagram"]).lower() == "hist":
            if type(query_result[0]) is list:
                log.critical(f"could not create svg histogram: expected 1-dimensional list of categorical attributes")
                return

            categories: list = sorted(list(set(query_result)))
            category_amounts: list = [query_result.count(c) for c in categories]

            fig, axs = plt.subplots()
            fig.set_figwidth(self.pipeline_parameters["width"])
            fig.set_figheight(self.pipeline_parameters["height"])

            axs.bar(categories, category_amounts, width=0.8, align="center")
            axs.set_xlabel(self.pipeline_parameters["x_axis"])
            axs.set_ylabel(self.pipeline_parameters["y_axis"])

            svg_file: Path = self.get_outfile_path(self.pipeline_parameters['outid'])
            plt.savefig(svg_file)
            plt.close()

        return
