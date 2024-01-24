import argparse
import logging
import os
import pathlib

os.environ["LGDO_CACHE"] = "false"
os.environ["LGDO_BOUNDSCHECK"] = "false"

import numpy as np
from daq2lh5.build_raw import build_raw
from legendmeta import LegendMetadata
from legendmeta.catalog import Props

argparser = argparse.ArgumentParser()
argparser.add_argument("input", help="input file", type=str)
argparser.add_argument("output", help="output file", type=str)
argparser.add_argument("--detector", help="detector", type=str, required=True)
argparser.add_argument("--timestamp", help="Timestamp", type=str, required=True)
argparser.add_argument("--configs", help="config file", type=str)
argparser.add_argument("--log", help="log file", type=str)
args = argparser.parse_args()

os.makedirs(os.path.dirname(args.log), exist_ok=True)
logging.basicConfig(level=logging.INFO, filename=args.log, filemode="w")

pathlib.Path(os.path.dirname(args.output)).mkdir(parents=True, exist_ok=True)

configs = LegendMetadata(path=args.configs)
channel_dict = configs.on(args.timestamp)["snakemake_rules"]["tier_raw"]["inputs"]
settings = Props.read_from(channel_dict["settings"])
channel_dict = channel_dict["out_spec"]
all_config = Props.read_from(channel_dict["gen_config"])

rng = np.random.default_rng()
rand_num = f"{rng.integers(0,99999):05d}"
temp_output = f"{args.output}.{rand_num}"

build_raw(args.input, out_spec=all_config, filekey=temp_output, **settings)

os.rename(temp_output, args.output)
