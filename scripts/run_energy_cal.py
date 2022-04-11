import pygama.lh5 as lh5
import numpy as np
import os,json
import pathlib
import argparse

from pygama.pargen.ecal_th import energy_cal_th
from pygama.pargen.ecal_other_sources import energy_cal_ba,energy_cal_co,energy_cal_am



def run_energy_cal(files, det,measurement, cut_parameters ={"bl_mean":4, "bl_std":4, "pz_std":4},  plot_path=None):
    
    print(f'{len(files)} files found')

    energy_params = ['trapEmax_ctc', 'cuspEmax_ctc','zacEmax_ctc','trapEftp_ctc','cuspEftp_ctc','zacEftp_ctc']
        
    if measurement == "th_HS2_top_psa" or measurement == "th_HS2_lat_psa":
        out_dict = energy_cal_th(files, energy_params, plot_path = plot_path, cut_parameters= cut_parameters)
    elif measurement == "ba_HS4_top_dlt":
        out_dict = energy_cal_ba(files, energy_params, plot_path = plot_path, cut_parameters= cut_parameters)
    elif measurement == "co_HS5_top_dlt":
        out_dict = energy_cal_co(files, energy_params, plot_path = plot_path, cut_parameters= cut_parameters)
    elif measurement == "am_HS1_lat_ssh" or measurement == "am_HS6_top_dlt":
        out_dict = energy_cal_am(files, energy_params, plot_path = plot_path, cut_parameters= cut_parameters)
    return out_dict

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument("files", help="files", nargs='*',type=str)
    argparser.add_argument("--detector", help="detector", type=str, required=True)
    argparser.add_argument("--measurement", help="measurement", type=str, required=True)
    argparser.add_argument("--metadata", help="metadata path", type=str, required=True)
    argparser.add_argument("--plot_path", help="plot_path", type=str)
    argparser.add_argument("--save_path", help="save_path", type=str)
    argparser.add_argument("--th_cal_file", help="th_cal_file", type=str)
    args = argparser.parse_args()

    main_config = os.path.join(f"{args.metadata}", "main_config.json")

    with open(main_config, 'r') as f:
        config_dict = json.load(f)

    det_config=config_dict[args.detector]

    cut_parameters = det_config["default_cut_parameters"]
    
    with open(args.files[0]) as f:
        files = f.read().splitlines()
        files = sorted(files)[:10]
    out_dict = run_energy_cal(files, args.detector, args.measurement, cut_parameters = cut_parameters, plot_path = args.plot_path)

    with open(args.save_path,'w') as fp:
        pathlib.Path(os.path.dirname(args.save_path)).mkdir(parents=True, exist_ok=True)
        json.dump(out_dict,fp, indent=4)

    if args.th_cal_file is not None:
        pathlib.Path(os.path.dirname(args.th_cal_file)).mkdir(parents=True, exist_ok=True)
        with open(args.th_cal_file,'w') as fp:
            json.dump(out_dict,fp, indent=4)