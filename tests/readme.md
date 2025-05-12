# `tsbs` tests

Scripts for running `tsbs` tests and their results


## Commands for `tsbs_benchmarks.py`

| db | command |
| ---- | ---- |
| influx | `python tsbs_benchmarks.py -f influx -a [auth key]` | 
| questdb | `python tsbs_benchmarks.py -f questdb` |
| timescale | `python tsbs_benchmarks.py -f timescaledb -p [password] -d tsdb` |
| victoriametrics | `python tsbs_benchmarks.py -f victoriametrics` |

`-s [number]` limits or increases scale of file, default `1000`

`-r [number]` changes number of runs and created files, default `5`



