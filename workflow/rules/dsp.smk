"""
Snakemake rules for processing dsp tier. This is done in 4 steps:
- extraction of pole zero constant(s) for each channel from cal data
- extraction of energy filter parameters and charge trapping correction for each channel from cal data
- combining of all channels into single pars files with associated plot and results files
- running dsp over all channels using par file
"""

from hadesflow.methods.patterns import (
    get_pattern_plts_tmp,
    get_pattern_plts,
    get_pattern_tier,
    get_pattern_pars_tmp,
    get_pattern_log,
    get_pattern_pars,
    get_pattern_log_par,
)


rule build_dsp:
    input:
        raw_file=get_pattern_tier(config, "raw", check_in_cycle=False),
        pars_file=lambda wildcards: get_par_file(wildcards, "dsp"),
    params:
        config_file=lambda wildcards: get_config_files(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            wildcards.detector,
            "tier_dsp",
            "processing_chain",
        ),
        log_config=lambda wildcards: get_log_config(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            "tier_dsp",
        ),
    output:
        tier_file=get_pattern_tier(config, "dsp", check_in_cycle=check_in_cycle),
    log:
        get_pattern_log(config, "tier_dsp", time),
    group:
        "tier-dsp"
    resources:
        runtime=300,
        mem_swap=30,
    shell:
        execenv_pyexe(config, "build-dsp-hades") + "--log {log} "
        "--log-config {params.log_config} "
        "--input {input.raw_file} "
        "--output {output.tier_file} "
        "--processing-chain {params.config_file} "
        "--database {input.pars_file} "
