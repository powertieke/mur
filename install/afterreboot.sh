#!/bin/bash
if [ -e readonly_on ];
then
	mount -o remount,rw /
	mount -o remount,rw /boot
fi
mv /etc/rc.local.bak /etc/rc.local
apt-get update -y
apt-get upgrade -y
apt-get install libdbus-glib-1-dev
apt-get install dbus-x11 -y
apt-get install python-pygame -y
apt-get install python3-pygame -y
apt-get install omxplayer -y
apt-get install python3-dbus -y
apt-get install python-dbus -y
apt-get install lighttpd -y
cp ../locations/boot/runonboot.sh /boot/
cp ../locations/boot/config.txt /boot/
cp -r ../locations/etc/lighttpd/* /etc/lighttpd/
cp ../locations/etc/rc.local /etc/rc.local
if [ ! -e /media/usb ]; then
mkdir -p /media/usb
fi
if [ ! -e /home/pi/movies ]; then
	mkdir -p /home/pi/movies
fi
if [ ! -e readonly_on ];
then
	./make_readonly.sh
fi
reboot
