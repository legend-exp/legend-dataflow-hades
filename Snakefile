from scripts.utils import *

# Set with `snakemake --configfile=/path/to/your/config.json`
# configfile: "have/to/specify/path/to/your/config.json"

setup = config["setups"]["l200hades"]


rule do_nothing:
    input:


rule tier0_to_tier1:
    input:
        tier_fn_pattern(setup, "tier0")
    output:
        tier_fn_pattern(setup, "tier1")
    script:
        "scripts/tier0_to_tier1.py"


rule tier1_to_tier2:
    input:
        tier_fn_pattern(setup, "tier1")
    output:
        tier_fn_pattern(setup, "tier2")
    params:
        n_max = lambda wildcards: 100
    script:
        "scripts/tier1_to_tier2.py"


# Create any of "dataset[-{detector}[-{measurement}[-{run}[-{timestamp}]]]].keys":
rule create_dataset:
    output:
        "dataset{keypart,|-.*}.keys"
    params:
        setup = lambda wildcards: setup
    script:
        "scripts/create_dataset.py"


# Create any of "{tier}[-{detector}[-{measurement}[-{run}[-{timestamp}]]]].files":
checkpoint create_filelist:
    input:
        "dataset{keypart}.keys"
    output:
        "{tier,[^-]+}{keypart,|-.*}.files"
    params:
        setup = lambda wildcards: setup
    script:
        "scripts/create_filelist.py"


def read_filelist(wildcards):
    with checkpoints.create_filelist.get(tier=wildcards.tier,keypart=wildcards.keypart).output[0].open() as f:
        return f.read().splitlines() 

# Create any of "{tier}[-{detector}[-{measurement}[-{run}[-{timestamp}]]]].gen":
rule gen_filelist:
    input:
        read_filelist
    output:
        "{tier,[^-]+}{keypart,|-.*}.gen"
    shell:
        "touch {output}"
