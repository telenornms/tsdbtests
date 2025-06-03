# Installation Guide - TimeScaleDB

- <https://docs.timescale.com/self-hosted/latest/install/installation-linux/>

## Install PostgreSQL and TimeScaleDB

```bash
sudo dnf install https://download.postgresql.org/pub/repos/yum/reporpms/EL-$(rpm -E %{rhel})-x86_64/pgdg-redhat-repo-latest.noarch.rpm
```

```bash
sudo tee /etc/yum.repos.d/timescale_timescaledb.repo <<EOL
[timescale_timescaledb]
name=timescale_timescaledb
baseurl=https://packagecloud.io/timescale/timescaledb/el/$(rpm -E %{rhel})/x86_64
repo_gpgcheck=1
gpgcheck=0
enabled=1
gpgkey=https://packagecloud.io/timescale/timescaledb/gpgkey
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
metadata_expire=300
EOL
```

```bash
sudo dnf update
```

```bash
sudo dnf install timescaledb-2-postgresql-17 postgresql17
```

disable builtin postgres v 13

```bash
sudo dnf -qy module disable postgresql
```

## Set up PostgreSQL

```bash
sudo /usr/pgsql-17/bin/postgresql-17-setup initdb
```

```bash
sudo timescaledb-tune --pg-config=/usr/pgsql-17/bin/pg_config
```

```bash
sudo systemctl enable postgresql-17
```

```bash
sudo systemctl start postgresql-17

sudo systemctl status postgresql-17
```

```bash
sudo -u postgres psql
```

```bash
\password postgres
```

```bash
\q
```

## Create new database(Extra step)

```bash
psql -U postgres -h localhost
```

```bash
CREATE database tsdb
```

```bash
\c tsdb
```

```bash
\q
```

```bash
psql -U postgres -h localhost -l
```

## Set up TimeScaleDB

```bash
psql -d "postgres://postgres:postgres@localhost/tsdb"
```

Database-name refers to either default, postgres, or your own i.e. `postgres://<username>:<password>@localhost/<database-name>`

```bash
CREATE EXTENSION IF NOT EXISTS timescaledb
```

```bash
\dx
```

```bash
\q
```
