"""
This module contains all the utility needed for the data production.
These are mainly resolvers for the config.json dictionary,
and for substituting the pathvar within, also the conversion
from timestamp to unix time
"""

import os, re
from datetime import datetime

def convert_to_daq_timestamp(value):
    return datetime.strftime(datetime.strptime(value, "%Y%m%dT%H%M%SZ"), "%y%m%dT%H%M%S")

def convert_to_legend_timestamp(value):
    return datetime.strftime(datetime.strptime(value, "%y%m%dT%H%M%S"), "%Y%m%dT%H%M%SZ")

def convert_to_legend_run(value):
    return re.sub(r'run\d{1}(\d{3})', r"r\1", value)

def convert_to_daq_run(value):
    return re.sub(r'r(\d{3})', r"run0\1", value)

def run_splitter(files):
    """
    Returns list containing lists of each run
    """

    runs = []
    run_files = []
    for file in files:
        base = os.path.basename(file)
        file_name = os.path.splitext(base)[0]
        parts = file_name.split("-")
        run_no = parts[3]
        if run_no not in runs:
            runs.append(run_no)
            run_files.append([])
        for i, run in enumerate(runs):
            if run == run_no:
                run_files[i].append(file)
    return run_files