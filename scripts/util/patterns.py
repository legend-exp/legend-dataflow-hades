"""
This module contains all the patterns needed for the data production
"""

import os

from .utils import (
    par_dsp_path,
    par_hit_path,
    # par_overwrite_path,
    pars_path,
    plts_path,
    tier_daq_path,
    tier_dsp_path,
    tier_hit_path,
    tier_path,
    tier_raw_path,
    tmp_log_path,
    tmp_par_path,
    tmp_plts_path,
)


def key_pattern():
    return "{experiment}-{detector}-{measurement}-{run}-{timestamp}"

def processing_pattern():
    return key_pattern()+"-{processing_step}"


def par_pattern():
    pattern = key_pattern()
    pattern.replace("{timestamp}", "T%Z%")
    return pattern


def get_pattern_tier_daq(setup):
    return os.path.join(
        f"{tier_daq_path(setup)}",
        "{detector}",
        "{measurement}",
        key_pattern() + ".fcio",
    )


def get_pattern_tier_raw(setup):
    return os.path.join(
        f"{tier_raw_path(setup)}",
        "{detector}",
        "{measurement}",
        key_pattern() + "-tier_raw.lh5",
    )


def get_pattern_tier_dsp(setup):
    return os.path.join(
        f"{tier_dsp_path(setup)}",
        "{detector}",
        "{measurement}",
        key_pattern() + "-tier_dsp.lh5",
    )


def get_pattern_tier_hit(setup):
    return os.path.join(
        f"{tier_hit_path(setup)}",
        "{detector}",
        "{measurement}",
        key_pattern() + "-tier_hit.lh5",
    )


def get_pattern_tier(setup, tier, check_in_cycle=True):
    if tier == "daq":
        file_pattern = get_pattern_tier_daq(setup)
    elif tier == "raw":
        file_pattern = get_pattern_tier_raw(setup)
    elif tier == "dsp":
        file_pattern = get_pattern_tier_dsp(setup)
    elif tier == "hit":
        file_pattern = get_pattern_tier_hit(setup)
    else:
        msg = "invalid tier"
        raise Exception(msg)
    if tier_path(setup) not in file_pattern and check_in_cycle is True:
        return "/tmp/" + key_pattern() + f"tier_{tier}.lh5"
    else:
        return file_pattern


def get_pattern_par_dsp(setup, name=None, extension="json"):
    if name is not None:
        return os.path.join(
            f"{par_dsp_path(setup)}",
            "{detector}",
            "{measurement}",
            par_pattern() + f"-par_dsp_{name}.{extension}",
        )
    else:
        return os.path.join(
            f"{par_dsp_path(setup)}",
            "{detector}",
            "{measurement}",
            par_pattern() + f"-par_dsp.{extension}",
        )


def get_pattern_par_hit(setup, name=None, extension="json"):
    if name is not None:
        return os.path.join(
            f"{par_hit_path(setup)}",
            "{detector}",
            "{measurement}",
            par_pattern() + f"-par_hit_{name}.{extension}",
        )
    else:
        return os.path.join(
            f"{par_hit_path(setup)}",
            "{detector}",
            "{measurement}",
            par_pattern() + f"-par_hit.{extension}",
        )


def get_pattern_pars(setup, tier, name=None, extension="json", check_in_cycle=True):
    if tier == "dsp":
        file_pattern = get_pattern_par_dsp(setup, name, extension)
    elif tier == "hit":
        file_pattern = get_pattern_par_hit(setup, name, extension)
    else:
        msg = "invalid tier"
        raise Exception(msg)
    if pars_path(setup) not in file_pattern and check_in_cycle is True:
        if name is None:
            return "/tmp/" + par_pattern() + f"-par_{tier}.{extension}"
        else:
            return ("/tmp/" + par_pattern() + f"-par_{tier}_{name}.{extension}",)
    else:
        return file_pattern


def get_pattern_pars_tmp(setup, tier, name=None, extension="json"):
    if name is None:
        return os.path.join(
            f"{tmp_par_path(setup)}",
            par_pattern() + f"-par_{tier}.{extension}",
        )
    else:
        return os.path.join(
            f"{tmp_par_path(setup)}",
            par_pattern() + f"-par_{tier}_{name}.{extension}",
        )


def get_pattern_plts_tmp(setup, tier, name=None, extension="pkl"):
    if name is None:
        return os.path.join(
            f"{tmp_plts_path(setup)}",
            par_pattern() + f"-plt_{tier}.{extension}",
        )
    else:
        return os.path.join(
            f"{tmp_plts_path(setup)}",
            par_pattern() + f"-plt_{tier}_{name}.{extension}",
        )


def get_pattern_plts(setup, tier, name=None):
    if name is None:
        return os.path.join(
            f"{plts_path(setup)}",
            tier,
            "{detector}",
            "{measurement}",
            par_pattern() + f"-plt_{tier}_{name}.pkl",
        )
    else:
        return os.path.join(
            f"{plts_path(setup)}",
            "{detector}",
            "{measurement}",
            par_pattern() + f"-plt_{tier}.pkl",
        )


def get_pattern_log(setup, processing_step):
    return os.path.join(
        f"{tmp_log_path(setup)}",
        processing_step,
        key_pattern() + f"-{processing_step}.log",
    )


def get_pattern_log_par(setup, processing_step):
    return os.path.join(
        f"{tmp_log_path(setup)}",
        processing_step,
        par_pattern() + f"-{processing_step}.log",
    )


# def dsp_pars_fn_pattern(setup):
#     return os.path.join(f"{pargendata_path(setup)}", "dsp_proc_pars", "dsp_pp-{detector}-tier2.json")

# def dsp_pars_e_fn_pattern(setup):
#     return os.path.join(f"{pargendata_path(setup)}", "dsp_proc_pars", "dsp_pp_e-{detector}-tier2.json")

# def opt_grids_fn_pattern_combine(setup):
#     return os.path.join(f"{pargendata_path(setup)}", "dsp_proc_pars","energy_optimising","{{detector}}", "peak_grids", "{peak}.pkl" )

# def opt_grids_fn_pattern(setup):
#     return os.path.join(f"{pargendata_path(setup)}", "dsp_proc_pars","energy_optimising", "{detector}", "peak_grids", "{peak}.pkl" )

# def qbb_grid_fn_pattern(setup):
#     return os.path.join(f"{pargendata_path(setup)}", "dsp_proc_pars","energy_optimising", "{detector}", "qbb_grid.pkl" )

# def best_e_res_fn_pattern(setup):
#     return os.path.join(f"{pargendata_path(setup)}", "dsp_proc_pars","energy_optimising", "{detector}", "fwhms.json" )

# def opt_plots_fn_pattern(setup):
#     return os.path.join(f"{plot_path(setup)}", "{detector}", "energy_optimising" )

# def tau_plots_fn_pattern(setup):
#     return os.path.join(f"{plot_path(setup)}", "{detector}", "pz_preprocess","slope.pdf" )

# def ecal_fn_pattern(setup):
#     return os.path.join(f"{pargendata_path(setup)}", "hit_pproc", "ecal","all_sources","ecal-{detector}-{measurement}.json")

# def ecal_fn_pattern_sub(setup, detector, measurement):
#     return os.path.join(f"{pargendata_path(setup)}", "hit_pproc", "ecal","all_sources",f'ecal-{detector}-{measurement}.json')

# def th_ecal_fn_pattern(setup):
#     return os.path.join(f"{pargendata_path(setup)}", "hit_pproc", "ecal","all_sources","ecal-{detector}-th_HS2_top_psa.json")

# def ecal_th_fn_pattern(setup):
#     return os.path.join(f"{pargendata_path(setup)}", "hit_pproc", "ecal","th_ecal-{detector}.json")

# def ecal_plots_fn_pattern(setup):
#     return os.path.join(f"{plot_path(setup)}", "{detector}", "ecal", "{measurement}")

# def ecal_plots_fn_pattern_th(setup):
#     return os.path.join(f"{plot_path(setup)}", "{detector}", "ecal", "th_HS2_top_psa")

# def aoe_cal_fn_pattern(setup):
#     return os.path.join(f"{pargendata_path(setup)}", "hit_pproc", "aoe_cal","aoecal-{detector}.json")

# def aoe_plots_fn_pattern(setup):
#     return os.path.join(f"{plot_path(setup)}", "{detector}", "aoe","{detector}.pdf" )
