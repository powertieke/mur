#!/bin/bash

# turn off swap.

sed 's/$/ fastboot noswap ro/' /boot/cmdline.txt > /boot/cmdline.txt

# move some files because Charles said so

apt-get install busybox-syslogd -y; dpkg --purge rsyslog

rm -rf /var/lib/dhcp/ /var/lib/dhcpcd5 /var/run /var/spool /var/lock /etc/resolv.conf
ln -s /tmp /var/lib/dhcp
ln -s /tmp /var/lib/dhcpcd5
ln -s /tmp /var/run
ln -s /tmp /var/spool
ln -s /tmp /var/lock
touch /tmp/dhcpcd.resolv.conf
ln -s /tmp/dhcpcd.resolv.conf /etc/resolv.conf


if ! [ -e /etc/systemd/system/dhcpcd5.service.bak ];
then
	cp /etc/systemd/system/dhcpcd5.service /etc/systemd/system/dhcpcd5.service.bak
fi
sed 's/PIDFile=\/run\/dhcpcd\.pid/PIDFile=\/var\/run\/dhcpcd.pid/' /etc/systemd/system/dhcpcd5.service > /etc/systemd/system/dhcpcd5.service.new
mv /etc/systemd/system/dhcpcd5.service.new /etc/systemd/system/dhcpcd5.service

rm /var/lib/systemd/random-seed

ln -s /tmp/random-seed /var/lib/systemd/random-seed

if ! [ -e /lib/systemd/system/systemd-random-seed.service.bak ];
then
	cp /lib/systemd/system/systemd-random-seed.service /lib/systemd/system/systemd-random-seed.service.bak
fi
sed 's/RemainAfterExit=yes/RemainAfterExit=yes\nExecStartPre=\/bin\/echo "" >\/tmp\/tandom-seed/' /lib/systemd/system/systemd-random-seed.service > /lib/systemd/system/systemd-random-seed.service.new
mv /lib/systemd/system/systemd-random-seed.service.new /lib/systemd/system/systemd-random-seed.service
systemctl daemon-reload

apt-get install ntp -y

if ! [ -e /etc/fstab.bak ];
then
  mv /etc/fstab /etc/fstab.bak
fi

cp fstab.readonly /etc/fstab
touch readonly_on
