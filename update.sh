#!/bin/bash
# update
if [ -e install/readonly_on ];
then
	mount -o remount,rw /
	mount -o remount,rw /boot
fi

git pull
cd install
./install.sh