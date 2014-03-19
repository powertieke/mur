#!/usr/bin/python3

import sys
import os
import controller
import re

def interface(clients, udpport_sync, moviefolder):
	syncre = re.compile(r'^sync:(.*)')
	skipre = re.compile(r'^skip:(.*)')
	playre = re.compile(r'^play:(.*)')
	while True:
		command = input('--> Type "play:<moviefile>" or "sync:<moviefile>" : ')
		if command == '':
			pass
		elif playre.match(command):
			moviename = playre.match(command).groups()[0]
			print("Which screen?\n")
			for key in clients.keys():
				print(key + "\n")
			while True:
				client = input("--> Type the name of the screen you would like to show the presentation on:")
				if client in clients.keys():
					break
				else:
					print(client + " not in screen list. Try again.\n")
			print(controller.play_single(moviefolder + "/singles/" + moviename + ".mp4", clients[client]))
		elif syncre.match(command):
			moviename = syncre.match(command).groups()[0]
			print(controller.play_sync(moviefolder + "/sync/" + moviename, clients, udpport_sync))
		else:
			pass