# Installation Guide - TimeScaleDB

- <https://docs.timescale.com/self-hosted/latest/install/installation-linux/>

## Install PostgreSQL and TimesScaleDB

- Red Hat:

```
sudo dnf install https://download.postgresql.org/pub/repos/yum/reporpms/EL-$(rpm -E %{rhel})-x86_64/pgdg-redhat-repo-latest.noarch.rpm
```

- Fedora:

```
sudo dnf install https://download.postgresql.org/pub/repos/yum/reporpms/F-$(rpm -E %{fedora})-x86_64/pgdg-fedora-repo-latest.noarch.rpm
```

- Red Hat:

```
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

- Fedora:

```
sudo tee /etc/yum.repos.d/timescale_timescaledb.repo <<EOL
[timescale_timescaledb]
name=timescale_timescaledb
baseurl=https://packagecloud.io/timescale/timescaledb/el/9/x86_64
repo_gpgcheck=1
gpgcheck=0
enabled=1
gpgkey=https://packagecloud.io/timescale/timescaledb/gpgkey
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
metadata_expire=300
EOL
```

```
sudo dnf update
```

```
sudo dnf install timescaledb-2-postgresql-17 postgresql17
```

- Red Hat(Extra step):

```
sudo dnf -qy module disable postgresql
```

## Set up PostgreSQL

```
sudo /usr/pgsql-17/bin/postgresql-17-setup initdb
```

```
sudo timescaledb-tune --pg-config=/usr/pgsql-17/bin/pg_config
```

```
sudo systemctl enable postgresql-17
```

```
sudo systemctl start postgresql-17

sudo systemctl status postgresql-17
```

```
sudo -u postgres psql
```

```
\password postgres
```

```
\q
```

## Create new database(Extra step)

```
psql -U postgres -h localhost
```

```
CREATE database tsdb
```

```
\c tsdb
```

```
\q
```

```
psql -U postgres -h localhost -l
```

## Set up TimeScaleDB

```
psql -d "postgres://<username>:<password>@localhost/<database-name>" (Database-name refers to either default, postgres, or your own)
```

```
CREATE EXTENSION IF NOT EXISTS timescaledb
```

```
\dx
```

```
\q
```
