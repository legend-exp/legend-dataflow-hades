import snakemake as smk
import os, re, glob

from utils import *

keypart = snakemake.wildcards.keypart
setup = snakemake.params.setup

d = parse_keypart(keypart)


tier0_pattern = tier_fn_pattern(setup, "tier0")
tier0_pattern_rx = re.compile(smk.io.regex(tier0_pattern))
fn_glob_pattern = smk.io.expand(tier0_pattern, detector = d["detector"], measurement = d["measurement"], run = d["run"], timestamp = d["timestamp"])[0]

files = glob.glob(fn_glob_pattern)

keys = []
for f in files:
    d = tier0_pattern_rx.match(f).groupdict()
    key = smk.io.expand(f"{key_pattern()}", detector = d["detector"], measurement = d["measurement"], run = d["run"], timestamp = d["timestamp"])[0]
    keys.append(key)

with open(snakemake.output[0], 'w') as f:
    for key in keys:
        f.write(f"{key}\n")
