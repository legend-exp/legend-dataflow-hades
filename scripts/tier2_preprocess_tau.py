import argparse, os, pathlib

import pygama
import pygama.genpar_tmp.dsp_preprocess as dpp

import json
from collections import OrderedDict 

argparser = argparse.ArgumentParser()
argparser.add_argument("--metadata", help="metadata path", type=str, required=True)
argparser.add_argument("input", help="input file", type=str)
argparser.add_argument("output", help="output file", type=str)
args = argparser.parse_args()

f_config = os.path.join(f"{args.metadata}", "initial_config_dsp.json")

with open(f_config) as f:
    config_dic = json.load(f, object_pairs_hook=OrderedDict) 

with open(args.input) as f:
    files = f.read().splitlines()[0]

pathlib.Path(os.path.dirname(args.output)).mkdir(parents=True, exist_ok=True)
dpp.dsp_preprocess_decay_const(files, config_dic, database_file=args.output,  verbose=True, overwrite=False) 
