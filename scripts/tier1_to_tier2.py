import argparse, os, pathlib

import pygama
from pygama.io.raw_to_dsp import raw_to_dsp 

import json
from collections import OrderedDict 

argparser = argparse.ArgumentParser()
argparser.add_argument("--metadata", help="metadata path", type=str, required=True)
argparser.add_argument("input", help="input file", type=str)
argparser.add_argument("output", help="output file", type=str)
args = argparser.parse_args()

f_config = os.path.join(f"{args.metadata}", "config_dsp.json")

with open(f_config) as f:
    config_dic = json.load(f, object_pairs_hook=OrderedDict) 

pathlib.Path(os.path.dirname(args.output)).mkdir(parents=True, exist_ok=True)

# ToDo: Atomic file creation

raw_to_dsp(args.input, args.output, config_dic, verbose=True, overwrite=False) 
