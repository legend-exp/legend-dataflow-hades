"""
Helper functions for running data production
"""
import pathlib, os
from scripts.util.utils import run_splitter
from scripts.util.patterns import (
    par_overwrite_path,
    get_pattern_tier_daq,
    get_pattern_tier_raw,
    get_pattern_plts_tmp,
)


def read_filelist(wildcards):
    with checkpoints.gen_filelist.get(
        label=wildcards.label, tier=wildcards.tier"
    ).output[0].open() as f:
        files = f.read().splitlines()
        return files

def get_th_filelist_firstentry(wildcards):
    label = f"all-{wildcards.detector}-th_HS2_top_psa"
    with checkpoints.gen_filelist.get(label=label, tier="raw").output[0].open() as f:
        files = f.read().splitlines()
        return files[0]


def get_th_filelist_longest_run(wildcards):
    #with open(f"all-{wildcards.detector}-th_HS2_lat_psa-tier1.filelist") as f:
    label = "all-"+wildcards.detector+"-th_HS2_top_psa"
    with checkpoints.gen_filelist.get(label=label, tier="raw").output[0].open() as f:
        files = f.read().splitlines()
        run_files = sorted(run_splitter(files),key=len)
        return run_files[-1]

def get_par_dsp_file(wildcards):
    pattern = get_pattern_par_dsp(setup)
    

def get_par_hit_file(wildcards):
    pattern = get_pattern_par_hit(setup)
    measurement = wildcards.measurement
    if wildcards.measurement == "bkg":
        measurement = "th_HS2_top_psa"
    elif wildcards.measurement == "co_HS5_top_hvs":
        measurement = "co_HS5_top_dlt"
    elif wildcards.measurement == "am_HS1_top_ssh":
        measurement = "am_HS1_lat_ssh"
    pattern.replace("{measurement}", measurement)
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

