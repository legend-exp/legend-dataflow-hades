from dspeed import build_dsp
import argparse
from dbetto import Props

from legenddataflowscripts.utils import (
    build_log,
)


def build_dsp_hades():
    # CLI config
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "--processing-chain", help="path to dataflow config files", required=True, nargs="*"
    )
    argparser.add_argument("--log", help="log file name")
    argparser.add_argument("--log-config", help="log config file")

    argparser.add_argument("--settings", help="settings", required=False, nargs="*")

    argparser.add_argument("--database", help="database file for HPGes", nargs="*", default=[])
    argparser.add_argument("--input", help="input file")

    argparser.add_argument("--output", help="output file")
    args = argparser.parse_args()

    build_log(args.log_config, args.log)

    db = Props.read_from(args.database)
    proc_chain = Props.read_from(args.processing_chain)

    settings_dict = Props.read_from(args.settings) if args.settings else {}

    build_dsp(
        args.input,
        args.output,
        proc_chain,
        database=db,
        write_mode="r",
        buffer_len=settings_dict.get("buffer_len", 1000),
        block_width=settings_dict.get("block_width", 16),
        lh5_tables="raw",
        base_group="",
    )
