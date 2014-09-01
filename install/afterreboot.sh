#!/bin/bash

mv /etc/rc.local.bak /etc/rc.local
apt-get update -y
apt-get upgrade -y
apt-get install omxplayer -y
apt-get install python3-dbus -y
apt-get install python-dbus -y
apt-get install lighttpd -y
cp ../locations/boot/runonboot.sh /boot/
cp ../locations/etc/lighttpd /etc/lighttpd
cp ../locations/etc/rc.local /etc/rc.local
reboot
