import argparse
import json
import logging
import os
import pathlib
import pickle as pkl
import time
import warnings

os.environ["LGDO_CACHE"] = "false"
os.environ["LGDO_BOUNDSCHECK"] = "false"
os.environ["DSPEED_CACHE"] = "false"
os.environ["DSPEED_BOUNDSCHECK"] = "false"

import lgdo.lh5 as lh5
import numpy as np
import pygama.math.peak_fitting as pgf
import pygama.pargen.energy_optimisation as om
import sklearn.gaussian_process.kernels as ker
from legendmeta import LegendMetadata
from legendmeta.catalog import Props
from pygama.pargen.dsp_optimize import run_one_dsp

#
# The code below was copied from a locally developed version of Pygama in LNGS
#

log = logging.getLogger(__name__)
sto = lh5.LH5Store()

from iminuit import Minuit, cost, util
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import LogNorm
from scipy.optimize import curve_fit, minimize
from scipy.stats import chisquare, norm
from sklearn.exceptions import ConvergenceWarning
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel
from sklearn.utils._testing import ignore_warnings
import pygama.math.histogram as pgh
import pygama.math.peak_fitting as pgf  # noqa: F811
import pygama.pargen.cuts as cts
import pygama.pargen.dsp_optimize as opt
import pygama.pargen.energy_cal as pgc

def get_wf_indexes(sorted_indexs, n_events):
    out_list = []
    if isinstance(n_events, list):
        for i in range(len(n_events)):
            new_list = []
            for idx, entry in enumerate(sorted_indexs):
                if (entry >= np.sum(n_events[:i])) and (
                    entry < np.sum(n_events[: i + 1])
                ):
                    new_list.append(idx)
            out_list.append(new_list)
    else:
        for i in range(int(len(sorted_indexs) / n_events)):
            new_list = []
            for idx, entry in enumerate(sorted_indexs):
                if (entry >= i * n_events) and (entry < (i + 1) * n_events):
                    new_list.append(idx)
            out_list.append(new_list)
    return out_list

def event_selection(
    raw_files,
    lh5_path,
    dsp_config,
    db_dict,
    peaks_keV,
    peak_idxs,
    kev_widths,
    cut_parameters=None,
    pulser_mask=None,
    energy_parameter="trapTmax",
    wf_field: str = "waveform",  # noqa: ARG001 # the variable was never used
    n_events=10000,
    threshold=1000,
    initial_energy="daqenergy",
    check_pulser=True,
):
    if cut_parameters is None:
        cut_parameters = {"bl_mean": 4, "bl_std": 4, "pz_std": 4}
    if not isinstance(peak_idxs, list):
        peak_idxs = [peak_idxs]
    if not isinstance(kev_widths, list):
        kev_widths = [kev_widths]

    if lh5_path[-1] != "/":
        lh5_path +="/"

    raw_fields = [field.replace(lh5_path, "") for field in lh5.ls(raw_files[0], lh5_path)]
    initial_fields = cts.get_keys(
        raw_fields, [initial_energy]
    )
    initial_fields += ["timestamp"]

    df = lh5.read_as(lh5_path, raw_files, "pd", field_mask=initial_fields)  # noqa: PD901
    df["initial_energy"] = df.eval(initial_energy)

    if pulser_mask is None and check_pulser is True:
        pulser_props = cts.find_pulser_properties(df, energy="initial_energy")
        if len(pulser_props) > 0:
            final_mask = None
            for entry in pulser_props:
                e_cut = (df.initial_energy.values < entry[0] + entry[1]) & (
                    df.initial_energy.values > entry[0] - entry[1]
                )
                final_mask = e_cut if final_mask is None else final_mask | e_cut
            ids = final_mask
            log.debug(f"pulser found: {pulser_props}")
        else:
            log.debug("no_pulser")
            ids = np.zeros(len(df.initial_energy.values), dtype=bool)
        # Get events around peak using raw file values
    elif pulser_mask is not None:
        ids = pulser_mask
    else:
        ids = np.zeros(len(df.initial_energy.values), dtype=bool)

    initial_mask = (df["initial_energy"] > threshold) & (~ids)
    rough_energy = np.array(df["initial_energy"])[initial_mask]
    initial_idxs = np.where(initial_mask)[0]

    guess_keV = 2620 / np.nanpercentile(rough_energy, 99)
    Euc_min = threshold / guess_keV * 0.6
    Euc_max = 2620 / guess_keV * 1.1
    dEuc = 1  # / guess_keV
    hist, bins, var = pgh.get_hist(rough_energy, range=(Euc_min, Euc_max), dx=dEuc)
    detected_peaks_locs, detected_peaks_keV, roughpars = pgc.hpge_find_E_peaks(
        hist,
        bins,
        var,
        np.array([238.632, 583.191, 727.330, 860.564, 1620.5, 2103.53, 2614.553]),
    )
    log.debug(f"detected {detected_peaks_keV} keV peaks at {detected_peaks_locs}")

    masks = []
    for peak_idx in peak_idxs:
        peak = peaks_keV[peak_idx]
        kev_width = kev_widths[peak_idx]
        try:
            if peak not in detected_peaks_keV:
                raise ValueError
            detected_peak_idx = np.where(detected_peaks_keV == peak)[0]
            peak_loc = detected_peaks_locs[detected_peak_idx]
            log.info(f"{peak} peak found at {peak_loc}")
            rough_adc_to_kev = roughpars[0]
            e_lower_lim = peak_loc - (1.1 * kev_width[0]) / rough_adc_to_kev
            e_upper_lim = peak_loc + (1.1 * kev_width[1]) / rough_adc_to_kev
        except ValueError:
            log.debug(f"{peak} peak not found attempting to use rough parameters")
            peak_loc = (peak - roughpars[1]) / roughpars[0]
            rough_adc_to_kev = roughpars[0]
            e_lower_lim = peak_loc - (1.5 * kev_width[0]) / rough_adc_to_kev
            e_upper_lim = peak_loc + (1.5 * kev_width[1]) / rough_adc_to_kev
        log.debug(f"lower_lim:{e_lower_lim}, upper_lim:{e_upper_lim}")
        e_mask = (rough_energy > e_lower_lim) & (rough_energy < e_upper_lim)
        e_idxs = initial_idxs[e_mask][: int(2.5 * n_events)]
        masks.append(e_idxs)
        log.debug(f"{len(e_idxs)} events found in energy range for {peak}")

    idx_list_lens = [len(masks[peak_idx]) for peak_idx in peak_idxs]

    sort_index = np.argsort(np.concatenate(masks))
    idx_list = get_wf_indexes(sort_index, idx_list_lens)
    idxs = np.array(sorted(np.concatenate(masks)))

    input_data = sto.read(f"{lh5_path}", raw_files, idx=idxs, n_rows=len(idxs))[0]

    if isinstance(dsp_config, str):
        with open(dsp_config) as r:
            dsp_config = json.load(r)

    dsp_config["outputs"] = cts.get_keys(  # noqa: RUF005 # Leaving the error
                                           # here for now because I have no idea
                                           # what the code does
        dsp_config["outputs"], list(cut_parameters)
    ) + [energy_parameter]

    log.debug("Processing data")
    tb_data = opt.run_one_dsp(input_data, dsp_config, db_dict=db_dict)

    cut_dict = cts.generate_cuts(tb_data, cut_parameters)
    log.debug(f"Cuts are: {cut_dict}")
    log.debug("Loaded Cuts")
    ct_mask = cts.get_cut_indexes(tb_data, cut_dict)

    final_events = []
    out_events = []
    for peak_idx in peak_idxs:
        peak = peaks_keV[peak_idx]
        kev_width = kev_widths[peak_idx]

        peak_ids = np.array(idx_list[peak_idx])
        peak_ct_mask = ct_mask[peak_ids]
        peak_ids = peak_ids[peak_ct_mask]

        energy = tb_data[energy_parameter].nda[peak_ids]

        hist, bins, var = pgh.get_hist(
            energy, range=(int(threshold), int(np.nanmax(energy))), dx=1
        )
        peak_loc = pgh.get_bin_centers(bins)[np.nanargmax(hist)]
        rough_adc_to_kev = peak / peak_loc

        e_lower_lim = peak_loc - (1.5 * kev_width[0]) / rough_adc_to_kev
        e_upper_lim = peak_loc + (1.5 * kev_width[1]) / rough_adc_to_kev

        e_ranges = (int(peak_loc - e_lower_lim), int(e_upper_lim - peak_loc))
        (
            params,
            errors,
            covs,
            bins,
            ranges,
            p_val,
            valid_pks,
            pk_funcs,
        ) = pgc.hpge_fit_E_peaks(
            energy,
            [peak_loc],
            [e_ranges],
            n_bins=(np.nanmax(energy) - np.nanmin(energy)) // 1,
            uncal_is_int=True,
        )
        if params[0] is None or np.isnan(params[0]).any():
            log.debug("Fit failed, using max guess")
            hist, bins, var = pgh.get_hist(
                energy, range=(int(e_lower_lim), int(e_upper_lim)), dx=1
            )
            params = [[0, pgh.get_bin_centers(bins)[np.nanargmax(hist)], 0, 0, 0, 0]]
        updated_adc_to_kev = peak / params[0][1]
        e_lower_lim = params[0][1] - (kev_width[0]) / updated_adc_to_kev
        e_upper_lim = params[0][1] + (kev_width[1]) / updated_adc_to_kev
        log.info(f"lower lim is :{e_lower_lim}, upper lim is {e_upper_lim}")
        final_mask = (energy > e_lower_lim) & (energy < e_upper_lim)
        final_events.append(peak_ids[final_mask][:n_events])
        out_events.append(idxs[final_events[-1]])
        log.info(f"{len(peak_ids[final_mask][:n_events])} passed selections for {peak}")
        if len(peak_ids[final_mask]) < 0.5 * n_events:
            log.warning("Less than half number of specified events found")
        elif len(peak_ids[final_mask]) < 0.1 * n_events:
            log.error("Less than 10% number of specified events found")
    out_events = np.unique(np.concatenate(out_events))
    sort_index = np.argsort(np.concatenate(final_events))
    idx_list = get_wf_indexes(sort_index, [len(mask) for mask in final_events])
    return out_events, idx_list

#
# The code above was copied from a locally developed version of Pygama in LNGS
#

warnings.filterwarnings(action="ignore", category=RuntimeWarning)

argparser = argparse.ArgumentParser()
argparser.add_argument("--raw_filelist", help="raw_filelist", type=str, nargs="*")
argparser.add_argument("--decay_const", help="decay_const", type=str, required=True)
argparser.add_argument("--configs", help="configs", type=str, required=True)
argparser.add_argument("--inplots", help="in_plot_path", type=str)

argparser.add_argument("--log", help="log_file", type=str)

argparser.add_argument("--detector", help="detector", type=str, required=True)
argparser.add_argument("--timestamp", help="timestamp", type=str, required=True)
argparser.add_argument("--measurement", help="measurement", type=str, required=True)

argparser.add_argument("--final_dsp_pars", help="final_dsp_pars", type=str, required=True)
argparser.add_argument("--out_obj", help="out_obj", type=str)
argparser.add_argument("--plot_path", help="plot_path", type=str)


argparser.add_argument("--plot_save_path", help="plot_save_path", type=str, required=False)
args = argparser.parse_args()

logging.basicConfig(level=logging.DEBUG, filename=args.log, filemode="w")
logging.getLogger("numba").setLevel(logging.INFO)
logging.getLogger("parse").setLevel(logging.INFO)
logging.getLogger("lgdo").setLevel(logging.INFO)
logging.getLogger("h5py").setLevel(logging.INFO)
logging.getLogger("matplotlib").setLevel(logging.INFO)
logging.getLogger("dspeed").setLevel(logging.INFO)


log = logging.getLogger(__name__)
sto = lh5.LH5Store()

t0 = time.time()

# The commented code below contains a undefined symbol `input_file`. That
# branch has never been run so there has no bug report yet. Ruff found it so I
# commented it out.

#if isinstance(args.raw_filelist, list) and args.raw_filelist[0].split(".")[-1] == "filelist":
#    files = args.raw_filelist[0]
#    with open(input_file) as f:
#        files = f.read().splitlines()
#else:
#    files = args.raw_filelist

files = args.raw_filelist

conf = LegendMetadata(path=args.configs)
configs = conf.on(args.timestamp)
dsp_config = configs["snakemake_rules"]["pars_dsp_eopt"]["inputs"]["processing_chain"][
    args.detector
]
opt_json = configs["snakemake_rules"]["pars_dsp_eopt"]["inputs"]["optimiser_config"][args.detector]

opt_dict = Props.read_from(opt_json)
db_dict = Props.read_from(args.decay_const)

if opt_dict.pop("run_eopt") is True:

    raw_files = sorted(files)

    peaks_keV = np.array(opt_dict["peaks"])
    kev_widths = [tuple(kev_width) for kev_width in opt_dict["kev_widths"]]

    kwarg_dicts_cusp = []
    kwarg_dicts_trap = []
    kwarg_dicts_zac = []
    for peak in peaks_keV:
        peak_idx = np.where(peaks_keV == peak)[0][0]
        kev_width = kev_widths[peak_idx]
        if peak == 238.632:
            kwarg_dicts_cusp.append(
                {
                    "parameter": "cuspEmax",
                    "func": pgf.extended_gauss_step_pdf,
                    "gof_func": pgf.gauss_step_pdf,
                    "peak": peak,
                    "kev_width": kev_width,
                }
            )
            kwarg_dicts_zac.append(
                {
                    "parameter": "zacEmax",
                    "func": pgf.extended_gauss_step_pdf,
                    "gof_func": pgf.gauss_step_pdf,
                    "peak": peak,
                    "kev_width": kev_width,
                }
            )
            kwarg_dicts_trap.append(
                {
                    "parameter": "trapEmax",
                    "func": pgf.extended_gauss_step_pdf,
                    "gof_func": pgf.gauss_step_pdf,
                    "peak": peak,
                    "kev_width": kev_width,
                }
            )
        else:
            kwarg_dicts_cusp.append(
                {
                    "parameter": "cuspEmax",
                    "func": pgf.extended_radford_pdf,
                    "gof_func": pgf.radford_pdf,
                    "peak": peak,
                    "kev_width": kev_width,
                }
            )
            kwarg_dicts_zac.append(
                {
                    "parameter": "zacEmax",
                    "func": pgf.extended_radford_pdf,
                    "gof_func": pgf.radford_pdf,
                    "peak": peak,
                    "kev_width": kev_width,
                }
            )
            kwarg_dicts_trap.append(
                {
                    "parameter": "trapEmax",
                    "func": pgf.extended_radford_pdf,
                    "gof_func": pgf.radford_pdf,
                    "peak": peak,
                    "kev_width": kev_width,
                }
            )

    idx_events, idx_list = event_selection(
        raw_files,
        "char_data/raw",
        dsp_config,
        db_dict,
        peaks_keV,
        np.arange(0, len(peaks_keV), 1).tolist(),
        kev_widths,
        cut_parameters=opt_dict["cut_parameters"],
        n_events=opt_dict["n_events"],
        threshold=opt_dict["threshold"],
        wf_field=opt_dict["wf_field"],
        initial_energy=opt_dict["initial_energy"],
        check_pulser=opt_dict["check_pulser"],
    )

    tb_data = sto.read(
        "char_data/raw",
        raw_files,
        idx=idx_events,
        n_rows=opt_dict["n_events"],
    )[0]

    t1 = time.time()
    log.info(f"Data Loaded in {(t1-t0)/60} minutes")

    if isinstance(dsp_config, str):
        dsp_config = Props.read_from(dsp_config)

    init_data = run_one_dsp(tb_data, dsp_config, db_dict=db_dict, verbosity=0)
    full_dt = (init_data["tp_99"].nda - init_data["tp_0_est"].nda)[idx_list[-1]]
    flat_val = np.ceil(1.1 * np.nanpercentile(full_dt, 99) / 100) / 10
    if flat_val < 1.0:
        flat_val = 1.0
    elif flat_val > 4:
        flat_val = 4
    flat_val = f"{flat_val}*us"

    db_dict["cusp"] = {"flat": flat_val}
    db_dict["zac"] = {"flat": flat_val}
    db_dict["etrap"] = {"flat": flat_val}

    tb_data.add_column("dt_eff", init_data["dt_eff"])

    dsp_config["processors"].pop("dt_eff")

    dsp_config["outputs"] = ["zacEmax", "cuspEmax", "trapEmax", "dt_eff"]

    kwarg_dict = [
        {
            "peak_dicts": kwarg_dicts_cusp,
            "ctc_param": "QDrift",
            "idx_list": idx_list,
            "peaks_keV": peaks_keV,
        },
        {
            "peak_dicts": kwarg_dicts_zac,
            "ctc_param": "QDrift",
            "idx_list": idx_list,
            "peaks_keV": peaks_keV,
        },
        {
            "peak_dicts": kwarg_dicts_trap,
            "ctc_param": "QDrift",
            "idx_list": idx_list,
            "peaks_keV": peaks_keV,
        },
    ]

    fom = eval(opt_dict["fom"])

    sample_x = np.array(opt_dict["initial_samples"])

    results_cusp = []
    results_zac = []
    results_trap = []

    sample_y_cusp = []
    sample_y_zac = []
    sample_y_trap = []

    err_y_cusp = []
    err_y_zac = []
    err_y_trap = []

    for i, x in enumerate(sample_x):
        db_dict["cusp"]["sigma"] = f"{x[0]}*us"
        db_dict["zac"]["sigma"] = f"{x[0]}*us"
        db_dict["etrap"]["rise"] = f"{x[0]}*us"

        log.info(f"Initialising values {i+1} : {db_dict}")

        tb_out = run_one_dsp(tb_data, dsp_config, db_dict=db_dict, verbosity=0)

        res = fom(tb_out, kwarg_dict[0])
        results_cusp.append(res)
        sample_y_cusp.append(res["y_val"])
        err_y_cusp.append(res["y_err"])

        res = fom(tb_out, kwarg_dict[1])
        results_zac.append(res)
        sample_y_zac.append(res["y_val"])
        err_y_zac.append(res["y_err"])

        res = fom(tb_out, kwarg_dict[2])
        results_trap.append(res)
        sample_y_trap.append(res["y_val"])
        err_y_trap.append(res["y_err"])

        log.info(f"{i+1} Finished")

    if np.isnan(sample_y_cusp).all():
        max_cusp = opt_dict["nan_default"]
    else:
        max_cusp = np.ceil(np.nanmax(sample_y_cusp) * 2)
    if np.isnan(sample_y_zac).all():
        max_zac = opt_dict["nan_default"]
    else:
        max_zac = np.ceil(np.nanmax(sample_y_zac) * 2)
    if np.isnan(sample_y_trap).all():
        max_trap = opt_dict["nan_default"]
    else:
        max_trap = np.ceil(np.nanmax(sample_y_trap) * 2)

    nan_vals = [max_cusp, max_zac, max_trap]

    for i in range(len(sample_x)):
        if np.isnan(sample_y_cusp[i]):
            results_cusp[i]["y_val"] = max_cusp
            sample_y_cusp[i] = max_cusp

        if np.isnan(sample_y_zac[i]):
            results_zac[i]["y_val"] = max_zac
            sample_y_zac[i] = max_zac

        if np.isnan(sample_y_trap[i]):
            results_trap[i]["y_val"] = max_trap
            sample_y_trap[i] = max_trap

    kernel = (
        ker.ConstantKernel(2.0, constant_value_bounds="fixed")
        + 1.0 * ker.RBF(1.0, length_scale_bounds=[0.5, 2.5])
        + ker.WhiteKernel(noise_level=0.1, noise_level_bounds=(1e-5, 1e1))
    )

    bopt_cusp = om.BayesianOptimizer(
        acq_func=opt_dict["acq_func"], batch_size=opt_dict["batch_size"], kernel=kernel
    )
    bopt_cusp.lambda_param = 1
    bopt_cusp.add_dimension("cusp", "sigma", 1, 13, 2, "us")

    bopt_zac = om.BayesianOptimizer(
        acq_func=opt_dict["acq_func"], batch_size=opt_dict["batch_size"], kernel=kernel
    )
    bopt_zac.lambda_param = 1
    bopt_zac.add_dimension("zac", "sigma", 1, 13, 2, "us")

    bopt_trap = om.BayesianOptimizer(
        acq_func=opt_dict["acq_func"], batch_size=opt_dict["batch_size"], kernel=kernel
    )
    bopt_trap.lambda_param = 1
    bopt_trap.add_dimension("etrap", "rise", 1, 13, 2, "us")

    bopt_cusp.add_initial_values(x_init=sample_x, y_init=sample_y_cusp, yerr_init=err_y_cusp)
    bopt_zac.add_initial_values(x_init=sample_x, y_init=sample_y_zac, yerr_init=err_y_zac)
    bopt_trap.add_initial_values(x_init=sample_x, y_init=sample_y_trap, yerr_init=err_y_trap)

    best_idx = np.nanargmin(sample_y_cusp)
    bopt_cusp.optimal_results = results_cusp[best_idx]
    bopt_cusp.optimal_x = sample_x[best_idx]

    best_idx = np.nanargmin(sample_y_zac)
    bopt_zac.optimal_results = results_zac[best_idx]
    bopt_zac.optimal_x = sample_x[best_idx]

    best_idx = np.nanargmin(sample_y_trap)
    bopt_trap.optimal_results = results_trap[best_idx]
    bopt_trap.optimal_x = sample_x[best_idx]

    optimisers = [bopt_cusp, bopt_zac, bopt_trap]

    out_param_dict, out_results_list = om.run_optimisation(
        tb_data,
        dsp_config,
        [fom],
        optimisers,
        fom_kwargs=kwarg_dict,
        db_dict=db_dict,
        nan_val=nan_vals,
        n_iter=opt_dict["n_iter"],
    )

    Props.add_to(db_dict, out_param_dict)

    # db_dict.update(out_param_dict)

    t2 = time.time()
    log.info(f"Optimiser finished in {(t2-t1)/60} minutes")

    out_alpha_dict = {}
    out_alpha_dict["cuspEmax_ctc"] = {
        "expression": "cuspEmax*(1+dt_eff*a)",
        "parameters": {"a": round(bopt_cusp.optimal_results["alpha"], 9)},
    }

    out_alpha_dict["cuspEftp_ctc"] = {
        "expression": "cuspEftp*(1+dt_eff*a)",
        "parameters": {"a": round(bopt_cusp.optimal_results["alpha"], 9)},
    }

    out_alpha_dict["zacEmax_ctc"] = {
        "expression": "zacEmax*(1+dt_eff*a)",
        "parameters": {"a": round(bopt_zac.optimal_results["alpha"], 9)},
    }

    out_alpha_dict["zacEftp_ctc"] = {
        "expression": "zacEftp*(1+dt_eff*a)",
        "parameters": {"a": round(bopt_zac.optimal_results["alpha"], 9)},
    }

    out_alpha_dict["trapEmax_ctc"] = {
        "expression": "trapEmax*(1+dt_eff*a)",
        "parameters": {"a": round(bopt_trap.optimal_results["alpha"], 9)},
    }

    out_alpha_dict["trapEftp_ctc"] = {
        "expression": "trapEftp*(1+dt_eff*a)",
        "parameters": {"a": round(bopt_trap.optimal_results["alpha"], 9)},
    }

    db_dict.update({"ctc_params": out_alpha_dict})

    pathlib.Path(os.path.dirname(args.out_obj)).mkdir(parents=True, exist_ok=True)
    with open(args.out_obj, "wb") as f:
        pkl.dump(optimisers, f)

else:
    pathlib.Path(args.out_obj).touch()

pathlib.Path(os.path.dirname(args.final_dsp_pars)).mkdir(parents=True, exist_ok=True)
with open(args.final_dsp_pars, "w") as w:
    json.dump(db_dict, w, indent=4)

if args.plot_path:
    if args.inplots:
        with open(args.inplots, "rb") as r:
            plot_dict = pkl.load(r)
    else:
        plot_dict = {}

    plot_dict["trap_optimisation"] = {
        "kernel_space": bopt_trap.plot(init_samples=sample_x),
        "acq_space": bopt_trap.plot_acq(init_samples=sample_x),
    }

    plot_dict["cusp_optimisation"] = {
        "kernel_space": bopt_cusp.plot(init_samples=sample_x),
        "acq_space": bopt_cusp.plot_acq(init_samples=sample_x),
    }

    plot_dict["zac_optimisation"] = {
        "kernel_space": bopt_zac.plot(init_samples=sample_x),
        "acq_space": bopt_zac.plot_acq(init_samples=sample_x),
    }

    pathlib.Path(os.path.dirname(args.plot_path)).mkdir(parents=True, exist_ok=True)
    with open(args.plot_path, "wb") as w:
        pkl.dump(plot_dict, w, protocol=pkl.HIGHEST_PROTOCOL)
