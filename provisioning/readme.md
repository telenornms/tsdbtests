# provisioning

Setup scripts and config for setting up as similar as possible servers.

* `./bump-storage.sh` bumps storage partitions uniformly 
* `./setup-tsbs.sh` installs the Questdb fork of `[tsbs](https://github.com/questdb/tsbs)` (the most up-to-date fork) locally on the machine
* `./setup-qdb` contains some custom setup for `Questdb` as it does not provide a package for RHEL or systemd daemon out of the box


## Database table

| database | influxdb | questdb | timescaledb | victoriametrics |
| ---- | ---- | ---- | ---- | ---- |
| storage location | /var/lib/influxdb/data | /var/lib/questdb/db | /var/lib/pgsql/17/data | /var/lib/victoria-metrics/data |



