#!/bin/bash -e

scriptdir() {
	(echo "${0}" | grep -q '^/') && dirname "${0}" || (cd "`pwd`/`dirname \"${0}\"`" && pwd)
}
this_scriptdir=`scriptdir`

dbpath="${HOME}/jobstatus.db"
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

run-sqlite() {
    sqlite3 -cmd ".timeout 10000" "${dbpath}" "$@"
}

run-sqlite "CREATE TABLE IF NOT EXISTS jobstatus (jobid INTEGER NOT NULL PRIMARY KEY, status INTEGER NOT NULL)" \
    || exit 1

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

run-sqlite "REPLACE INTO jobstatus (jobid, status) VALUES (${job_id}, 4)" \
    && echo "JOB SUBMISSION: marked job ${job_id} as running." >&2

echo "${job_id}"
