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
    label = f"all-{wildcards.detector}-th_HS2_top_psa"
    with checkpoints.gen_filelist.get(label=label, tier="tier1").output[0].open() as f:
        files = f.read().splitlines()
        return files[0]

rule tier1_to_tier2_preprocess_tau:
    input:
        get_th_filelist_firstentry
    params:
        det = "{detector}"
    output:
        out_files = dsp_pars_fn_pattern(setup),
        out_plots = tau_plots_fn_pattern(setup)
    group: "tier-1-2-pproc"
    resources:
        runtime=300
    shell:
        "{swenv} python3 {basedir}/scripts/tier2_preprocess_tau.py --metadata {metadata} --detector {params.det} --plot_path {output.out_plots} {input} {output.out_files}"

def get_th_filelist_longest_run(wildcards):
    #with open(f"all-{wildcards.detector}-th_HS2_lat_psa-tier1.filelist") as f:
    label = "all-"+wildcards.detector+"-th_HS2_top_psa"
    with checkpoints.gen_filelist.get(label=label, tier="tier1").output[0].open() as f:
        files = f.read().splitlines()
        run_files = sorted(run_splitter(files),key=len)
        return run_files[-1]

rule tier1_to_tier2_preprocess_energy:
    input:
        #filelist = "all-{detector}-th_HS2_top_psa-tier1.filelist",
        #genlist= "all-{detector}-th_HS2_top_psa-tier1.gen",
        files = get_th_filelist_longest_run,
        db_dict_path = dsp_pars_fn_pattern(setup)
    params:    
        peak = "{peak}",
        det = "{detector}"
    output:
        opt_grids_fn_pattern(setup)
    group: "tier-1-2-pproc_e"
    resources:
        runtime=300
    shell:
        "{swenv} python3 {basedir}/scripts/tier2_preprocess_energy.py --db_dict_path {input.db_dict_path}  --metadata {metadata} --detector {params.det} --peak {params.peak}  --output_path {output} {input.files}"

rule tier1_to_tier2_preprocess_energy_combine:
    input:
        files = expand(opt_grids_fn_pattern_combine(setup), peak = [238.632,   583.191, 727.330, 860.564, 1620.5, 2614.553]),
        filelist = "all-{detector}-th_HS2_top_psa-tier1.filelist",
        db_dict_path = dsp_pars_fn_pattern(setup)
    params:
        det = "{detector}"
    output:
        qbb_grid = qbb_grid_fn_pattern(setup),
        fwhms = best_e_res_fn_pattern(setup),
        db_dict_path = dsp_pars_e_fn_pattern(setup),
        plot_path = directory(opt_plots_fn_pattern(setup))
    group: "tier-1-2-pproc_ec"
    resources:
        runtime=300
    shell:
        "{swenv} python3 {basedir}/scripts/tier2_preprocess_energy_combine.py --db_dict_path {output.db_dict_path} --metadata {metadata} --detector {params.det} --raw_filelist {input.filelist} --tau_db_dict_path {input.db_dict_path} --qbb_grid_path {output.qbb_grid} --fwhm_path {output.fwhms} --plot_save_path {output.plot_path} {input.files}  "



rule tier1_to_tier2:
    input:
        infile = tier_fn_pattern(setup, "tier1"), 
        database = dsp_pars_e_fn_pattern(setup)
    params:
        det = "{detector}"
    output:
        tier_fn_pattern(setup, "tier2")
    group: "tier-2"
    resources:
        runtime=300
    shell:
        "{swenv} python3 {basedir}/scripts/tier1_to_tier2.py --metadata {metadata} --detector {params.det}  --database {input.database} {input.infile} {output}"

def get_tier2_files(wildcards): 
    label = f'all-{wildcards.detector}-{wildcards.measurement}'
    with checkpoints.gen_filelist.get(label=label, tier="tier2").output[0].open() as f:
        files = f.read().splitlines()
        return sorted(files)[:10]

def get_tier2_files_th(wildcards): 
    label = f'all-{wildcards.detector}-th_HS2_top_psa'
    with checkpoints.gen_filelist.get(label=label, tier="tier2").output[0].open() as f:
        files = f.read().splitlines()
        return sorted(files)[:10]

def get_all_tier2_files_th(wildcards): 
    label = f'all-{wildcards.detector}-th_HS2_top_psa'
    with checkpoints.gen_filelist.get(label=label, tier="tier2").output[0].open() as f:
        files = f.read().splitlines()
        return sorted(files)

ruleorder: th_energy_calibration > energy_calibration

rule th_energy_calibration:
    input:
        files = get_tier2_files_th
    params:
        det = "{detector}"
    output:
        cal_file = th_ecal_fn_pattern(setup),
        th_cal_file = ecal_th_fn_pattern(setup),
        plot_file = directory(ecal_plots_fn_pattern_th(setup))
    group: "tier-2-ecal"
    resources:
        runtime=300
    shell:
        "{swenv} python3 {basedir}/scripts/run_energy_cal.py --metadata {metadata} --detector {params.det} --measurement th_HS2_top_psa --detector {params.det} --plot_path {output.plot_file} --save_path {output.cal_file} --th_cal_file {output.th_cal_file} {input.files}"

rule energy_calibration:
    input:
        files = get_tier2_files
    params:
        source = "{measurement}",
        det = "{detector}"
    output:
        cal_file = ecal_fn_pattern(setup),
        plot_file = directory(ecal_plots_fn_pattern(setup))
    group: "tier-2-ecal"
    resources:
        runtime=300
    shell:
        "{swenv} python3 {basedir}/scripts/run_energy_cal.py --metadata {metadata} --detector {params.det} --measurement {params.source} --detector {params.det} --plot_path {output.plot_file} --save_path {output.cal_file} {input.files}"   

rule aoe_calibration:
    input:
        files = get_all_tier2_files_th,
        ecal_file = ecal_th_fn_pattern(setup)
    params:
        det = "{detector}"
    output:
        aoe_cal_file =  aoe_cal_fn_pattern(setup),
        plot_file = aoe_plots_fn_pattern(setup)
    group: "tier-2-aoe"
    resources:
        runtime=300
    shell:
        "{swenv} python3 {basedir}/scripts/run_aoe_cal.py  --metadata {metadata} --detector {params.det} --plot_file {output.plot_file} --aoe_cal_file {output.aoe_cal_file} --ecal_file {input.ecal_file} {input.files}"     


def get_ecal_file(wildcards):
    measurement = wildcards.measurement
    detector = wildcards.detector
    if wildcards.measurement == "bkg":
        measurement = "th_HS2_top_psa"
    elif wildcards.measurement == "co_HS5_top_hvs":
        measurement = "co_HS5_top_dlt"
    elif wildcards.measurement =="am_HS1_top_ssh":
        measurement = "am_HS1_lat_ssh"
    pattern = ecal_fn_pattern_sub(setup, detector, measurement)
    return pattern

rule tier2_to_tier3:
    input:
        infile = tier_fn_pattern(setup, "tier2"), 
        ecal_database = get_ecal_file, 
        aoe_database = aoe_cal_fn_pattern(setup)
    params:
        det = "{detector}"
    output:
        tier_fn_pattern(setup, "tier3")
    group: "tier-3"
    resources:
        runtime=300
    shell:
        "{swenv} python3 {basedir}/scripts/tier2_to_tier3.py --metadata {metadata} --detector {params.det} --ecal_file {input.ecal_database} --aoe_cal_file {input.aoe_database} {input.infile} {output}"
