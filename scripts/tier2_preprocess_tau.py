import argparse, os, pathlib

import pygama
import pygama.pargen.get_decay_const as dpp

import json
from collections import OrderedDict 

argparser = argparse.ArgumentParser()
argparser.add_argument("--metadata", help="metadata path", type=str, required=True)
argparser.add_argument("--plot_path", help="plot path", type=str, required=False)
argparser.add_argument("input", help="input file", type=str)
argparser.add_argument("output", help="output file", type=str)
args = argparser.parse_args()

f_config = os.path.join(f"{args.metadata}", "initial_config_dsp.json")

with open(f_config) as f:
    config_dic = json.load(f, object_pairs_hook=OrderedDict) 

input_file = args.input

if input_file.split('.')[-1] == 'filelist':
    with open(input_file) as f:
        input_file = f.read().splitlines()[0]

print(input_file) 
pathlib.Path(os.path.dirname(args.output)).mkdir(parents=True, exist_ok=True)
if args.plot_path:
    dpp.dsp_preprocess_decay_const(input_file, config_dic, database_file=args.output, plot_path=args.plot_path, verbose=True, overwrite=False) 
else:
    dpp.dsp_preprocess_decay_const(input_file, config_dic, database_file=args.output, verbose=True, overwrite=False) 
