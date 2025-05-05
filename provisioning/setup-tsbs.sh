#!/usr/bin/env bash

dnf install go -y

git clone https://github.com/questdb/tsbs

cd tsbs || exit

make
