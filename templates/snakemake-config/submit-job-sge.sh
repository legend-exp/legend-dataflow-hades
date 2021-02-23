#!/bin/bash -e

venv="$HOME/.local/bin/venv"

# echo "Called submit-job.sh with args:" "$@" >> "$HOME/job-submission.log"

runtime="1200"
while getopts r: OPT; do
	case ${OPT} in
	r) runtime="${OPTARG}" ;;
	esac
done
shift `expr $OPTIND - 1`
jobscript="$1"

# echo "Submitting $jobscript with runtime $runtime" >> "$HOME/job-submission.log"

jobname=`basename "$jobscript" ".sh"`

mkdir -p "$HOME/batch-logs"

qsub \
    -sync y \
    -cwd \
    -b y \
    -N "$jobname" \
    -o "$HOME/batch-logs/$jobname.stdout"  \
    -e "$HOME/batch-logs/$jobname.stderr" \
    -l "h_rt=$runtime" \
    "$venv" legend "$jobscript"
