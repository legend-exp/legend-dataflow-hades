#!/bin/bash
# properties = properties

set -o errexit

jobstatusdir="$HOME/batch-status"

jobid="$JOB_ID"

if [ -z "$jobid" ] ; then
    echo "ERROR: JOBSCRIPT: Can't find job id in environment variables." >&2
    exit 1
fi

echo "JOBSCRIPT: Job id $jobid starting: $0" >&2

mkdir -p "$jobstatusdir"

exec_cmd=$(
(cat | sed 's/exit 0/true/; s/exit 1/false/') <<EOF
{exec_job}
EOF
)

eval "$exec_cmd" && (
    touch "$jobstatusdir/$jobid.success"
    exit 0
) || (
    touch "$jobstatusdir/$jobid.failed"
    exit 1
)
