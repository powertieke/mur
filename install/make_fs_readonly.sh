#!/bin/bash
# make system readonly

# disable swap
dphys-swapfile swapoff
dphys-swapfile uninstall
update-rc.d dphys-swapfile disable

# install UnionFS
apt-get install unionfs-fuse -y

cp mount_unionfs /usr/local/bin/
chmod +x /usr/local/bin/mount_unionfs

cp fstab /etc/

cp -al /etc /etc_org
mv /var /var_org
mkdir /etc_rw
mkdir /var /var_rw
touch readonly_on