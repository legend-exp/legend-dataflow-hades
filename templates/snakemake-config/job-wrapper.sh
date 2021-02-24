#!/bin/bash

dbpath="${HOME}/jobstatus.db"

job_id="${JOB_ID}"

echo "JOB WRAPPER: job ${job_id} starting." >&2

run-sqlite() {
    sqlite3 -cmd ".timeout 10000" "${dbpath}" "$@"
}

if [ ! -f "${dbpath}" ] ; then
    echo "ERROR, SQLite job database \"${dbpath}\" doesn't exist." >&2
    exit 1
fi

run-sqlite "CREATE TABLE IF NOT EXISTS jobstatus (jobid INTEGER NOT NULL PRIMARY KEY, status INTEGER NOT NULL)"

run-sqlite "REPLACE INTO jobstatus (jobid, status) VALUES (${job_id}, 2)" \
    && echo "JOB WRAPPER: marked job ${job_id} as running." >&2

if ("$@"); then
    run-sqlite "REPLACE INTO jobstatus (jobid, status) VALUES (${job_id}, 0)" \
        && echo "JOB WRAPPER: marked job ${job_id} as successful." >&2
    exit 0
else
    run-sqlite "REPLACE INTO jobstatus (jobid, status) VALUES (${job_id}, 1)" \
        && echo "JOB WRAPPER: marked job ${job_id} as failed." >&2
    exit 1
fi
