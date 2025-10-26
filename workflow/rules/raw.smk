from hadesflow.methods.patterns import (
    get_pattern_tier_daq,
    get_pattern_tier,
    get_pattern_log,
)
from legenddataflowscripts.workflow import execenv_pyexe

def get_json_output(output):
    print(output[0])
    return "'{filekey:" + output+"}'"

rule build_raw:
    """
    This rule runs build raw, it takes in a daq file and outputs a raw file
    """
    input:
        get_daq_file,
    params:
        config_file=lambda wildcards: get_config_files(
            dataflow_configs_texdb,
            wildcards.timestamp,
            wildcards.measurement,
            wildcards.detector,
            "tier_raw",
            "raw_config",
        )
    output:
        get_pattern_tier(config, "raw", check_in_cycle=check_in_cycle),
    log:
        get_pattern_log(config, "tier_raw", time),
    group:
        "tier-raw"
    shell:
        execenv_pyexe(config, "legend-daq2lh5") + " "
        "--out-spec {params.config_file} "
        "{input} "
        "--kwargs " + "'" + '{{"filekey":' +'"{output}"' + "}}'"
        " > {log}"
