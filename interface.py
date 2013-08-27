#!/usr/bin/python3

import sys
import os
import controller

def interface(clients, udpport_sync):
	while True:
		command = input('--> Type \'sync\' and an <ENTER> for synced play : ')
		if command == 'sync':
			controller.play_sync("/home/pi/mur/movie_files/sync/Comp", clients, udpport_sync)
		