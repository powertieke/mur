#!/usr/bin/python3

import sys
import os
import controller

def interface(clients, udpport_sync, moviefolder):
	while True:
		command = input('--> Hit <ENTER> for synced play : ')
		if command == '':
			controller.play_sync(moviefolder + "sync/screen", clients, udpport_sync)
		