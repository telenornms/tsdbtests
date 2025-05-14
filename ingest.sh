#!/usr/bin/env bash
# size of ingest
s=${1:-1000}

# amt workers
w=${3:-20}

# start timestamp
t=${2:-01-2023}

db=$TSDB_NAME

flags="-f \"$db\"  -s \"$s\" -t \"$t\" -w \"$w\""

case "$db" in
"timescaledb")
  flags="$flags -p \"$TSDB_PASSWORD\" -d tsdb"
  ;;
"influxdb")
  flags="$flags -a \"$TSDB_PASSWORD\""
  ;;
esac

eval "python benchmark.py $flags"
