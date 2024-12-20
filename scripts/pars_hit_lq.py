from __future__ import annotations

import argparse
import json
import logging
import os
import pathlib
import pickle as pkl
import warnings

import numpy as np
import pandas as pd
from legendmeta import LegendMetadata
from legendmeta.catalog import Props
from pygama.math.peak_fitting import gauss_cdf
from pygama.pargen.lq_cal import *  # noqa: F403
from pygama.pargen.lq_cal import cal_lq
from pygama.pargen.utils import get_tcm_pulser_ids, load_data

log = logging.getLogger(__name__)
warnings.filterwarnings(action="ignore", category=RuntimeWarning)


def lq_calibration(
    data: pd.DataFrame,
    cal_dicts: dict,
    energy_param: str,
    cal_energy_param: str,
    eres_func: callable,
    cdf: callable = gauss_cdf,
    selection_string: str = "",
    plot_options: dict | None = None,
):
    """Loads in data from the provided files and runs the LQ calibration on said files

    Parameters
    ----------
    data: pd.DataFrame
        A dataframe containing the data used for calibrating LQ
    cal_dicts: dict
        A dict of hit-level operations to apply to the data
    energy_param: string
        The energy parameter of choice. Used for normalizing the
        raw lq values
    cal_energy_param: string
        The calibrated energy parameter of choice
    eres_func: callable
        The energy resolution functions
    cdf: callable
        The CDF used for the binned fitting of LQ distributions
    selection_string: string
        A string of flags to apply to the data when running the calibration
    plot_options: dict
        A dict containing the plot functions the user wants to run,and any
        user options to provide those plot functions

    Returns
    -------
    cal_dicts: dict
        The user provided dict, updated with hit-level operations for LQ
    results_dict: dict
        A dict containing the results of the LQ calibration
    plot_dict: dict
        A dict containing all the figures specified by the plot options
    lq: cal_lq class
        The cal_lq object used for the LQ calibration
    """

    lq = cal_lq(
        cal_dicts,
        cal_energy_param,
        eres_func,
        cdf,
        selection_string,
        plot_options,
    )

    data["LQ_Ecorr"] = np.divide(data["lq80"], data[energy_param])

    lq.update_cal_dicts(
        {
            "LQ_Ecorr": {
                "expression": f"lq80/{energy_param}",
                "parameters": {},
            }
        }
    )

    lq.calibrate(data, "LQ_Ecorr")
    log.info("Calibrated LQ")
    return cal_dicts, lq.get_results_dict(), lq.fill_plot_dict(data), lq


argparser = argparse.ArgumentParser()
argparser.add_argument("files", help="files", nargs="*", type=str)
argparser.add_argument("--ecal_file", help="ecal_file", type=str, required=True)
argparser.add_argument("--eres_file", help="eres_file", type=str, required=True)
argparser.add_argument("--inplots", help="in_plot_path", type=str, required=False)

argparser.add_argument("--configs", help="configs", type=str, required=True)
argparser.add_argument("--detector", help="detector", type=str, required=True)
argparser.add_argument("--timestamp", help="timestamp", type=str, required=True)
argparser.add_argument("--measurement", help="measurement", type=str, required=True)

argparser.add_argument("--log", help="log_file", type=str)

argparser.add_argument("--plot_file", help="plot_file", type=str, required=False)
argparser.add_argument("--hit_pars", help="hit_pars", type=str)
argparser.add_argument("--lq_results", help="lq_results", type=str)
args = argparser.parse_args()

logging.basicConfig(level=logging.DEBUG, filename=args.log, filemode="w")
logging.getLogger("numba").setLevel(logging.INFO)
logging.getLogger("parse").setLevel(logging.INFO)
logging.getLogger("lgdo").setLevel(logging.INFO)
logging.getLogger("h5py").setLevel(logging.INFO)
logging.getLogger("matplotlib").setLevel(logging.INFO)

configs = LegendMetadata(path=args.configs)
channel_dict = configs.on(args.timestamp)["snakemake_rules"]["pars_hit_lqcal"]["inputs"][
    "lqcal_config"
][args.detector]

kwarg_dict = Props.read_from(channel_dict)

ecal_dict = Props.read_from(args.ecal_file)
cal_dict = ecal_dict["pars"]["operations"]
eres_dict = ecal_dict["results"]

with open(args.eres_file, "rb") as o:
    object_dict = pkl.load(o)

if kwarg_dict["run_lq"] is True:
    kwarg_dict.pop("run_lq")

    cdf = eval(kwarg_dict.pop("cdf")) if "cdf" in kwarg_dict else gauss_cdf

    if "plot_options" in kwarg_dict:
        for field, item in kwarg_dict["plot_options"].items():
            kwarg_dict["plot_options"][field]["function"] = eval(item["function"])

    with open(args.files[0]) as f:
        files = f.read().splitlines()
    files = sorted(files)[:8]

    try:
        eres = eres_dict[kwarg_dict["cal_energy_param"]]["eres_linear"].copy()

        def eres_func(x):
            return eval(eres["expression"], dict(x=x, **eres["parameters"]))

    except KeyError:

        def eres_func(x):
            return x * np.nan

    params = [
        "lq80",
        "dt_eff",
        kwarg_dict["energy_param"],
        kwarg_dict["cal_energy_param"],
        kwarg_dict["cut_field"],
    ]

    # load data in
    data, threshold_mask = load_data(
        files,
        "char_data/dsp",
        cal_dict,
        params=params,
        threshold=kwarg_dict.pop("threshold"),
        return_selection_mask=True,
    )

    data["is_pulser"] = np.zeros(len(data), dtype=bool)

    cal_dict, out_dict, plot_dict, obj = lq_calibration(
        data,
        selection_string=f"{kwarg_dict.pop('cut_field')}&(~is_pulser)",
        cal_dicts=cal_dict,
        eres_func=eres_func,
        cdf=cdf,
        **kwarg_dict,
    )

    # need to change eres func as can't pickle lambdas
    try:
        obj.eres_func = eres_dict[kwarg_dict["cal_energy_param"]]["eres_linear"].copy()
    except KeyError:
        obj.eres_func = {}
else:
    out_dict = {}
    plot_dict = {}
    obj = None

if args.plot_file:
    common_dict = plot_dict.pop("common") if "common" in list(plot_dict) else None
    if args.inplots:
        with open(args.inplots, "rb") as r:
            out_plot_dict = pkl.load(r)
        out_plot_dict.update({"lq": plot_dict})
    else:
        out_plot_dict = {"lq": plot_dict}

    if "common" in list(out_plot_dict) and common_dict is not None:
        out_plot_dict["common"].update(common_dict)
    elif common_dict is not None:
        out_plot_dict["common"] = common_dict

    pathlib.Path(os.path.dirname(args.plot_file)).mkdir(parents=True, exist_ok=True)
    with open(args.plot_file, "wb") as w:
        pkl.dump(out_plot_dict, w, protocol=pkl.HIGHEST_PROTOCOL)

pathlib.Path(os.path.dirname(args.hit_pars)).mkdir(parents=True, exist_ok=True)
with open(args.hit_pars, "w") as w:
    final_hit_dict = {
        "pars": {"operations": cal_dict},
        "results": {"ecal": eres_dict, "lq": out_dict},
    }
    json.dump(final_hit_dict, w, indent=4)

pathlib.Path(os.path.dirname(args.lq_results)).mkdir(parents=True, exist_ok=True)
with open(args.lq_results, "wb") as w:
    pkl.dump({"ecal": object_dict, "lq": obj}, w, protocol=pkl.HIGHEST_PROTOCOL)
