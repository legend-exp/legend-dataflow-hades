# ruff: noqa: F821, T201

import glob
import json
import os

from util.FileKey import FileKey
from util.patterns import get_pattern_tier
from util.utils import convert_to_legend_timestamp

setup = snakemake.params.setup

file_selection = snakemake.wildcards.label[:3]
tier = snakemake.wildcards.tier
keypart = snakemake.wildcards.label[3:]  # .replace("all","")
search_pattern = snakemake.params.search_pattern

ignore_keys = []
if snakemake.params.configs:
    configs = snakemake.params.configs
    ignored_keyslist = os.path.join(configs, "ignore_keys.keylist")
    if os.path.isfile(ignored_keyslist):
        with open(ignored_keyslist) as f:
            ignore_keys = f.read().splitlines()
        ignore_keys = [
            key.split("#")[0].strip() if "#" in key else key.strip() for key in ignore_keys
        ]
    else:
        print("no ignore_keys.keylist file found")

    analysis_runs_file = os.path.join(configs, "analysis_runs.json")
    if os.path.isfile(analysis_runs_file):
        with open(analysis_runs_file) as f:
            analysis_runs = json.load(f)
    else:
        print("no analysis_runs file found")

key = FileKey.parse_keypart(keypart)

item_list = []
for item in key:
    _item = item  # .split("_") if "_" in item and item != "char_data" else item
    if isinstance(_item, list):
        item_list.append(_item)
    else:
        item_list.append([_item])

filekeys = []
for i in item_list[0]:
    for j in item_list[1]:
        for k in item_list[2]:
            for i2 in item_list[3]:
                for j2 in item_list[4]:
                    filekeys.append(FileKey(i, j, k, i2, j2))

filenames = []
fn_pattern = get_pattern_tier(setup, tier, check_in_cycle=False)
for key in filekeys:
    fn_glob_pattern = key.get_path_from_filekey(search_pattern)[0]
    print(fn_glob_pattern)
    files = glob.glob(fn_glob_pattern)
    for f in files:
        _key = FileKey.get_filekey_from_pattern(f, search_pattern)
        filename = FileKey.get_path_from_filekey(_key, fn_pattern)
        if len(_key.timestamp) == 13 and tier != "daq":
            tstamp = convert_to_legend_timestamp(_key.timestamp)
            filename = [filen.replace(_key.timestamp, tstamp) for filen in filename]
        if _key.name in ignore_keys:
            pass
        else:
            filenames += filename

filenames = sorted(filenames)

with open(snakemake.output[0], "w") as f:
    for fn in filenames:
        f.write(f"{fn}\n")
