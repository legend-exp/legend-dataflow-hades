import os, pathlib

import pygama
from pygama.io.fcdaq import * 

import numpy as np

pathlib.Path(os.path.dirname(snakemake.output[0])).mkdir(parents=True, exist_ok=True)

# ToDo: Atomic file creation

process_flashcam(snakemake.input[0], snakemake.output[0], np.inf)
