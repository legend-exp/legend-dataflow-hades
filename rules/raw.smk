from scripts.util.patterns import (
    get_pattern_tier_daq,
    get_pattern_tier_raw,
    get_pattern_tier,
    get_pattern_log,
)


rule build_raw:
    """
    This rule runs build raw, it takes in a daq file and outputs a raw file
    """
    input:
        get_daq_file,
    params:
        timestamp="{timestamp}",
        detector="{detector}",
    output:
        get_pattern_tier(setup, "raw", check_in_cycle=check_in_cycle),
    log:
        get_pattern_log(setup, "tier_raw"),
    group:
        "tier-raw"
    shell:
        "{swenv} python3 -B "
        f"{workflow.source_path('../scripts/build_raw.py')} "
        "--log {log} "
        "--configs {configs} "
        "--detector {params.detector} "
        "--timestamp {params.timestamp} "
        "{input} {output}"
