#!/bin/bash

if [ -f /boot/update_now ];
	then
	cd /home/pi/mur
	git pull
	cd /boot
	rm update_now
	reboot
fi

if [ -e /dev/sda1 ];
	then
	mount -t vfat /dev/sda1 /media/usb
	cd /home/pi/mur
	python3 muur.py -s $HOSTNAME /media/usb/
fi
