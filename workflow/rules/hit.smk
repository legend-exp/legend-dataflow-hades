"""
Snakemake rules for processing hit tier. This is done in 4 steps:
- extraction of calibration curves(s) for each channel from cal data
- extraction of psd calibration parameters for each channel from cal data
- combining of all channels into single pars files with associated plot and results files
- running build hit over all channels using par file
"""

from hadesflow.methods.patterns import (
    get_pattern_tier,
    get_pattern_log,
)

rule build_hit:
    input:
        dsp_file=get_pattern_tier(config, "dsp", check_in_cycle=False),
        pars_file=get_par_hit_file,
    output:
        tier_file=get_pattern_tier(config, "hit", check_in_cycle=check_in_cycle),
        db_file=get_pattern_pars_tmp(config, "hit_db"),
    params:
        timestamp="{timestamp}",
        detector="{detector}",
    log:
        get_pattern_log(config, "tier_hit"),
    group:
        "tier-hit"
    resources:
        runtime=300,
    shell:
        "{swenv} python3 -B "
        f"{workflow.source_path('../scripts/build_hit.py')} "
        "--configs {configs} "
        "--log {log} "
        "--detector {params.detector} "
        "--timestamp {params.timestamp} "
        "--pars_file {input.pars_file} "
        "--output {output.tier_file} "
        "--input {input.dsp_file} "
        "--db_file {output.db_file}"
