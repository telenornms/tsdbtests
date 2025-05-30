#!/usr/bin/env bash

sudo pvcreate /dev/sdb
sudo vgextend vg0 /dev/sdb

sudo lvresize -rL +5G vg0/tmp
sudo lvresize -rL +45G vg0/var
sudo lvresize -rL +5G vg0/home
sudo lvresize -rL +5G vg0/var-log
