from hadesflow.methods.patterns import (
    get_pattern_plts_tmp,
    get_pattern_plts,
    get_pattern_tier,
    get_pattern_pars_tmp,
    get_pattern_log_par,
    get_pattern_pars,
)


# This rule builds the qc using the calibration dsp files and fft files
rule par_hit_qc:
    input:
        files=(
            Path(filelist_path(config))
            / "all-{experiment}-{detector}-{measurement}-{run}-dsp.filelist"
        ),
    params:
        config_file=lambda wildcards: get_config_files(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            wildcards.detector,
            "pars_hit_qc",
            "qc_config",
        ),
        log_config=lambda wildcards: get_log_config(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            "pars_hit_qc",
        ),
        dsp_table_name="raw",
    output:
        qc_file=temp(get_pattern_pars_tmp(config, "hit", "qc")),
        plot_file=temp(get_pattern_plts(config, "hit", "qc")),
    log:
        get_pattern_log_par(config, "pars_hit_qc", time),
    group:
        "par-hit"
    resources:
        runtime=300,
    shell:
        execenv_pyexe(config, "par-geds-hit-qc") + "--log {log} "
        "--log-config {params.log_config} "
        "--config-file {params.config_file} "
        "--table-name {params.dsp_table_name} "
        "--plot-path {output.plot_file} "
        "--save-path {output.qc_file} "
        "--cal-files {input.files} "


# This rule builds the energy calibration using the calibration dsp files
rule build_energy_calibration:
    input:
        files=(
            Path(filelist_path(config))
            / "all-{experiment}-{detector}-{measurement}-{run}-dsp.filelist"
        ),
        ctc_dict=get_pattern_pars(config, "dsp"),
        inplots=rules.par_hit_qc.output.plot_file,
        in_hit_dict=rules.par_hit_qc.output.qc_file,
    params:
        config_file=lambda wildcards: get_config_files(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            wildcards.detector,
            "pars_hit_ecal",
            "ecal_config",
        ),
        log_config=lambda wildcards: get_log_config(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            "pars_hit_ecal",
        ),
        dsp_table_name="raw",
        det_status="on",
    output:
        ecal_file=temp(get_pattern_pars_tmp(config, "hit", "energy_cal")),
        results_file=temp(
            get_pattern_pars_tmp(config, "hit", "energy_cal_objects", extension="pkl")
        ),
        plot_file=temp(get_pattern_plts_tmp(config, "hit", "energy_cal")),
    # wildcard_constraints:
    #     measurement = "^th*"
    log:
        get_pattern_log_par(config, "pars_hit_energy_cal", time),
    group:
        "par-hit"
    resources:
        runtime=300,
    shell:
        execenv_pyexe(config, "par-geds-hit-ecal") + "--log {log} "
        "--log-config {params.log_config} "
        "--config-file {params.config_file} "
        "--det-status {params.det_status} "
        "--table-name {params.dsp_table_name} "
        "--plot-path {output.plot_file} "
        "--results-path {output.results_file} "
        "--save-path {output.ecal_file} "
        "--inplot-dict {input.inplots} "
        "--in-hit-dict {input.in_hit_dict} "
        "--ctc-dict {input.ctc_dict} "
        "--files {input.files}"


# This rule builds the a/e calibration using the calibration dsp files
rule build_aoe_calibration:
    input:
        files=(
            Path(filelist_path(config))
            / "all-{experiment}-{detector}-{measurement}-{run}-dsp.filelist"
        ),
        ecal_file=get_pattern_pars_tmp(config, "hit", "energy_cal"),
        eres_file=get_pattern_pars_tmp(
            config, "hit", "energy_cal_objects", extension="pkl"
        ),
        inplots=get_pattern_plts_tmp(config, "hit", "energy_cal"),
    params:
        config_file=lambda wildcards: get_config_files(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            wildcards.detector,
            "pars_hit_aoecal",
            "aoecal_config",
        ),
        log_config=lambda wildcards: get_log_config(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            "pars_hit_aoecal",
        ),
        dsp_table_name="raw",
    output:
        hit_pars=temp(get_pattern_pars_tmp(config, "hit", "aoe_cal")),
        aoe_results=temp(
            get_pattern_pars_tmp(config, "hit", "aoe_cal_objects", extension="pkl")
        ),
        plot_file=temp(get_pattern_plts_tmp(config, "hit", "aoe_cal")),
    log:
        get_pattern_log_par(config, "pars_hit_aoe_cal", time),
    group:
        "par-hit"
    resources:
        runtime=300,
    shell:
        execenv_pyexe(config, "par-geds-hit-aoe") + "--log {log} "
        "--log-config {params.log_config} "
        "--config-file {params.config_file} "
        "--table-name {params.dsp_table_name} "
        "--aoe-results {output.aoe_results} "
        "--hit-pars {output.hit_pars} "
        "--plot-file {output.plot_file} "
        "--inplots {input.inplots} "
        "--eres-file {input.eres_file} "
        "--ecal-file {input.ecal_file} "
        "{input.files}"


# This rule builds the lq calibration using the calibration dsp files
rule build_lq_calibration:
    input:
        files=(
            Path(filelist_path(config))
            / "all-{experiment}-{detector}-{measurement}-{run}-dsp.filelist"
        ),
        ecal_file=get_pattern_pars_tmp(config, "hit", "aoe_cal"),
        eres_file=get_pattern_pars_tmp(
            config, "hit", "aoe_cal_objects", extension="pkl"
        ),
        inplots=get_pattern_plts_tmp(config, "hit", "aoe_cal"),
    params:
        config_file=lambda wildcards: get_config_files(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            wildcards.detector,
            "pars_hit_lqcal",
            "lqcal_config",
        ),
        log_config=lambda wildcards: get_log_config(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            "pars_hit_lqcal",
        ),
        dsp_table_name="raw",
    output:
        hit_pars=get_pattern_pars(config, "hit", check_in_cycle=check_in_cycle),
        lq_results=get_pattern_pars(
            config,
            "hit",
            name="objects",
            extension="dir",
            check_in_cycle=check_in_cycle,
        ),
        plot_file=get_pattern_plts(config, "hit"),
    log:
        get_pattern_log_par(config, "pars_hit_lq_cal", time),
    group:
        "par-hit"
    resources:
        runtime=300,
    shell:
        execenv_pyexe(config, "par-geds-hit-lq") + "--log {log} "
        "--log-config {params.log_config} "
        "--config-file {params.config_file} "
        "--table-name {params.dsp_table_name} "
        "--hit-pars {output.hit_pars} "
        "--plot-file {output.plot_file} "
        "--lq-results {output.lq_results} "
        "--ecal-file {input.ecal_file} "
        "--inplots {input.inplots} "
        "--eres-file {input.eres_file} "
        "{input.files}"
