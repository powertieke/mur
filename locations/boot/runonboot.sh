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
		if [ ! -d /media/usb ];
		then
			cd /media
			mkdir usb
		fi
	mount -t vfat /dev/sda1 /media/usb
	if [ ! -e /home/pi/movies ]; then
		mkdir -p /home/pi/movies
	fi
	rsync -va --delete /media/usb/ /home/pi/movies/
	cd /home/pi/mur
fi
if [ "$HOSTNAME" == "picontroller" ];
	then
		python3 muur.py -m $HOSTNAME /home/pi/movies/
	else
		python3 muur.py -s $HOSTNAME /home/pi/movies/
fi
