#!/bin/bash

jobstatusdir="${HOME}/batch-status"

jobid="$1"


if (qstat -u `whoami` | grep -q "${jobid}") ; then
    echo "running"
else
    if [ -f "${jobstatusdir}/${jobid}.success" ]; then
        echo "success"
    elif [ -f "${jobstatusdir}/${jobid}.failed" ]; then
        echo "failed"
    else
        # Wait to account for distributed file system latency:
        sleep 10
        if [ -f "${jobstatusdir}/${jobid}.success" ]; then
            echo "success"
        else
            echo "WARN: JOB STATUS: Job ${jobid} terminated without creating status file, assuming job has failed." >&2
            echo "failed"
        fi
    fi
fi
