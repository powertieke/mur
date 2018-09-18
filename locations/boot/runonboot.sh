#!/bin/bash

if [ -f /boot/update_now ];
	then
	cd /home/pi/mur
	git pull
	cd /boot
	rm update_now
	reboot
fi

if [ -e /dev/sda ];
	then
		if [ -e /home/pi/mur/install/readonly_on ];
		then
			mount -o remount,rw /
			mount -o remount,rw /boot
		fi
		
		if [ ! -d /media/usb ];
		then
			cd /media
			mkdir usb
		fi
	mount -t vfat /dev/sda /media/usb
	if [ ! -e /home/pi/movies ]; then
		mkdir -p /home/pi/movies
	fi
	rsync -va --delete /media/usb/ /home/pi/movies/
	if [ -e /home/pi/mur/install/readonly_on ];
	then
		mount -o remount,ro /
		mount -o remount,ro /boot
	fi
fi

cd /home/pi/mur

## tvservice -e "CEA 31"
## fbset -depth 8 && fbset -depth 16

if [ "$HOSTNAME" == "picontroller" ];
	then
		python3 muur.py -m $HOSTNAME /home/pi/movies/
	else
		python3 muur.py -s $HOSTNAME /home/pi/movies/
fi
