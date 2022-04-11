import argparse, os, pathlib

import pygama
import pygama.pargen.get_decay_const as dpp

import json
from collections import OrderedDict 

argparser = argparse.ArgumentParser()
argparser.add_argument("--metadata", help="metadata path", type=str, required=True)
argparser.add_argument("--detector", help="detector", type=str, required=True)
argparser.add_argument("--plot_path", help="plot path", type=str, required=False)

argparser.add_argument("input", help="input file", type=str)
argparser.add_argument("output", help="output file", type=str)
args = argparser.parse_args()

main_config = os.path.join(f"{args.metadata}", "main_config.json")

default_dict = {"initial_dsp_config":"initial_config_dsp.json", "main_dsp_config":"main_dsp_config.json",
                "energy_config":"opt_config.json","energy_ftp_config":"opt_config_ftp.json",
               "default_cut_parameters": {"bl_mean":4, "bl_std":4, "pz_std":4}}

with open(main_config, 'r') as f:
    config_dict = json.load(f)

try:
    det_config=config_dict[args.detector]
except:
    config_dict[args.detector] = default_dict
    det_config = default_dict
    with open(main_config, 'w') as f:
        json.dump(config_dict, f, indent=4)

f_config = os.path.join(f"{args.metadata}", det_config["initial_dsp_config"])

with open(f_config) as f:
    config_dic = json.load(f, object_pairs_hook=OrderedDict) 

input_file = args.input

if input_file.split('.')[-1] == 'filelist':
    with open(input_file) as f:
        input_file = f.read().splitlines()[0]

pathlib.Path(os.path.dirname(args.output)).mkdir(parents=True, exist_ok=True)
if args.plot_path:
    dpp.dsp_preprocess_decay_const(input_file, config_dic, database_file=args.output, plot_path=args.plot_path, verbose=True, overwrite=False) 
else:
    dpp.dsp_preprocess_decay_const(input_file, config_dic, database_file=args.output, verbose=True, overwrite=False) 
