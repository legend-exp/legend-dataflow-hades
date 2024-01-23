import argparse, os, pathlib

import pygama
from pygama.io.build_hit import build_hit

import json

argparser = argparse.ArgumentParser()
argparser.add_argument("input", help="input file", type=str)
argparser.add_argument("--ecal_file", help="energy calibration file for detector", type=str)
argparser.add_argument("--aoe_cal_file", help="a/e calibration file for detector", type=str)
argparser.add_argument("--metadata", help="metadata path", type=str, required=True)
argparser.add_argument("--detector", help="detector", type=str, required=True)
argparser.add_argument("output", help="output file", type=str)
args = argparser.parse_args()

main_config = os.path.join(f"{args.metadata}", "main_config.json")

with open(main_config, 'r') as f:
    config_dict = json.load(f)

det_config=config_dict[args.detector]

cut_parameters = det_config["default_cut_parameters"]


with open(args.ecal_file) as f:
    ecal_dict = json.load(f)


with open(args.aoe_cal_file) as f:
    aoe_dict = json.load(f)

db_dict ={}
db_dict['ecal_pars'] = ecal_dict["cuspEmax_ctc"]["Calibration_pars"]
db_dict['aoe_cut_low']=aoe_dict["Low_cut"]
db_dict['aoe_cut_high']=aoe_dict["High_cut"]
db_dict['aoe_mu_pars']=aoe_dict["Mean_pars"]
db_dict['aoe_sigma_pars']=aoe_dict["Sigma_pars"]

builder_config = {      
        'energy_param' : 'cuspEmax_ctc', 
        'current_param' : "A_max", 
        'aoe_energy_param' : "cuspEmax",  
        "cut_parameters":cut_parameters,
        'copy_cols':None
        }

pathlib.Path(os.path.dirname(args.output)).mkdir(parents=True, exist_ok=True)

build_hit(args.input, db_dict, f_hit =args.output, overwrite=False)
