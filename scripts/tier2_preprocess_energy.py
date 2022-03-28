import json, os
import pygama.pargen.energy_optimising as om
import pygama.analysis.peak_fitting as pgf
from collections import OrderedDict
import pickle
import argparse
import pathlib
import time
import numpy as np

argparser = argparse.ArgumentParser()
argparser.add_argument("raw_files", help="raw_files", type=str)
#argparser.add_argument("raw_files", help="files", nargs='*',type=str)
argparser.add_argument("--output_path", help="output_path", type=str)
argparser.add_argument("--metadata", help="metadata", type=str, required=True)
argparser.add_argument("--db_dict_path", help="db_dict_path", type=str, required=True)
argparser.add_argument("--peak", help="peak", type=float, required=True)
args = argparser.parse_args()

peaks_keV = np.array([238.632,   583.191, 727.330, 860.564, 1620.5, 2614.553])
#kev_widths = [(10,10), (25,40), (25,40),(25,40),(25,40), (50,50)]
#funcs = [pgf.gauss_step, pgf.radford_peak, pgf.radford_peak,pgf.radford_peak,pgf.radford_peak, pgf.radford_peak]

if args.peak == 2614.553:
        kev_widths = (70, 70)
        n_processes = 19
        func = pgf.extended_radford_pdf
        gof_func = pgf.radford_pdf
elif args.peak == 238.632:
    kev_widths = (10,10)
    n_processes = 5
    func = pgf.extended_gauss_step_pdf
    gof_func = pgf.gauss_step_pdf
else:
    kev_widths = (25,55)
    n_processes = 19
    func = pgf.extended_radford_pdf
    gof_func = pgf.radford_pdf
    
peak_idx = np.where(peaks_keV == args.peak)[0][0]

with open(args.raw_files) as f:
    files = f.read().splitlines()

raw_files = sorted(om.run_splitter(files), key=len)[-1]


f_config = os.path.join(f"{args.metadata}", "config_dsp.json")
with open(f_config, 'r') as config_file:
    config_dict = json.load(config_file, object_pairs_hook=OrderedDict)

with open(args.db_dict_path, 'r') as t:
    db_dict = json.load(t)

wf_idxs = om.event_selection(raw_files, config_dict, db_dict, peaks_keV, peak_idx, kev_widths)

o_config = os.path.join(f"{args.metadata}", "opt_config.json")
with open(o_config, 'r') as o:
    opt_dict = json.load(o)

print('Loaded configs')

parameters=['zacEmax', 'trapEmax', 'cuspEmax']

t0 = time.time()

grid_out = om.run_optimisation_multiprocessed(raw_files, opt_dict, config_dict, db_dict = db_dict, 
            fom = om.fom_all_fit, cuts = wf_idxs, n_events=10000,
            processes=n_processes, parameter=parameters, func=func, gof_func = gof_func,
            peak=args.peak, kev_width=kev_widths) #
    
t1 = time.time()

print(f'Calculated Grid in {(t1-t0)/60} minutes')

save_dict = {}
for i,param in enumerate(parameters):
    save_dict[param] = grid_out[i]
    
pathlib.Path(os.path.dirname(args.output_path)).mkdir(parents=True, exist_ok=True)
with open(args.output_path,"wb") as f:
    pickle.dump(save_dict,f)
