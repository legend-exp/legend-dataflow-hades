import snakemake as smk
import re
import os
import shutil
import copy
import string

# For testing/debugging, use
# from scripts.utils import *
# import snakemake as smk
# setup = smk.load_configfile("config.json")["setups"]["l200hades"]

def origdata_path(setup):
    return setup["paths"]["orig"]

def gendata_path(setup):
    return setup["paths"]["gen"]

def metadata_path(setup):
    return setup["paths"]["meta"]


def runcmd(setup):
    if "software" in setup:
        if "venv" in setup["software"]:
            venv_path = setup["software"]["venv"]["path"]
            venv_name = setup["software"]["venv"]["name"]
            return f"{venv_path} {venv_name}"
        else:
            return "exec"
    else:
        return "exec"


def key_pattern():
    return "{detector}-{measurement}-run{run}-{timestamp}"

def tier_fn_pattern(setup, tier):
    if tier == "tier0":
        return os.path.join(f"{origdata_path(setup)}", "{detector}", "tier0", "{measurement}", "char_data-{detector}-{measurement}-run{run}-{timestamp}.fcio")
    else:
        return os.path.join(f"{gendata_path(setup)}", "{detector}", tier, "{measurement}", "char_data-{detector}-{measurement}-run{run}-{timestamp}_" + tier + ".lh5")


def parse_keypart(keypart):
    keypart_rx = re.compile('(-(?P<detector>[^-]+)(\\-(?P<measurement>[^-]+)(\\-(?P<run>[^-]+)(\\-(?P<timestamp>[^-]+))?)?)?)?$')
    d = keypart_rx.match(keypart).groupdict()
    for key in d:
        if d[key] is None:
            d[key] = "*"
    return d


def tier_files(setup, dataset_file, tier):
    key_pattern_rx = re.compile(smk.io.regex(key_pattern()))
    fn_pattern = tier_fn_pattern(setup, tier)
    files = []
    with open(dataset_file) as f:
        for line in f:
            d = key_pattern_rx.match(line.strip()).groupdict()
            tier_filename = smk.io.expand(fn_pattern, detector = d["detector"], measurement = d["measurement"], run = d["run"], timestamp = d["timestamp"])[0]
            files.append(tier_filename)
    return files


def subst_vars_impl(x, var_values, ignore_missing = False):
    if isinstance(x, str):
        if '$' in x:
            if ignore_missing:
                return string.Template(x).safe_substitute(var_values)
            else:
                return string.Template(x).substitute(var_values)
        else:
            return x
    if isinstance(x, dict):
        for key in x:
            value = x[key]
            new_value = subst_vars_impl(value, var_values, ignore_missing)
            if new_value is not value:
                x[key] = new_value
        return x
    if isinstance(x, list):
        for i in range(len(x)):
            value = x[i]
            new_value = subst_vars_impl(value, var_values, ignore_missing)
            if new_value is not value:
                x[i] = new_value
        return x
    else:
        return x

def subst_vars(props, var_values = {}, use_env = False, ignore_missing = False):
    combined_var_values = var_values
    if use_env:
        combined_var_values = {k: v for k, v in iter(os.environ.items())}
        combined_var_values.update(copy.copy(var_values))
    subst_vars_impl(props, combined_var_values, ignore_missing)


def subst_vars_in_snakemake_config(workflow, config):
    config_filename = workflow.overwrite_configfiles[0] # ToDo: Better way of handling this?
    subst_vars(
        config,
        var_values = {'_': os.path.dirname(config_filename)},
        use_env = True, ignore_missing = False
    )
