"""
Helper functions for running data production
"""

import pathlib, os
import snakemake as smk
from dbetto import AttrsDict
from hadesflow.methods.utils import (
    run_splitter,
    convert_to_daq_timestamp,
    convert_to_daq_run,
)
from hadesflow.methods.FileKey import ProcessingFileKey
from hadesflow.methods.patterns import (
    # par_overwrite_path,
    get_pattern_pars,
    get_pattern_tier_daq,
    get_pattern_tier,
)
from hadesflow.scripts.flow.build_filelist import get_filelist_full_wildcards
from hadesflow.methods.paths import tier_daq_path
from legenddataflowscripts.workflow import as_ro


def ro(path):
    return as_ro(config, path)


def get_th_filelist_longest_run(wildcards):
    # # with open(f"all-{wildcards.detector}-th_HS2_lat_psa-tier1.filelist") as f:
    # label = f"all-{wildcards.experiment}-{wildcards.detector}-th_HS2_top_psa"
    # with checkpoints.gen_filelist.get(label=label, tier="raw").output[0].open() as f:
    #     files = f.read().splitlines()
    #     run_files = sorted(run_splitter(files), key=len)
    #     return run_files[-1]
    return


def get_daq_file(wildcards):
    wildcards = dict(wildcards)
    wildcards["timestamp"] = convert_to_daq_timestamp(wildcards["timestamp"])
    wildcards["run"] = convert_to_daq_run(wildcards["run"])
    return smk.io.expand(get_pattern_tier_daq(config), **wildcards)[0]


def get_par_file(wildcards, tier):
    pattern = get_pattern_pars(config, tier, check_in_cycle=False)
    measurement = wildcards.measurement
    wildcards = AttrsDict(dict(wildcards))

    if Path(
        str(get_pattern_tier_daq(config).parent)
        .replace("{detector}", wildcards.detector)
        .replace("{measurement}", "th_HS2_lat_psa")
    ).is_dir():
        wildcards["measurement"] = "th_HS2_lat_psa"
    else:
        wildcards["measurement"] = "th_HS2_top_psa"

    wildcards["run"] = "*"
    wildcards["timestamp"] = "*"

    # if wildcards.measurement == "bkg":
    #     measurement = "th_HS2_top_psa"
    # elif wildcards.measurement == "co_HS5_top_hvs":
    #     measurement = "co_HS5_top_dlt"
    # elif wildcards.measurement == "am_HS1_top_ssh":
    #     measurement = "am_HS1_lat_ssh"

    wildcards = AttrsDict(wildcards)

    files = get_filelist_full_wildcards(
        wildcards,
        config,
        get_pattern_tier(config, "daq", check_in_cycle=False),
        "raw",
        ignore_keys_file=Path(dataflow_configs) / "ignored_cycles.yaml",
    )
    fk = ProcessingFileKey.get_filekey_from_pattern(Path(files[0]).name)
    return ProcessingFileKey.get_full_path_from_filename(
        files[0], get_pattern_tier(config, "raw", check_in_cycle=False), pattern
    )


def get_config_files(config_db, timestamp, measurement, channel, rule_name, field):
    if isinstance(config_db, (str, Path)):
        config_db = TextDB(config_db, lazy=True)
    rule_dict = config_db.valid_for(timestamp, system=measurement)["snakemake_rules"][
        rule_name
    ]["inputs"][field]

    return ro(rule_dict[channel] if channel in rule_dict else rule_dict["__default__"])


def get_log_config(config_db, timestamp, measurement, rule_name):
    if isinstance(config_db, (str, Path)):
        config_db = TextDB(config_db, lazy=True)
    return ancient(
        ro(
            config_db.valid_for(timestamp, system=measurement)["snakemake_rules"][
                rule_name
            ]["options"]["logging"]
        )
    )
