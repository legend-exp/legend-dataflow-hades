import argparse
import json
import logging
import os
import pathlib
import time

from legendmeta import LegendMetadata
from legendmeta.catalog import Props
from pygama.hit.build_hit import build_hit

argparser = argparse.ArgumentParser()
argparser.add_argument("--input", help="input file", type=str)
argparser.add_argument("--pars_file", help="hit pars file", nargs="*")

argparser.add_argument("--configs", help="configs", type=str, required=True)
argparser.add_argument("--detector", help="detector", type=str, required=True)
argparser.add_argument("--timestamp", help="Timestamp", type=str, required=True)
argparser.add_argument("--tier", help="Tier", type=str, required=True)

argparser.add_argument("--log", help="log_file", type=str)

argparser.add_argument("--output", help="output file", type=str)
argparser.add_argument("--db_file", help="db file", type=str)
args = argparser.parse_args()

pathlib.Path(os.path.dirname(args.log)).mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.DEBUG, filename=args.log, filemode="w")
logging.getLogger("numba").setLevel(logging.INFO)
logging.getLogger("parse").setLevel(logging.INFO)
logging.getLogger("pygama.lgdo.lh5_store").setLevel(logging.INFO)
logging.getLogger("h5py._conv").setLevel(logging.INFO)


log = logging.getLogger(__name__)


configs = LegendMetadata(path=args.configs)
if args.tier == "hit":
    channel_dict = configs.on(args.timestamp)["snakemake_rules"]["tier_hit"]["inputs"][
        "hit_config"
    ][args.detector]
else:
    msg = "unknown tier"
    raise ValueError(msg)

cfg_dict = Props.read_from(channel_dict)

if isinstance(args.pars_file, list):
    pars_dict = Props.read_from(args.pars_file)
else:
    with open(args.pars_file) as f:
        pars_dict = json.load(f)

Props.add_to(pars_dict, cfg_dict)

t_start = time.time()
pathlib.Path(os.path.dirname(args.output)).mkdir(parents=True, exist_ok=True)
build_hit(args.input, hit_config=pars_dict, outfile=args.output)
t_elap = time.time() - t_start
log.info(f"Done!  Time elapsed: {t_elap:.2f} sec.")

full_dict = {
    "valid_fields": {args.tier: pars_dict["outputs"]},
}

pathlib.Path(os.path.dirname(args.db_file)).mkdir(parents=True, exist_ok=True)
with open(args.db_file, "w") as w:
    json.dump(full_dict, w, indent=4)
