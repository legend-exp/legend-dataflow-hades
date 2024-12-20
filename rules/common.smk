"""
Helper functions for running data production
"""

import pathlib, os
import snakemake as smk
from scripts.util.utils import run_splitter, convert_to_daq_timestamp
from scripts.util.FileKey import ProcessingFileKey
from scripts.util.patterns import (
    # par_overwrite_path,
    get_pattern_tier_daq,
    get_pattern_tier_raw,
)


def read_filelist(wildcards):
    with checkpoints.gen_filelist.get(
        label=wildcards.label, tier=wildcards.tier
    ).output[0].open() as f:
        files = f.read().splitlines()
        return files


def read_filelist_det(wildcards, tier):
    label = f"all-{wildcards.experiment}-{wildcards.detector}-{wildcards.measurement}"
    with checkpoints.gen_filelist.get(label=label, tier=tier).output[0].open() as f:
        files = f.read().splitlines()
        return files


def get_th_filelist_firstentry(wildcards):
    label = f"all-{wildcards.experiment}-{wildcards.detector}-th_HS2_top_psa"
    with checkpoints.gen_filelist.get(label=label, tier="raw").output[0].open() as f:
        files = f.read().splitlines()
        return files[0]


def get_th_filelist_longest_run(wildcards):
    # with open(f"all-{wildcards.detector}-th_HS2_lat_psa-tier1.filelist") as f:
    label = f"all-{wildcards.experiment}-{wildcards.detector}-th_HS2_top_psa"
    with checkpoints.gen_filelist.get(label=label, tier="raw").output[0].open() as f:
        files = f.read().splitlines()
        run_files = sorted(run_splitter(files), key=len)
        return run_files[-1]


def get_par_dsp_file(wildcards):
    pattern = get_pattern_par_dsp(setup)
    pattern = pattern.replace("{measurement}", "th_HS2_top_psa")
    measurement = "th_HS2_top_psa"
    label = f"all-{wildcards.experiment}-{wildcards.detector}-{measurement}"
    with checkpoints.gen_filelist.get(label=label, tier="raw").output[0].open() as f:
        files = f.read().splitlines()
    file = sorted(read_filelist_det(wildcards, "raw"))[0]
    fk = ProcessingFileKey.get_filekey_from_pattern(
        os.path.splitext(os.path.basename(file))[0]
    )
    pattern = pattern.replace("{timestamp}", fk.timestamp)
    return pattern


def get_daq_file(wildcards):
    tstamp = convert_to_daq_timestamp(wildcards.timestamp)
    pattern = smk.io.expand(get_pattern_tier_daq(setup), **wildcards)[0]
    pattern = pattern.replace(wildcards.timestamp, tstamp)
    return pattern


def get_par_hit_file(wildcards):
    pattern = get_pattern_par_hit(setup)
    measurement = wildcards.measurement
    if wildcards.measurement == "bkg":
        measurement = "th_HS2_top_psa"
    elif wildcards.measurement == "co_HS5_top_hvs":
        measurement = "co_HS5_top_dlt"
    elif wildcards.measurement == "am_HS1_top_ssh":
        measurement = "am_HS1_lat_ssh"
    pattern = pattern.replace("{measurement}", measurement)
    label = f"all-{wildcards.experiment}-{wildcards.detector}-{measurement}"
    with checkpoints.gen_filelist.get(label=label, tier="raw").output[0].open() as f:
        files = f.read().splitlines()
    file = sorted(read_filelist_det(wildcards, "raw"))[0]
    fk = ProcessingFileKey.get_filekey_from_pattern(
        os.path.splitext(os.path.basename(file))[0]
    )
    pattern = pattern.replace("{timestamp}", fk.timestamp)
    return pattern
# def get_tier2_files(wildcards):
#     label = f"all-{wildcards.detector}-{wildcards.measurement}"
#     with checkpoints.gen_filelist.get(label=label, tier="tier2").output[0].open() as f:
#         files = f.read().splitlines()
#         return sorted(files)
# def get_tier2_files_th(wildcards):
#     label = f"all-{wildcards.detector}-th_HS2_top_psa"
#     with checkpoints.gen_filelist.get(label=label, tier="tier2").output[0].open() as f:
#         files = f.read().splitlines()
#         return sorted(files)
