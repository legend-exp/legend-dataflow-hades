#!/bin/bash

dbpath="${HOME}/jobstatus.db"

run-sqlite() {
    sqlite3 -cmd ".timeout 10000" "${dbpath}" "$@"
}

run-sqlite 'select * from jobstatus' | cut -d '|' -f 2 | sort | uniq -c
