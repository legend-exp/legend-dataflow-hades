import json, os
import pygama.genpar_tmp.optimiser_macro as om
import pygama.analysis.peak_fitting as pgf
from collections import OrderedDict
import argparse
import pathlib
import pickle as pkl
import numpy as np

argparser = argparse.ArgumentParser()
argparser.add_argument("files", help="files", nargs='*',type=str)
argparser.add_argument("--db_dict_path", help="db_dict_path", type=str, required=True)
argparser.add_argument("--metadata", help="metadata", type=str, required=True)
argparser.add_argument("--qbb_grid_path", help="qbb_grid_path", type=str)
argparser.add_argument("--fwhm_path", help="fwhm_path", type=str)
argparser.add_argument("--raw_filelist", help="raw_filelist", type=str)
argparser.add_argument("--tau_db_dict_path", help="db_dict_path", type=str, required=True)
argparser.add_argument("--plot_save_path", help="plot_save_path", type=str, required=False)
args = argparser.parse_args()
    
o_config = os.path.join(f"{args.metadata}", "opt_config.json")
with open(o_config, 'r') as o:
    opt_dict = json.load(o)

if args.plot_save_path:
    energy_db_dict, fwhm_dict, qbb_grid = om.get_filter_params(args.files, opt_dict, save_path = args.plot_save_path)
else:
    energy_db_dict, fwhm_dict, qbb_grid = om.get_filter_params(args.files, opt_dict)



# FTP optimisation

with open(args.raw_filelist) as f:
    file_list = f.read().splitlines()

raw_file = sorted(om.run_splitter(file_list), key=len)[-1]

f_config = os.path.join(f"{args.metadata}", "config_dsp.json")
with open(f_config, 'r') as config_file:
    config_dict = json.load(config_file, object_pairs_hook=OrderedDict)

with open(args.tau_db_dict_path, 'r') as t:
    db_dict = json.load(t)

db_dict.update(energy_db_dict)

wf_idxs = om.event_selection(raw_file, config_dict, db_dict, np.array([238.632,   583.191, 727.330, 860.564, 1620.5, 2614.553]), 5, (70,70))

parameters=[ 'trapEftp_ctc', 'cuspEftp_ctc', 'zacEftp_ctc']

o_config = os.path.join(f"{args.metadata}", "opt_config_ftp.json")
with open(o_config, 'r') as o:
    opt_dict = json.load(o)
print('Loaded configs')

out_grids = om.run_optimisation_multiprocessed(raw_file, opt_dict, config_dict, db_dict = db_dict, 
            fom = om.fom_FWHM_fit, cuts = wf_idxs, n_events=10000,
            processes=30, parameter=parameters, func=pgf.extended_radford_pdf, gof_func=pgf.radford_pdf,
            peak=2614.553, kev_width=(70,70)) #kev_width=(50,50) pgf.radford_peak

ftp_dict = {}
for i in range(len(out_grids)):
    values = np.array([out_grids[i][j]['fwhm_o_max'] for j in range(len(out_grids[i]))])
    out_index = np.nanargmin(values)
    db_dict_entry1 = list(opt_dict[i].keys())[0]
    db_dict_entry2 = list(opt_dict[i][db_dict_entry1].keys())[0]
    opt_d = opt_dict[i][db_dict_entry1][db_dict_entry2]
    opt_vals = np.linspace(opt_d['start'], opt_d['end'], opt_d['frequency'])
    #try:
    #    opt_vals = [ f'{val:.2f}*{opt_d["unit"]}' for val in opt_vals]
    #except:
    opt_vals = [ f'{val:.2f}' for val in opt_vals]
    ftp_dict[db_dict_entry1] = {db_dict_entry2:opt_vals[out_index]}

for key in list(db_dict.keys()):
    try:
        db_dict[key].update(ftp_dict[key]) 
    except:
        pass

#Save db dict values
with open(args.db_dict_path, 'w') as w:
    json.dump(db_dict, w, indent=4)
    
with open(args.fwhm_path, 'w') as fp:
    json.dump(fwhm_dict, fp, indent=4)

with open(args.qbb_grid_path,"wb") as f:
    pkl.dump(qbb_grid,f)
