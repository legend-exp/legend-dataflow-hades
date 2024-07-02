import pathlib, os, json, sys
import scripts.util as ds
from scripts.util.patterns import get_pattern_tier_daq
from scripts.util.utils import (
    subst_vars_in_snakemake_config,
    runcmd,
    config_path,
    filelist_path,
    metadata_path,
)
from datetime import datetime
from collections import OrderedDict

# Set with `snakemake --configfile=/path/to/your/config.json`
# configfile: "have/to/specify/path/to/your/config.json"

check_in_cycle = True

subst_vars_in_snakemake_config(workflow, config)

setup = config["setups"]["l200hades"]
metadata = metadata_path(setup)
swenv = runcmd(setup, "default")

basedir = workflow.basedir


setup = config["setups"]["l200"]
configs = config_path(setup)
meta = metadata_path(setup)
swenv = runcmd(setup)
basedir = workflow.basedir


include: "rules/common.smk"
include: "rules/main.smk"
include: "rules/raw.smk"
include: "rules/dsp.smk"
include: "rules/hit.smk"


localrules:
    gen_filelist,
    autogen_output,


onstart:
    print("Starting workflow")


onsuccess:
    print("Workflow finished, no error")
    shell("rm *.gen || true")
    shell(f"rm {filelist_path(setup)}/* || true")


# Placeholder, can email or maybe put message in slack
onerror:
    print("An error occurred :( ")


checkpoint gen_filelist:
    """
    This rule generates the filelist. It is a checkpoint so when it is run it will update
    the dag passed on the files it finds as an output. It does this by taking in the search
    pattern, using this to find all the files that match this pattern, deriving the keys from
    the files found and generating the list of new files needed.
    """
    output:
        os.path.join(filelist_path(setup), "{label}-{tier}.{extension}list"),
    params:
        setup=lambda wildcards: setup,
        search_pattern=lambda wildcards: get_pattern_tier_daq(setup),
        basedir=basedir,
        configs=configs,
        chan_maps=chan_maps,
    script:
        "scripts/create_filelist.py"
