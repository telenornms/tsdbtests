#!/bin/bash

if [ -z "$1" ]; then
  echo "Error: Name argument required"
  echo "Usage: $0 <tsdb_name>"
  exit 1
fi

tsdbname=$1
echo 'export TSDB_NAME="'"$tsdbname"'"' | sudo tee /etc/profile.d/tsdb_name.sh
sudo chmod 644 /etc/profile.d/tsdb_name.sh

echo "Successfully set tsdb name variable. Will be available after logout."
