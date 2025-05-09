#!/usr/bin/env bash
db=$1
n=$2
pw=$3

python tsbs_benchmarks.py -f "$db" -s "$n" -a "$pw"
