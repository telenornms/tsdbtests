# Time series database testing repo

Code related to testing performance of time series databases.

Setup for databases found in `./setup`, test results in `./results`

## `tsbs` tests

Scripts for running [`tsbs`](https://github.com/questdb/tsbs) tests and their results


### Commands for `benchmark.py`

| db | command |
| ---- | ---- |
| influx | `python benchmark.py -f influx -a [auth key]` | 
| questdb | `python benchmark.py -f questdb` |
| timescale | `python benchmark.py -f timescaledb -p [password] -d tsdb` |
| victoriametrics | `python benchmark.py -f victoriametrics` |

Run `python benchmark.py -h` for all additional configurable options and their significance.



