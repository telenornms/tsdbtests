# Time series database testing repo

Code related to testing performance of time series databases.

Setup for databases found in `./setup`, test results in `./results`

## `tsbs` tests

Scripts for running `tsbs` tests and their results


### Commands for `ingest_test.py`

| db | command |
| ---- | ---- |
| influx | `python ingest_test.py -f influx -a [auth key]` | 
| questdb | `python ingest_test.py -f questdb` |
| timescale | `python ingest_test.py -f timescaledb -p [password] -d tsdb` |
| victoriametrics | `python ingest_test.py -f victoriametrics` |

`-s [number]` limits or increases scale of file, default `1000`

`-r [number]` changes number of runs and created files, default `5`

`-t [number]` timestamp of first run



