# LEGEND L200 dataflow for HADES data

*Note: Still work in progress.*

Implementation of an automatic data processing flow for HADES L200
detector characterization data, based on
[Snakemake](https://snakemake.readthedocs.io/).


## Configuration

Data processing resources are configured via a single site-dependent (and
possibly user-dependent) configuration file, named "config.json" in the
following. You may choose an arbitrary name, though.

Use the included [templates/config.json](templates/config.json) as a template
and adjust the data base paths as necessary.

When running Snakemake, the path to the config file *must* be provided via
`--configfile=path/to/configfile.json`. For example, run

```shell
snakemake -j`nproc` --configfile=config.json file_to_generate
```


## Key-Lists

Data generation is based on key-lists, which are flat text files
(extension ".keylist") containing one entry of the form
`{detector}-{measurement}-run{run}-{timestamp}` per line.

Key-lists can be auto-generated based on the available tier0 (raw DAQ) files
using Snakemake targets of the form

* `all.keylist`
* `all-{detector}.keylist`
* `all-{detector}-{measurement}.keylist`
* `all-{detector}-{measurement}-run{run}.keylist`
* `all-{detector}-{measurement}-run{run}-{timestamp}.keylist`

which will generate the list of available file keys for all detectors, resp.
a specific detector, or a specific detector and measurement, etc.

For example:

```shell
snakemake -j4 --configfile=config.json all-mydet-mymeas.keylist
```

will generate a key-list with all files regarding detector `mydet` and
measurement `mymeas`.


## File-Lists

File-lists are flat files listing output files that should be generated,
with one file per line. A file-list will typically be generated for a given
data tier from a key-list, using the Snakemake targets of the form
`{label}-{tier}.filelist` (generated from `{label}.filelist`).

For file lists based on auto-generated key-lists like
`all-{detector}-{measurement}-{tier}.filelist`, the corresponding key-list
(`all-{detector}-{measurement}.keylist` in this case) will be created
automatically, if it doesn't exist.

Example:

```shell
snakemake -j4 --configfile=config.json all-mydet-mymeas-tier2.filelist
```

File-lists may of course also be derived from custom keylists, generated
manually or by other means, e.g. `my-dataset-tier1.keylist` will be
generated from `my-dataset.filelist`.


## Main output generation

Usually, the main output will be determined by a file-list, resp. a key-list
and data tier. The special output target `{label}-{tier}.gen` is used to
generate all files listed in `{label}-{tier}.filelist`. After the files
are created, the empty file `{label}-{tier}.filelist` will be created to
mark the successful data production.

Snakemake targets like `all-{detector}-{measurement}-{tier}.gen` may be used
to automatically generate key-lists and file-lists (if not already present)
and produce all possible output for the given data tier, based on available
tier0 files which match the target.

Example:

```shell
snakemake -j`nproc` --configfile=config.json all-mydet-mymeas-tier2.gen
```

Targets like `my-dataset-tier1.gen` (derived from a key-list
`my-dataset.keylist`) are of course allowed as well.


## Monitoring

Snakemake supports monitoring by connecting to a
[panoptes](https://github.com/panoptes-organization/panoptes) server.

Run (e.g.)

```shell
panoptes --port 5000

```

in the background to run a panoptes server instance, which comes with a
GUI that can be accessed with a web-brower on the specified port.

Then use the Snakemake option `--wms-monitor` to instruct Snakemake to push
progress information to the panoptes server:

```shell
snakemake --wms-monitor http://127.0.0.1:5000 [...]
```


## Running on a batch system

A template configuration to run the dataflow on an SGE batch system with
Singularity containers instantiated via
[`venv`](https://github.com/oschulz/singularity-venv) is included in
[templates/snakemake-config](templates/snakemake-config). Copy the
configuration into `"$HOME/.config/snakemake"` and adjust as necessary
(especially batch-queue selection, number of jobs, etc.).

The configuration assumes that `venv` is installed as
`"$HOME/.local/bin/venv"` and that `venv legend` will start a suitable LEGEND
 container instance.

You should then be able to run containerized data production on the batch
system via (e.g.):

```shell
snakemake --profile cluster-sge --configfile=config.json all-mydet-mymeas-tier2.gen
```

The template configuration for SGE uses the Snakemakes' `--cluster-sync`
option, so no `--cluster-status` script is necessary.
