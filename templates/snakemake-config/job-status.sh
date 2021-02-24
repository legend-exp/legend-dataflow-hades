#!/bin/bash

dbpath="${HOME}/jobstatus.db"

job_id="$1"

if [ -z "${job_id}" ] ; then
    echo "ERROR, no job id specified" >&2
    exit 1
fi

if [ ! -f "${dbpath}" ] ; then
    echo "ERROR, SQLite job database \"${dbpath}\" doesn't exist." >&2
    exit 1
fi

job_status=`sqlite3 -cmd ".timeout 10000" "${dbpath}" "SELECT status FROM jobstatus WHERE jobid = ${job_id}"`

if [ "${job_status}" = "0" ] ; then
    echo "success"
elif [ "${job_status}" = "1" ] ; then
    echo "failed"
elif [ "${job_status}" = "2" -o "${job_status}" = "4" ] ; then
    # Snakemake cluster-status has no special return value for queued jobs,
    # so report both running and queued jobs as running.

    # Check `qstat`, in case job failed to mark it's exit status in the
    # database. If so, assume job has failed:
    if (qstat -u `whoami` | grep -q "${job_id}") ; then
        echo "running"
    else
        echo "WARNING, job \"${job_id}\" has status \"${job_status}\", but is no longer listed in batch system." >&2
        echo "failed"
    fi
elif [ "${job_status}" = "" ] ; then
    echo "ERROR, job \"${job_id}\" not found in job status database." >&2
    exit 1
else
    echo "ERROR, invalid job status \"${job_status}\" for job id \"${job_id}\"." >&2
    exit 1
fi
