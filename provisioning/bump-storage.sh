pvcreate /dev/sdb
vgextend vg0 /dev/sdb

lvresize -rL +15G vg0/tmp
lvresize -rL +50G vg0/var
lvresize -rL +15G vg0/home
lvresize -rL +10G vg0/var-log
