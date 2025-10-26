"""
Snakemake rules for building dsp pars for HPGes, before running build_dsp()
- extraction of pole zero constant(s) for each channel from cal data
- extraction of energy filter parameters and charge trapping correction for each channel from cal data
"""

from hadesflow.methods.patterns import (
    get_pattern_pars_tmp,
    get_pattern_plts_tmp,
    get_pattern_pars,
    get_pattern_plts,
    get_pattern_log,
    get_pattern_tier,
    get_pattern_log,
    get_pattern_pars,
)
from hadesflow.methods.paths import (
    filelist_path,
    config_path,
)
from legenddataflowscripts.workflow import execenv_pyexe


rule build_pars_dsp_pz_geds:
    input:
        files=(
            Path(filelist_path(config))
            / "all-{experiment}-{detector}-{measurement}-{run}-raw.filelist"
        ),
    params:
        config_file=lambda wildcards: get_config_files(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            wildcards.detector,
            "pars_dsp_tau",
            "tau_config",
        ),
        processing_chain=lambda wildcards: get_config_files(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            wildcards.detector,
            "pars_dsp_tau",
            "processing_chain",
        ),
        log_config=lambda wildcards: get_log_config(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            "pars_dsp_tau",
        ),
        raw_table_name="raw",
        configs=config_path(config),
    output:
        decay_const=temp(get_pattern_pars_tmp(config, "dsp", "decay_constant")),
        plots=temp(get_pattern_plts_tmp(config, "dsp", "decay_constant")),
    log:
        get_pattern_log(config, "par_dsp_decay_constant", time),
    group:
        "par-dsp"
    resources:
        runtime=300,
    shell:
        execenv_pyexe(config, "par-geds-dsp-pz") + "-p --log {log} "
        "--log-config {params.log_config} "
        "--config-file {params.config_file} "
        "--processing-chain {params.processing_chain} "
        "--raw-table-name {params.raw_table_name} "
        "--plot-path {output.plots} "
        "--output-file {output.decay_const} "
        "--raw-files {input.files} "


rule build_pars_evtsel_geds:
    input:
        files=os.path.join(
            filelist_path(config),
            "all-{experiment}-{detector}-{measurement}-{run}-raw.filelist",
        ),
        database=rules.build_pars_dsp_pz_geds.output.decay_const,
    params:
        config_file=lambda wildcards: get_config_files(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            wildcards.detector,
            "pars_dsp_peak_selection",
            "peak_config",
        ),
        processing_chain=lambda wildcards: get_config_files(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            wildcards.detector,
            "pars_dsp_peak_selection",
            "processing_chain",
        ),
        log_config=lambda wildcards: get_log_config(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            "pars_dsp_peak_selection",
        ),
        raw_table_name="raw",
    output:
        peak_file=temp(get_pattern_pars_tmp(config, "dsp", "peaks", extension="lh5")),
    log:
        get_pattern_log(config, "par_dsp_event_selection", time),
    group:
        "par-dsp"
    resources:
        runtime=300,
        mem_swap=70,
    shell:
        execenv_pyexe(config, "par-geds-dsp-evtsel") + "-p --log {log} "
        "--log-config {params.log_config} "
        "--config-file {params.config_file} "
        "--processing-chain {params.processing_chain} "
        "--raw-table-name {params.raw_table_name} "
        "--peak-file {output.peak_file} "
        "--decay-const {input.database} "
        "--raw-filelist {input.files}"


# This rule builds the optimal energy filter parameters for the dsp using calibration dsp files
rule build_pars_dsp_eopt_geds:
    input:
        peak_file=rules.build_pars_evtsel_geds.output.peak_file,
        decay_const=rules.build_pars_dsp_pz_geds.output.decay_const,
        inplots=rules.build_pars_dsp_pz_geds.output.plots,
    params:
        config_file=lambda wildcards: get_config_files(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            wildcards.detector,
            "pars_dsp_eopt",
            "optimiser_config",
        ),
        processing_chain=lambda wildcards: get_config_files(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            wildcards.detector,
            "pars_dsp_eopt",
            "processing_chain",
        ),
        log_config=lambda wildcards: get_log_config(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            "pars_dsp_eopt",
        ),
        raw_table_name="raw",
    output:
        dsp_pars=temp(get_pattern_pars(config, "dsp")),
        qbb_grid=temp(get_pattern_pars(config, "dsp", "objects", extension="pkl")),
        plots=temp(get_pattern_plts(config, "dsp")),
    log:
        get_pattern_log(config, "pars_dsp_eopt", time),
    group:
        "par-dsp"
    resources:
        runtime=300,
    shell:
        execenv_pyexe(config, "par-geds-dsp-eopt") + "--log {log} "
        "--log-config {params.log_config} "
        "--config-file {params.config_file} "
        "--processing-chain {params.processing_chain} "
        "--raw-table-name {params.raw_table_name} "
        "--peak-file {input.peak_file} "
        "--inplots {input.inplots} "
        "--decay-const {input.decay_const} "
        "--plot-path {output.plots} "
        "--qbb-grid-path {output.qbb_grid} "
        "--final-dsp-pars {output.dsp_pars}"
