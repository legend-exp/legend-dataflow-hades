#!/bin/bash -e

jobstatusdir="${HOME}/batch-status"

joblogdir="${HOME}/batch-logs"


scriptdir() {
	(echo "${0}" | grep -q '^/') && dirname "${0}" || (cd "`pwd`/`dirname \"${0}\"`" && pwd)
}
this_scriptdir=`scriptdir`


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

mkdir -p "$joblogdir"
mkdir -p "$jobstatusdir"

job_id=$(
    qsub \
        -cwd \
        -b y \
        -N "$jobname" \
        -o "$HOME/batch-logs/$jobname.stdout"  \
        -e "$HOME/batch-logs/$jobname.stderr" \
        -l "h_rt=$runtime" \
        "$this_scriptdir/job-wrapper.sh" "$jobscript" \
    | head -n1 | sed 's/[^0-9]*\([0-9]\+\).*/\1/'
)

echo "${job_id}"
