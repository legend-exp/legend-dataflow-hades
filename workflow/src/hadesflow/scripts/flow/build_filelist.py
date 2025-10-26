# ruff: noqa: I002

import glob
from pathlib import Path

from dbetto import Props

import hadesflow.methods.patterns as patt
from hadesflow.methods import FileKey
from hadesflow.methods.utils import convert_to_daq_run


def get_ignored_keys(ignore_keys_file):
    """
    This function reads in the ignore_keys and analysis_runs files and returns the dictionaries
    """
    ignore_keys = []

    if ignore_keys_file is not None:
        if Path(ignore_keys_file).is_file():
            if Path(ignore_keys_file).suffix in (".json", ".yaml", ".yml"):
                ignore_keys = Props.read_from(ignore_keys_file)
            elif Path(ignore_keys_file).suffix == ".keylist":
                with Path(ignore_keys_file).open() as f:
                    ignore_keys = f.read().splitlines()
                ignore_keys = [  # remove any comments in the keylist
                    key.split("#")[0].strip() if "#" in key else key.strip() for key in ignore_keys
                ]

            else:
                msg = "ignore_keys_file file not in json, yaml or keylist format"
                raise ValueError(msg)

        else:
            msg = f"no ignore_keys file found: {ignore_keys_file}"
            raise ValueError(msg)

    return ignore_keys


def get_keys(
    keypart,
):
    key = FileKey.parse_keypart(keypart)

    item_list = []
    for name, item in key.items():
        if name != "measurement":
            _item = item.split("_") if "_" in item and item != "char_data" else [item]
        else:
            _item = [item]

        if name == "run":
            _item += [convert_to_daq_run(i) for i in _item]

        if isinstance(_item, list):
            item_list.append(_item)

    filekeys = []
    for i in item_list[0]:
        for j in item_list[1]:
            for k in item_list[2]:
                for i2 in item_list[3]:
                    for j2 in item_list[4]:
                        filekeys.append(FileKey(i, j, k, i2, j2))
    return filekeys


def get_pattern(config, tier):
    """
    Helper function to get the search pattern for the given tier,
    some tiers such as skm need to refer to a different pattern when looking for files
    as only phy files are taken to skm others are only taken to pet
    """
    if tier in ("daq", "daq_compress"):
        fn_pattern = patt.get_pattern_tier_daq(config, extension="{ext}", check_in_cycle=False)
    else:
        fn_pattern = patt.get_pattern_tier(config, tier, check_in_cycle=False)
    return fn_pattern


def build_filelist(
    config,
    filekeys,
    search_pattern,
    tier,
    ignore_keys=None,
):
    """
    This function builds the filelist for the given filekeys, search pattern
    and tier. It will ignore any keys in the ignore_keys list and only include
    the keys specified in the analysis_runs dict.
    """
    # the ignore_keys dictionary organizes keys in sections, gather all the
    # section contents in a single list
    if ignore_keys is not None:
        if tier in ("raw"):
            ignore_keys = ignore_keys.get("unprocessable", [])
        else:
            _ignore_keys = ignore_keys.get("removed", [])
            _ignore_keys += ignore_keys.get("unprocessable", [])
            ignore_keys = sorted(_ignore_keys)
    else:
        ignore_keys = []

    fn_pattern = get_pattern(config, tier)
    filenames = []

    for key in filekeys:
        if not isinstance(search_pattern, list):
            search_pattern = [search_pattern]
        for _search_pat in search_pattern:
            if Path(_search_pat).suffix == ".*":
                search_pat = Path(_search_pat).with_suffix(".{ext}")
            else:
                search_pat = _search_pat
            fn_glob_pattern = key.get_path_from_filekey(search_pat, ext="*")[0]
            files = glob.glob(fn_glob_pattern)
            for f in files:
                _key = FileKey.get_filekey_from_pattern(f, search_pat)
                if _key.name in ignore_keys:
                    pass
                else:
                    if tier == "daq":
                        filename = FileKey.get_path_from_filekey(
                            _key, fn_pattern.with_suffix("".join(Path(f).suffixes))
                        )
                    elif tier == "daq_compress":
                        if Path(f).suffix == ".orca":
                            filename = FileKey.get_path_from_filekey(
                                _key, fn_pattern.with_suffix(".orca.bz2")
                            )
                        else:
                            filename = FileKey.get_path_from_filekey(
                                _key, fn_pattern.with_suffix("".join(Path(f).suffixes))
                            )
                    else:
                        filename = FileKey.get_path_from_filekey(_key, fn_pattern)

                    filenames += filename

    return sorted(filenames)


def get_filelist(wildcards, config, search_pattern, ignore_keys_file=None):
    # remove the file selection from the keypart
    keypart = f"-{wildcards.label.split('-', 1)[1]}"
    ignore_keys = get_ignored_keys(ignore_keys_file)

    filekeys = get_keys(keypart)

    return build_filelist(
        config,
        filekeys,
        search_pattern,
        wildcards.tier,
        ignore_keys,
    )


def get_filelist_full_wildcards(
    wildcards,
    config,
    search_pattern,
    tier,
    ignore_keys_file=None,
):
    keypart = (
        f"-{wildcards.experiment}-{wildcards.detector}-{wildcards.measurement}-{wildcards.run}"
    )

    ignore_keys = get_ignored_keys(ignore_keys_file)

    filekeys = get_keys(keypart)
    return build_filelist(
        config,
        filekeys,
        search_pattern,
        tier,
        ignore_keys,
    )
