"""
This module contains all the utility needed for the data production.
These are mainly resolvers for the config.json dictionary,
and for substituting the pathvar within, also the conversion
from timestamp to unix time
"""

import copy
import os
import string
from datetime import datetime

# from dateutil import parser

# For testing/debugging, use
# from scripts.utils import *
# import snakemake as smk
# setup = smk.load_configfile("config.json")["setups"]["l200"]


def tier_daq_path(setup):
    return setup["paths"]["tier_daq"]


def tier_path(setup):
    return setup["paths"]["tier"]


def tier_tcm_path(setup):
    return setup["paths"]["tier_tcm"]


def tier_raw_path(setup):
    return setup["paths"]["tier_raw"]


def tier_dsp_path(setup):
    return setup["paths"]["tier_dsp"]


def tier_hit_path(setup):
    return setup["paths"]["tier_hit"]


def get_tier_path(setup, tier):
    if tier == "raw":
        return tier_raw_path(setup)
    elif tier == "dsp":
        return tier_dsp_path(setup)
    elif tier == "hit":
        return tier_hit_path(setup)
    else:
        msg = f"no tier matching:{tier}"
        raise ValueError(msg)


def config_path(setup):
    return setup["paths"]["config"]


def chan_map_path(setup):
    return setup["paths"]["chan_map"]


def metadata_path(setup):
    return setup["paths"]["metadata"]


def detector_db_path(setup):
    return setup["paths"]["detector_db"]


def par_raw_path(setup):
    return setup["paths"]["par_raw"]


def par_dsp_path(setup):
    return setup["paths"]["par_dsp"]


def par_hit_path(setup):
    return setup["paths"]["par_hit"]


def pars_path(setup):
    return setup["paths"]["par"]


def get_pars_path(setup, tier):
    if tier == "raw":
        return par_raw_path(setup)
    elif tier == "dsp":
        return par_dsp_path(setup)
    elif tier == "hit":
        return par_hit_path(setup)
    else:
        msg = f"no tier matching:{tier}"
        raise ValueError(msg)


def tmp_par_path(setup):
    return setup["paths"]["tmp_par"]


def tmp_plts_path(setup):
    return setup["paths"]["tmp_plt"]


def plts_path(setup):
    return setup["paths"]["plt"]


def par_overwrite_path(setup):
    return setup["paths"]["par_overwrite"]


def log_path(setup):
    return setup["paths"]["log"]


def tmp_log_path(setup):
    return setup["paths"]["tmp_log"]


def filelist_path(setup):
    return setup["paths"]["tmp_filelists"]


def runcmd(setup):
    exec_cmd = setup["execenv"]["cmd"]
    exec_arg = setup["execenv"]["arg"]
    path_install = setup["paths"]["install"]
    return f"PYTHONUSERBASE={path_install} {exec_cmd} {exec_arg}"


def subst_vars_impl(x, var_values, ignore_missing=False):
    if isinstance(x, str):
        if "$" in x:
            if ignore_missing:
                return string.Template(x).safe_substitute(var_values)
            else:
                return string.Template(x).substitute(var_values)
        else:
            return x
    if isinstance(x, dict):
        for key in x:
            value = x[key]
            new_value = subst_vars_impl(value, var_values, ignore_missing)
            if new_value is not value:
                x[key] = new_value
        return x
    if isinstance(x, list):
        for i in range(len(x)):
            value = x[i]
            new_value = subst_vars_impl(value, var_values, ignore_missing)
            if new_value is not value:
                x[i] = new_value
        return x
    else:
        return x


def subst_vars(props, var_values=None, use_env=False, ignore_missing=False):
    if var_values is None:
        var_values = {}
    combined_var_values = var_values
    if use_env:
        combined_var_values = dict(iter(os.environ.items()))
        combined_var_values.update(copy.copy(var_values))
    subst_vars_impl(props, combined_var_values, ignore_missing)


def subst_vars_in_snakemake_config(workflow, config):
    config_filename = workflow.overwrite_configfiles[0]  # ToDo: Better way of handling this?
    subst_vars(
        config,
        var_values={"_": os.path.dirname(config_filename)},
        use_env=True,
        ignore_missing=False,
    )


def run_splitter(files):
    """
    Returns list containing lists of each run
    """

    runs = []
    run_files = []
    for file in files:
        base = os.path.basename(file)
        file_name = os.path.splitext(base)[0]
        parts = file_name.split("-")
        run_no = parts[3]
        if run_no not in runs:
            runs.append(run_no)
            run_files.append([])
        for i, run in enumerate(runs):
            if run == run_no:
                run_files[i].append(file)
    return run_files


def unix_time(value):
    if isinstance(value, str):
        return datetime.timestamp(datetime.strptime(value, "%Y%m%dT%H%M%SZ"))
    else:
        msg = f"Can't convert type {type(value)} to unix time"
        raise ValueError(msg)


def convert_to_legend_timestamp(value):
    return datetime.strftime(datetime.strptime(value, "%y%m%dT%H%M%S"), "%Y%m%dT%H%M%SZ")


def convert_to_daq_timestamp(value):
    return datetime.strftime(datetime.strptime(value, "%Y%m%dT%H%M%SZ"), "%y%m%dT%H%M%S")
