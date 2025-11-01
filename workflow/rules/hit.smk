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
        pars_file=lambda wildcards: get_par_file(wildcards, "hit"),
    params:
        config_file=lambda wildcards: get_config_files(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            wildcards.detector,
            "tier_hit",
            "config_file",
        ),
        log_config=lambda wildcards: get_log_config(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            "tier_hit",
        ),
    output:
        tier_file=get_pattern_tier(config, "hit", check_in_cycle=check_in_cycle),
    log:
        get_pattern_log(config, "tier_hit", time),
    group:
        "tier-hit"
    resources:
        runtime=300,
    shell:
        execenv_pyexe(config, "build-hit-hades") + "--log {log} "
        "--log-config {params.log_config} "
        "--input {input.dsp_file} "
        "--config {params.config_file} {input.pars_file} "
        "--output {output.tier_file} "
