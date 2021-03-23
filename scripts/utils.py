import snakemake as smk
import re
import shutil

# For testing/debugging, use
# from scripts.utils import *
# import snakemake as smk
# setup = smk.load_configfile("config.json")["setups"]["l200hades"]

def origdata_path(setup):
    return setup["data"]["orig"]

def gendata_path(setup):
    return setup["data"]["gen"]

def metadata_path(setup):
    return setup["data"]["meta"]


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
        return f"{origdata_path(setup)}/" + "{detector}/tier0/{measurement}/char_data-{detector}-{measurement}-run{run}-{timestamp}.fcio"
    else:
        return f"{gendata_path(setup)}/" + "{detector}/" + tier + "/{measurement}/char_data-{detector}-{measurement}-run{run}-{timestamp}_" + tier +".lh5"


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
