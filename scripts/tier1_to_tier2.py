
import argparse, os, pathlib

import pygama
from pygama.io.raw_to_dsp import raw_to_dsp

import json
from collections import OrderedDict

argparser = argparse.ArgumentParser()
argparser.add_argument("--metadata", help="metadata path", type=str, required=True)
#argparser.add_argument("--measurement", help="Measurement", type=str, required=True)
argparser.add_argument("input", help="input file", type=str)
argparser.add_argument("--database", help="database file for detector", type=str)
argparser.add_argument("output", help="output file", type=str)
args = argparser.parse_args()

main_config = os.path.join(f"{args.metadata}", "main_config.json")

with open(main_config, 'r') as f:
    config_dict = json.load(f)

det_config=config_dict[args.detector]

f_config = os.path.join(f"{args.metadata}", det_config["main_dsp_config"])

with open(f_config) as f:
    config_dic = json.load(f, object_pairs_hook=OrderedDict)


with open(args.database) as f:
    database_dic = json.load(f, object_pairs_hook=OrderedDict)

pathlib.Path(os.path.dirname(args.output)).mkdir(parents=True, exist_ok=True)

raw_to_dsp(args.input, args.output, config_dic, database = database_dic, verbose=True, overwrite=False)
