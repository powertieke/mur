#!/bin/bash
# install mur on clean raspberry pi
if [ -e readonly_on ];
then
	mount -o remount,rw /
fi
apt-get update -y
apt-get upgrade -y
rpi-update
mv /etc/rc.local /etc/rc.local.bak
cp rc.local /etc/
reboot