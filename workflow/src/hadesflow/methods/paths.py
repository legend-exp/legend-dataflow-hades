
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