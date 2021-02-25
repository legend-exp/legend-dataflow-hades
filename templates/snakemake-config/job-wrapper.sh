#!/bin/bash

jobstatusdir="${HOME}/batch-status"

jobid="${JOB_ID}"


if [ -z "${jobid}" ] ; then
    echo "ERROR: JOB WRAPPER: Can't find job id in environment variables." >&2
    exit 1
fi

echo "JOB WRAPPER: Job id ${jobid} starting: $@" >&2

if ("$@"); then
    touch "${jobstatusdir}/${jobid}.success"
    exit 0
else
    touch "${jobstatusdir}/${jobid}.failed"
    exit 1
fi
