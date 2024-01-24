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
        get_pattern_tier_daq(setup),
    params:
        timestamp="{timestamp}",
        detector="{detector}",
    output:
        get_pattern_tier(setup, "raw", check_in_cycle=check_in_cycle),
    log:
        get_pattern_log(setup, "tier_raw"),
    group:
        "tier-raw"
    resources:
        mem_swap=110,
        runtime=300,
    shell:
        "{swenv} python3 -B "
        f"{workflow.source_path('../scripts/build_raw.py')} "
        "--log {log} "
        "--configs {configs} "
        "--datatype {params.datatype} "
        "--detector {params.detector} "
        "--timestamp {params.timestamp} "
        "{input} {output}"