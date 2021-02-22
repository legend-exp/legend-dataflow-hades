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


# Auto-generate "all[-{detector}[-{measurement}[-{run}[-{timestamp}]]]].keylist"
# based on available tier0 files.
rule autogen_dataset:
    output:
        "all{keypart,|-.*}.keylist"
    params:
        setup = lambda wildcards: setup
    script:
        "scripts/create_dataset.py"


checkpoint gen_filelist:
    input:
        "{label}.keylist"
    output:
        "{label}-{tier,[^-]+}.filelist"
    params:
        setup = lambda wildcards: setup
    script:
        "scripts/create_filelist.py"


def read_filelist(wildcards):
    with checkpoints.gen_filelist.get(label=wildcards.label, tier=wildcards.tier).output[0].open() as f:
        return f.read().splitlines() 

# Create "{label}-{tier}.gen", based on "{label}.keylist" via "{label}-{tier}.filelist".
# E.g. "all[-{detector}[-{measurement}[-{run}[-{timestamp}]]]]-{tier}.gen":
rule autogen_output:
    input:
        read_filelist
    output:
        "{label}-{tier,[^-]+}.gen"
    shell:
        "touch {output}"
