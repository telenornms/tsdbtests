#!/usr/bin/env bash

echo "configuring system file limits for questdb"

cp ./98-fs-file-max.conf ./98-vm-max-map-count.conf /etc/sysctl.d/

sysctl --system

echo "creating questdb user and group"

groupadd questdb
adduser questdb -g questdb

echo "set up java"
sudo dnf install java-17-openjdk.x86_64 -y

echo "get latest questdb"
wget https://github.com/questdb/questdb/releases/download/8.3.1/questdb-8.3.1-no-jre-bin.tar.gz

mkdir -p qdb
sudo tar -xzf ./questdb-8.3.1-no-jre-bin.tar.gz -C qdb --strip-components 1
sudo cp ./qdb/questdb.jar /usr/local
sudo rm -fr ./qdb questdb.tar.gz
sudo mkdir -p /var/lib/questdb
sudo chown questdb:questdb /var/lib/questdb
sudo chmod 770 /var/lib/questdb

echo "setup systemd daemon"

cp ./questdb.service /etc/systemd/system/

systemctl daemon-reload
systemctl enable questdb
systemctl start questdb

echo "done, check status with"
echo "journalctl -u questdb | tail"
