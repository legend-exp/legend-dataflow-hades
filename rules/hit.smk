"""
Snakemake rules for processing hit tier. This is done in 4 steps:
- extraction of calibration curves(s) for each channel from cal data
- extraction of psd calibration parameters for each channel from cal data
- combining of all channels into single pars files with associated plot and results files
- running build hit over all channels using par file
"""

from scripts.util.patterns import (
    get_pattern_plts_tmp,
    get_pattern_par_hit,
    get_pattern_plts,
    get_pattern_par_dsp,
    get_pattern_tier_dsp,
    get_pattern_tier,
    get_pattern_pars_tmp,
    get_pattern_log,
    get_pattern_pars,
    get_pattern_log_par,
)


# This rule builds the energy calibration using the calibration dsp files
rule build_energy_calibration:
    input:
        files=lambda wildcards: read_filelist_det(wildcards, "dsp"),
        ctc_dict=get_par_dsp_file,
    params:
        timestamp="{timestamp}",
        detector="{detector}",
        source="{measurement}",
    output:
        ecal_file=temp(get_pattern_pars_tmp(setup, "hit", "energy_cal")),
        results_file=temp(
            get_pattern_pars_tmp(setup, "hit", "energy_cal_objects", extension="pkl")
        ),
        plot_file=temp(get_pattern_plts_tmp(setup, "hit", "energy_cal")),
    # wildcard_constraints:
    #     measurement = "^th*"
    log:
        get_pattern_log_par(setup, "pars_hit_energy_cal"),
    group:
        "par-hit"
    resources:
        runtime=300,
    shell:
        "{swenv} python3 -B "
        f"{workflow.source_path('../scripts/pars_hit_ecal.py')} "
        "--log {log} "
        "--detector {params.detector} "
        "--timestamp {params.timestamp} "
        "--measurement {params.source} "
        "--configs {configs} "
        "--plot_path {output.plot_file} "
        "--results_path {output.results_file} "
        "--save_path {output.ecal_file} "
        "--ctc_dict {input.ctc_dict} "
        "--files {input.files}"


# This rule builds the a/e calibration using the calibration dsp files
rule build_aoe_calibration:
    input:
        files=os.path.join(
            filelist_path(setup),
            "all-{experiment}-{detector}-th_HS2_top_psa-dsp.filelist",
        ),
        ecal_file=get_pattern_pars_tmp(setup, "hit", "energy_cal"),
        eres_file=get_pattern_pars_tmp(
            setup, "hit", "energy_cal_objects", extension="pkl"
        ),
        inplots=get_pattern_plts_tmp(setup, "hit", "energy_cal"),
    params:
        timestamp="{timestamp}",
        detector="{detector}",
        source="{measurement}",
    output:
        hit_pars=temp(get_pattern_pars_tmp(setup, "hit", "aoe_cal")),
        aoe_results=temp(
            get_pattern_pars_tmp(setup, "hit", "aoe_cal_objects", extension="pkl")
        ),
        plot_file=temp(get_pattern_plts_tmp(setup, "hit", "aoe_cal")),
    log:
        get_pattern_log_par(setup, "pars_hit_aoe_cal"),
    group:
        "par-hit"
    resources:
        runtime=300,
    shell:
        "{swenv} python3 -B "
        f"{workflow.source_path('../scripts/pars_hit_aoe.py')} "
        "--log {log} "
        "--configs {configs} "
        "--detector {params.detector} "
        "--timestamp {params.timestamp} "
        "--measurement {params.source} "
        "--inplots {input.inplots} "
        "--aoe_results {output.aoe_results} "
        "--eres_file {input.eres_file} "
        "--hit_pars {output.hit_pars} "
        "--plot_file {output.plot_file} "
        "--ecal_file {input.ecal_file} "
        "{input.files}"


# This rule builds the lq calibration using the calibration dsp files
rule build_lq_calibration:
    input:
        files=os.path.join(
            filelist_path(setup),
            "all-{experiment}-{detector}-th_HS2_top_psa-dsp.filelist",
        ),
        ecal_file=get_pattern_pars_tmp(setup, "hit", "aoe_cal"),
        eres_file=get_pattern_pars_tmp(setup, "hit", "aoe_cal_objects", extension="pkl"),
        inplots=get_pattern_plts_tmp(setup, "hit", "aoe_cal"),
    params:
        timestamp="{timestamp}",
        detector="{detector}",
        source="{measurement}",
    output:
        hit_pars=get_pattern_pars(setup, "hit", check_in_cycle=check_in_cycle),
        lq_results=get_pattern_pars(
            setup,
            "hit",
            name="objects",
            extension="dir",
            check_in_cycle=check_in_cycle,
        ),
        plot_file=get_pattern_plts(setup, "hit"),
    log:
        get_pattern_log_par(setup, "pars_hit_lq_cal"),
    group:
        "par-hit"
    resources:
        runtime=300,
    shell:
        "{swenv} python3 -B "
        f"{workflow.source_path('../scripts/pars_hit_lq.py')} "
        "--log {log} "
        "--configs {configs} "
        "--detector {params.detector} "
        "--timestamp {params.timestamp} "
        "--measurement {params.source} "
        "--inplots {input.inplots} "
        "--lq_results {output.lq_results} "
        "--eres_file {input.eres_file} "
        "--hit_pars {output.hit_pars} "
        "--plot_file {output.plot_file} "
        "--ecal_file {input.ecal_file} "
        "{input.files}"


rule build_hit:
    input:
        dsp_file=get_pattern_tier_dsp(setup),
        pars_file=get_par_hit_file,
    output:
        tier_file=get_pattern_tier(setup, "hit", check_in_cycle=check_in_cycle),
        db_file=get_pattern_pars_tmp(setup, "hit_db"),
    params:
        timestamp="{timestamp}",
        detector="{detector}",
    log:
        get_pattern_log(setup, "tier_hit"),
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
