from scripts.utils import *
import pathlib, os

# Set with `snakemake --configfile=/path/to/your/config.json`
# configfile: "have/to/specify/path/to/your/config.json"

subst_vars_in_snakemake_config(workflow, config)

setup = config["setups"]["l200hades"]
metadata = metadata_path(setup)
swenv = runcmd(setup)

basedir = workflow.basedir


localrules: do_nothing, autogen_keylist, gen_filelist, autogen_output

rule do_nothing:
    input:


# Auto-generate "all[-{detector}[-{measurement}[-{run}[-{timestamp}]]]].keylist"
# based on available tier0 files.
rule autogen_keylist:
    output:
        "all{keypart,|-.*}.keylist"
    params:
        setup = lambda wildcards: setup
    script:
        "scripts/create_keylist.py"


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

# Create "{label}-{tier}.gen", based on "{label}.keylist" via
# "{label}-{tier}.filelist". Will implicitly trigger creation of all files
# in "{label}-{tier}.filelist".
# Example: "all[-{detector}[-{measurement}[-{run}[-{timestamp}]]]]-{tier}.gen":
rule autogen_output:
    input:
        read_filelist
    output:
        "{label}-{tier,[^-]+}.gen"
    run:
        pathlib.Path(output[0]).touch()


rule tier0_to_tier1:
    input:
        tier_fn_pattern(setup, "tier0")
    output:
        tier_fn_pattern(setup, "tier1")
    group: "tier-1-2"
    resources:
        runtime=300
    shell:
        "{swenv} python3 {basedir}/scripts/tier0_to_tier1.py {input} {output}"


rule tier1_to_tier2:
    input:
        tier_fn_pattern(setup, "tier1")
    output:
        tier_fn_pattern(setup, "tier2")
    group: "tier-1-2"
    resources:
        runtime=300
    shell:
        "{swenv} python3 {basedir}/scripts/tier1_to_tier2.py --metadata {metadata} --nmax 100 {input} {output}"
