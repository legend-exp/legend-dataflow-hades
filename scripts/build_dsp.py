import argparse
import json
import logging
import os
import pathlib
import re
import time

os.environ["LGDO_CACHE"] = "false"
os.environ["LGDO_BOUNDSCHECK"] = "false"
os.environ["DSPEED_CACHE"] = "false"
os.environ["DSPEED_BOUNDSCHECK"] = "false"

import lgdo.lh5_store as lh5
import numpy as np
from dspeed import build_dsp
from legendmeta import LegendMetadata
from legendmeta.catalog import Props

argparser = argparse.ArgumentParser()
argparser.add_argument("--configs", help="configs path", type=str, required=True)
argparser.add_argument("--detector", help="detector", type=str, required=True)
argparser.add_argument("--timestamp", help="Timestamp", type=str, required=True)
argparser.add_argument("--pars_file", help="database file for detector", nargs="*", default=[])
argparser.add_argument("--log", help="log file", type=str)
argparser.add_argument("--input", help="input file", type=str)
argparser.add_argument("--output", help="output file", type=str)
argparser.add_argument("--db_file", help="db file", type=str)
args = argparser.parse_args()

pathlib.Path(os.path.dirname(args.log)).mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.DEBUG, filename=args.log, filemode="w")
logging.getLogger("numba").setLevel(logging.INFO)
logging.getLogger("parse").setLevel(logging.INFO)
log = logging.getLogger(__name__)

configs = LegendMetadata(path=args.configs)
channel_dict = configs.on(args.timestamp, system=args.datatype)["snakemake_rules"]["tier_dsp"][
    "inputs"
]["processing_chain"]

if isinstance(args.pars_file, list):
    database_dic = Props.read_from(args.pars_file)
else:
    with open(args.pars_file) as f:
        database_dic = json.load(f)


def replace_list_with_array(dic):
    for key, value in dic.items():
        if isinstance(value, dict):
            dic[key] = replace_list_with_array(value)
        elif isinstance(value, list):
            dic[key] = np.array(value)
        else:
            pass
    return dic


database_dic = replace_list_with_array(database_dic)

pathlib.Path(os.path.dirname(args.output)).mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng()
rand_num = f"{rng.integers(0,99999):05d}"
temp_output = f"{args.output}.{rand_num}"

start = time.time()

build_dsp(
    args.input,
    temp_output,
    {},
    database=database_dic,
    chan_config=channel_dict,
    write_mode="r",
)

log.info(f"build_dsp finished in {time.time()-start}")

os.rename(temp_output, args.output)

key = os.path.basename(args.output).replace("-tier_dsp.lh5", "")

raw_fields = [field.split("/")[-1] for field in lh5.ls(args.input, f"raw/")]

full_dict = {
    "valid_fields": {
        "raw": {"fields": raw_fields},
        "dsp": Props.read_from(file)["outputs"],
    },
}
pathlib.Path(os.path.dirname(args.db_file)).mkdir(parents=True, exist_ok=True)
with open(args.db_file, "w") as w:
    json.dump(full_dict, w, indent=4)
