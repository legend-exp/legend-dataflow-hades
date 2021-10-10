from scripts.utils import *
import pathlib, os

# Set with `snakemake --configfile=/path/to/your/config.json`
# configfile: "have/to/specify/path/to/your/config.json"

subst_vars_in_snakemake_config(workflow, config)

setup = config["setups"]["l200hades"]
metadata = metadata_path(setup)
swenv = runcmd(setup, "default")

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
        files = f.read().splitlines()
        return files 

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
    group: "tier-1"
    resources:
        runtime=300
    shell:
        "{swenv} python3 {basedir}/scripts/tier0_to_tier1.py {input} {output}"

def get_th_filelist_firstentry(wildcards):
    label = "all-"+wildcards.detector+"-th_HS2_lat_psa"
    with checkpoints.gen_filelist.get(label=label, tier="tier1").output[0].open() as f:
        files = f.read().splitlines()
        return files[0]

rule tier1_to_tier2_preprocess_tau:
    input:
        get_th_filelist_firstentry
    output:
        dsp_pars_fn_pattern(setup)
    group: "tier-1-2-pproc"
    resources:
        runtime=300
    shell:
        "{swenv} python3 {basedir}/scripts/tier2_preprocess_tau.py --metadata {metadata} {input} {output}"

def get_th_filelist_longest_run(wildcards):
    #with open(f"all-{wildcards.detector}-th_HS2_lat_psa-tier1.filelist") as f:
    label = "all-"+wildcards.detector+"-th_HS2_lat_psa"
    with checkpoints.gen_filelist.get(label=label, tier="tier1").output[0].open() as f:
        files = f.read().splitlines()
        run_files = sorted(run_splitter(files),key=len)
        return run_files[-1]

rule tier1_to_tier2_preprocess_energy:
    input:
        filelist = "all-{detector}-th_HS2_lat_psa-tier1.filelist",
        genlist= "all-{detector}-th_HS2_lat_psa-tier1.gen",
        #files = get_th_filelist_longest_run,
        db_dict_path = dsp_pars_fn_pattern(setup)
    params:    
        peak = "{peak}"
    output:
        opt_grids_fn_pattern(setup)
    group: "tier-1-2-pproc_e"
    resources:
        runtime=300
    shell:
        "{swenv} python3 {basedir}/scripts/tier2_preprocess_energy.py --db_dict_path {input.db_dict_path}  --metadata {metadata} --peak {params.peak}  --output_path {output} {input.filelist}"

rule tier1_to_tier2_preprocess_energy_combine:
    input:
        files = expand(opt_grids_fn_pattern_combine(setup), peak = [238.632,   583.191, 727.330, 860.564, 1620.5, 2614.553]),
        filelist = "all-{detector}-th_HS2_lat_psa-tier1.filelist",
        db_dict_path = dsp_pars_fn_pattern(setup)
    output:
        qbb_grid = qbb_grid_fn_pattern(setup),
        fwhms = best_e_res_fn_pattern(setup),
        db_dict_path = dsp_pars_e_fn_pattern(setup)
    group: "tier-1-2-pproc_ec"
    resources:
        runtime=300
    shell:
        "{swenv} python3 {basedir}/scripts/tier2_preprocess_energy_combine.py --db_dict_path {output.db_dict_path} --metadata {metadata} --raw_filelist {input.filelist} --tau_db_dict_path {input.db_dict_path} --qbb_grid_path {output.qbb_grid} --fwhm_path {output.fwhms} {input.files}  "



rule tier1_to_tier2:
    input:
        infile = tier_fn_pattern(setup, "tier1"), 
        database = dsp_pars_fn_pattern(setup),
        database_energy = dsp_pars_e_fn_pattern(setup)
    output:
        tier_fn_pattern(setup, "tier2")
    group: "tier-2"
    resources:
        runtime=300
    shell:
        "{swenv} python3 {basedir}/scripts/tier1_to_tier2.py --metadata {metadata} --database_tau {input.database} --database_energy {input.database_energy} {input.infile} {output}"

