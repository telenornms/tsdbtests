#!/usr/bin/env bash
# size of ingest
s=${1:-1000}

# amt workers
w=${3:-20}

# start timestamp
t=${2:-01-2023}

db=$TSDB_NAME
pw=$TSDB_PASSWORD

python ingest_test.py -f "$db" -a "$pw" -p "$pw" -s "$s" -t "$t" -w "$w"
