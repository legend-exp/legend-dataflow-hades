"""
Snakemake rules for processing dsp tier. This is done in 4 steps:
- extraction of pole zero constant(s) for each channel from cal data
- extraction of energy filter parameters and charge trapping correction for each channel from cal data
- combining of all channels into single pars files with associated plot and results files
- running dsp over all channels using par file
"""
from scripts.util.patterns import (
    get_pattern_plts_tmp,
    get_pattern_par_dsp,
    get_pattern_plts,
    get_pattern_tier_raw,
    get_pattern_tier,
    get_pattern_pars_tmp,
    get_pattern_log,
    get_pattern_pars,
)


rule build_pars_dsp_tau:
    input:
        get_th_filelist_firstentry,
    params:
        #timestamp="{timestamp}",
        detector="{detector}",
    output:
        decay_const=temp(get_pattern_pars_tmp(setup, "dsp", "decay_constant")),
        plots=temp(get_pattern_plts_tmp(setup, "dsp", "decay_constant")),
    log:
        get_pattern_log_par(setup, "par_dsp_decay_constant"),
    group:
        "par-dsp"
    resources:
        runtime=300,
    shell:
        "{swenv} python3 -B "
        f"{workflow.source_path('../scripts/pars_dsp_tau.py')} "
        "--configs {configs} "
        "--log {log} "
        "--timestamp {params.timestamp} "
        "--detector {params.detector} "
        "--plot_path {output.plots} "
        "--output_file {output.decay_const} "
        "--raw_files {input.files}"


# # This rule builds the optimal energy filter parameters for the dsp using fft files
# rule build_pars_dsp_nopt:
#     input:
#         files=os.path.join(
#             filelist_path(setup), "all-{experiment}-{period}-{run}-fft-raw.filelist"
#         ),
#         database=get_pattern_pars_tmp(setup, "dsp", "decay_constant"),
#         inplots=get_pattern_plts_tmp(setup, "dsp", "decay_constant"),
#     params:
#         timestamp="{timestamp}",
#     output:
#         dsp_pars_nopt=temp(
#             get_pattern_pars_tmp(setup, "dsp", "noise_optimization")
#         ),
#         plots=temp(get_pattern_plts_tmp(setup, "dsp", "noise_optimization")),
#     log:
#         get_pattern_log(setup, "par_dsp_noise_optimization"),
#     group:
#         "par-dsp"
#     resources:
#         runtime=300,
#     shell:
#         "{swenv} python3 -B "
#         f"{workflow.source_path('../scripts/pars_dsp_nopt.py')} "
#         "--database {input.database} "
#         "--configs {configs} "
#         "--log {log} "
#         "--timestamp {params.timestamp} "
#         "--detector {params.detector} "
#         "--inplots {input.inplots} "
#         "--plot_path {output.plots} "
#         "--dsp_pars {output.dsp_pars_nopt} "
#         "--raw_filelist {input.files}"


# This rule builds the optimal energy filter parameters for the dsp using calibration dsp files
rule build_pars_dsp_eopt:
    input:
        files=get_th_filelist_longest_run,
        decay_const=get_pattern_pars_tmp_channel(setup, "dsp", "noise_optimization"),
        inplots=get_pattern_plts_tmp_channel(setup, "dsp", "noise_optimization"),
    params:
        #timestamp="{timestamp}",
        detector="{detector}",
    output:
        dsp_pars=temp(get_pattern_pars(setup, "dsp")),
        qbb_grid=temp(get_pattern_pars(setup, "dsp", "objects", extension="pkl")),
        plots=temp(get_pattern_plts(setup, "dsp")),
    log:
        get_pattern_log_par(setup, "pars_dsp_eopt"),
    group:
        "par-dsp"
    resources:
        runtime=300,
    shell:
        "{swenv} python3 -B "
        f"{workflow.source_path('../scripts/pars_dsp_eopt.py')} "
        "--log {log} "
        "--configs {configs} "
        "--timestamp {params.timestamp} "
        "--detector {params.detector} "
        "--raw_filelist {input.files} "
        "--tcm_filelist {input.tcm_filelist} "
        "--inplots {input.inplots} "
        "--decay_const {input.decay_const} "
        "--plot_path {output.plots} "
        "--qbb_grid_path {output.qbb_grid} "
        "--final_dsp_pars {output.dsp_pars}"


rule build_dsp:
    input:
        raw_file=get_pattern_tier_raw(setup),
        pars_file=get_par_dsp_file,
    params:
        timestamp="{timestamp}",
        detector="{detector}",
    output:
        tier_file=get_pattern_tier(setup, "dsp", check_in_cycle=check_in_cycle),
        db_file=get_pattern_pars_tmp(setup, "dsp_db"),
    log:
        get_pattern_log(setup, "tier_dsp"),
    group:
        "tier-dsp"
    resources:
        runtime=300,
        mem_swap=30,
    shell:
        "{swenv} python3 -B "
        f"{workflow.source_path('../scripts/build_dsp.py')} "
        "--log {log} "
        "--configs {configs} "
        "--detector {params.detector} "
        "--timestamp {params.timestamp} "
        "--input {input.raw_file} "
        "--output {output.tier_file} "
        "--db_file {output.db_file} "
        "--pars_file {input.pars_file}"
