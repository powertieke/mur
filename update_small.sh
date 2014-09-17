#!/bin/bash
# small update
if [ -e install/readonly_on ];
then
	mount -o remount,rw /
	mount -o remount,rw /boot
fi

git pull
cp locations/boot/runonboot.sh /boot/
cp -r locations/etc/lighttpd/* /etc/lighttpd/
cp locations/etc/rc.local /etc/rc.local
reboot