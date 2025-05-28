# Installation Guide - VictoriaMetricsDB

## Installation of VictoriaMetrics

- Download from GitHub release:

```
wget https://github.com/VictoriaMetrics/VictoriaMetrics/releases/download/v1.116.0/victoria-metrics-linux-amd64-v1.116.0.tar.gz
```

- Install

```
sudo tar -xvf <victoriametrics-archive> -C /usr/local/bin
```

```
sudo useradd -s /usr/sbin/nologin victoriametrics

sudo mkdir -p /var/lib/victoria-metrics && sudo chown -R victoriametrics:victoriametrics /var/lib/victoria-metrics
```

```
sudo bash -c 'cat <<END >/etc/systemd/system/victoriametrics.service
[Unit]
Description=VictoriaMetrics service
After=network.target

[Service]
Type=simple
User=victoriametrics
Group=victoriametrics
ExecStart=/usr/local/bin/victoria-metrics-prod -storageDataPath=/var/lib/victoria-metrics -retentionPeriod=90d -selfScrapeInterval=10s
SyslogIdentifier=victoriametrics
Restart=always
RestartSec=10

PrivateTmp=yes
ProtectHome=yes
NoNewPrivileges=yes

ProtectSystem=full

[Install]
WantedBy=multi-user.target
END'
```

## Start VictoriaMetrics Service

```
sudo systemctl daemon-reload && sudo systemctl enable victoriametrics.service

sudo systemctl start victoriametrics.service

sudo systemctl status victoriametrics.service
```

## View GUI

```
localhost:8428/vmui
```