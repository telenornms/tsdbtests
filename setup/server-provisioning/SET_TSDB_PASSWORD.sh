#!/bin/bash

if [ -z "$1" ]; then
  echo "Error: Password argument required"
  echo "Usage: $0 <tsdb_password>"
  exit 1
fi

tsdbpassword=$1
echo 'export TSDB_PASSWORD="'"$tsdbpassword"'"' | sudo tee /etc/profile.d/tsdb_pw.sh
sudo chmod 644 /etc/profile.d/tsdb_pw.sh

echo "Successfully set tsdb password variable. Will be available after logout."
