"""
This module contains all the patterns needed for the data production
"""

from __future__ import annotations
from pathlib import Path

from .paths import (
    get_pars_path,
    pars_path,
    plts_path,
    tier_daq_path,
    tier_path,
    tmp_log_path,
    tmp_par_path,
    tmp_plts_path,
    get_tier_path
)


def key_pattern():
    return "{experiment}-{detector}-{measurement}-{run}-{timestamp}"


def processing_pattern():
    return key_pattern() + "-{processing_step}"


def par_pattern():
    pattern = key_pattern()
    return pattern


def get_pattern_tier_daq(setup):
    return (Path(f"{tier_daq_path(setup)}") /
        "{detector}" /
        "tier0" /
        "{measurement}" / 
        (key_pattern() + ".fcio")
    )

def get_pattern_tier(setup, tier, check_in_cycle=True):
    if tier == "daq":
        file_pattern = get_pattern_tier_daq(setup)
    elif tier in ["raw", "dsp", "hit"]:
        file_pattern = (
        Path(f"{get_tier_path(setup, tier)}") /
        "{detector}" /
        "{measurement}" /
        (key_pattern() + f"-tier_{tier}.lh5")
    )
    else:
        msg = "invalid tier"
        raise Exception(msg)
    if tier_path(setup) not in str(file_pattern) and check_in_cycle is True:
        return "/tmp/" + key_pattern() + f"tier_{tier}.lh5"
    else:
        return file_pattern


def get_pattern_pars(setup, tier, name=None, extension="yaml", check_in_cycle=True):
    if tier in ["dsp", "hit"]:

        if name is not None:
            file_pattern = (
                Path(get_pars_path(setup, tier))
                / "{detector}"
                / "{measurement}"
                / (
                    par_pattern() +
                    f"-par_{tier}_{name}.{extension}"
                )
            )
        else:
            file_pattern = (
                Path(get_pars_path(setup, tier))
                / "{detector}"
                / "{measurement}"
                / (
                    par_pattern() +
                    f"-par_{tier}.{extension}"
                )
            )
    else:
        msg = "invalid tier"
        raise Exception(msg)
    if pars_path(setup) not in str(file_pattern) and check_in_cycle is True:
        if name is None:
            return ("/tmp/" + par_pattern() + f"-par_{tier}.{extension}")
        else:
            return ("/tmp/" + par_pattern() + f"-par_{tier}_{name}.{extension}")
    else:
        return file_pattern


def get_pattern_pars_tmp(setup, tier, name=None, extension="yaml"):
    if name is None:
        return (
            Path(f"{tmp_par_path(setup)}") /
            (par_pattern() + f"-par_{tier}.{extension}")
        )
    else:
        return (
            Path(f"{tmp_par_path(setup)}") / 
            (par_pattern() + f"-par_{tier}_{name}.{extension}")
        )


def get_pattern_plts_tmp(setup, tier, name=None, extension="pkl"):
    if name is None:
        return (
            Path(f"{tmp_plts_path(setup)}") / 
            (par_pattern() + f"-plt_{tier}.{extension}")
        )
    else:
        return (
            Path(f"{tmp_plts_path(setup)}") /
            (par_pattern() + f"-plt_{tier}_{name}.{extension}")
        )


def get_pattern_plts(setup, tier, name=None):
    if name is None:
        return (
            Path(f"{plts_path(setup)}")/
            tier /
            "{detector}" /
            "{measurement}" /
            (par_pattern() + f"-plt_{tier}_{name}.pkl"),
        )
    else:
        return (
            Path(f"{plts_path(setup)}") /
            "{detector}" /
            "{measurement}" /
            (par_pattern() + f"-plt_{tier}.pkl"),
        )


def get_pattern_log(setup, processing_step, time):
    return (
        Path(f"{tmp_log_path(setup)}") /
        time / 
        processing_step /
        (key_pattern() + f"-{processing_step}.log"),
    )


def get_pattern_log_par(setup, processing_step, time):
    return (
        Path(f"{tmp_log_path(setup)}") / 
        time / 
        processing_step /
        (par_pattern() + f"-{processing_step}.log"),
    )