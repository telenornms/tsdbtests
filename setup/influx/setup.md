# Installation guide - InfluxDB

- <https://docs.influxdata.com/influxdb/v2/install/>

- <https://docs.influxdata.com/influxdb/v2/tools/influx-cli/>

## Installation and setup of influxdb

- RedHat:

```bash
sudo curl --silent --location -O https://repos.influxdata.com/influxdata-archive.key && echo "943666881a1b8d9b849b74caebf02d3465d6beb716510d86a39f6c8e8dac7515  influxdata-archive.key" | sha256sum --check - && cat influxdata-archive.key | gpg --dearmor | tee /etc/pki/rpm-gpg/RPM-GPG-KEY-influxdata > /dev/null
```

```bash
sudo cat <<EOF | sudo tee /etc/yum.repos.d/influxdata.repo
[influxdata]
name = InfluxData Repository - Stable
baseurl = https://repos.influxdata.com/stable/x86_64/main
enabled = 1
gpgcheck = 1
gpgkey = file:///etc/pki/rpm-gpg/RPM-GPG-KEY-influxdata
EOF
```

```bash
sudo dnf install influxdb2
```

- Debian:

```bash
curl --silent --location -O https://repos.influxdata.com/influxdata-archive.key
echo "943666881a1b8d9b849b74caebf02d3465d6beb716510d86a39f6c8e8dac7515  influxdata-archive.key" | sha256sum --check - && cat influxdata-archive.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/influxdata-archive.gpg > /dev/null && echo 'deb [signed-by=/etc/apt/trusted.gpg.d/influxdata-archive.gpg] https://repos.influxdata.com/debian stable main' | sudo tee /etc/apt/sources.list.d/influxdata.list
```

```bash
sudo apt update && sudo apt install influxdb2

```

- Common:

```bash
sudo service influxdb start

sudo service influxdb status
```

### Setup config

```bash
nvim /etc/default/influxdb2

ARG1="--http-bind-address :8086"
ARG2="--storage-wal-fsync-delay=15m"
```

```bash
sudo nvim /lib/systemd/system/influxdb.service

ExecStart=/usr/lib/influxdb/scripts/influxd-systemd-start.sh $ARG1 $ARG2
```

## Installation and setup of influxd

```bash
curl --location -O https://download.influxdata.com/influxdb/releases/influxdb2-2.7.11_linux_amd64.tar.gz
```

```bash
curl --silent --location https://repos.influxdata.com/influxdata-archive.key | gpg --import - 2>&1 | grep 'InfluxData Package Signing Key <support@influxdata.com>' && curl --silent --location "https://download.influxdata.com/influxdb/releases/influxdb2-2.7.11_linux_amd64.tar.gz.asc" | gpg --verify - influxdb2-2.7.11_linux_amd64.tar.gz 2>&1 | grep 'InfluxData Package Signing Key <support@influxdata.com>'
```

```bash
tar -xvzf ./influxdb2-2.7.11_linux_amd64.tar.gz
```

```bash
sudo cp ./influxdb2-2.7.11/usr/bin/influxd /usr/local/bin/
```

### Start influxd

```bash
influxd
```

- Go to localhost:8086 to view the influxUI

## Installation and setup of influx

```bash
wget https://dl.influxdata.com/influxdb/releases/influxdb2-client-2.7.5-linux-amd64.tar.gz
```

```bash
tar -xvzf ./influxdb2-client-2.7.5-linux-amd64.tar.gz
```

```bash
sudo cp ./influx /usr/local/bin
```

### Setup config for auth in influx

- IMPORTANT!!! Can't use any influx commands without first setting this up

```bash
influx config create -n <config-name> -u http://localhost:8086 -p <username>:<password> -o <organization>
```

- Parameters:

```bash
<config-name>: "Just the name of this config, used to change the config later"

<username>:<password>: "The username and password you set up when creating the influx setup"

<organization>: "The organization you set up when creating the influx setup"
```

### Creating database in bucket

```bash
influx v1 dbrp create --db <database-name> --rp 0 --bucket-id `influx bucket ls --name <bucket-name> | awk -v i=2 -v j=1 'FNR == i {print $j}'` --default
```

Parameters:

```bash
<database-name>: "The name of the database you want to create"

<bucket-name>: "The name of the bucket you set up when creating the influx setup"
```
