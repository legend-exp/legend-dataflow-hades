#!/bin/bash -e

joblogdir="${HOME}/batch-logs"


scriptdir() {
	(echo "${0}" | grep -q '^/') && dirname "${0}" || (cd "`pwd`/`dirname \"${0}\"`" && pwd)
}
this_scriptdir=`scriptdir`



jobscript="$1"

jobname=`basename "$jobscript" ".sh"`

mkdir -p "$joblogdir"

job_id=$(
    qsub \
        -cwd -V \
        -N "$jobname" \
        -o "$HOME/batch-logs/$jobname.stdout"  \
        -e "$HOME/batch-logs/$jobname.stderr" \
        "$jobscript" \
    | head -n1 | sed 's/[^0-9]*\([0-9]\+\).*/\1/'
)

echo "${job_id}"
