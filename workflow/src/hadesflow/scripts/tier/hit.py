from pygama.hit import build_hit
import argparse
from dbetto import Props

from legenddataflowscripts.utils import (
    build_log,
)


def build_hit_hades():
    # CLI config
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "--config", help="path to dataflow config files", required=True, nargs="*"
    )
    argparser.add_argument("--pars", help="path to pars files", required=True, nargs="*")
    argparser.add_argument("--log", help="log file name")
    argparser.add_argument("--log-config", help="log config file")

    argparser.add_argument("--settings", help="settings", required=False, nargs="*")

    argparser.add_argument("--input", help="input file")
    argparser.add_argument("--output", help="output file")
    args = argparser.parse_args()

    build_log(args.log_config, args.log)

    db = Props.read_from(args.config)
    pars = Props.read_from(args.pars)["pars"]
    Props.add_to(db, pars)

    settings_dict = Props.read_from(args.settings) if args.settings else {}

    build_hit(args.input, hit_config=db, outfile=args.output, lh5_tables=["dsp"], **settings_dict)
