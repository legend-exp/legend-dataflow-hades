import os, pathlib

import pygama
from pygama.io.raw_to_dsp import raw_to_dsp 

import json
from collections import OrderedDict 

from utils import *

metadata = metadata_path(snakemake.params.setup)
f_config = f"{metadata}/config_dsp.json"

with open(f_config) as f:
    config_dic = json.load(f, object_pairs_hook=OrderedDict) 

pathlib.Path(os.path.dirname(snakemake.output[0])).mkdir(parents=True, exist_ok=True)

# ToDo: Atomic file creation

raw_to_dsp(snakemake.input[0], snakemake.output[0], config_dic, n_max=snakemake.params.n_max, verbose=True, overwrite=False) 
