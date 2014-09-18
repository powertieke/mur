#!/usr/bin/python3

import sys
import os
import controller
import re

def interface(clients, udpport_sync, moviefolder):
	syncre = re.compile(r'^sync:(.*)$')
	skipre = re.compile(r'^skip:(.*)$')
	playre = re.compile(r'^play:(.*)$')
	while True:
		command = input('--> Type "play:<moviefile>" or "sync:<moviefile>" : ')
		if command == '':
			pass
		elif playre.match(command):
			moviename = playre.match(command).group(1)
			print("Which screen?\n")
			for key in clients.keys():
				print(key)
			while True:
				client = input("--> Type the name of the screen you would like to show the presentation on or type cancel:")
				if client in clients.keys():
					controller.play_single(moviefolder + "/Single/" + moviename + ".mp4", clients[client])
					break
				elif client == "cancel":
					break
				else:
					print(client + " not in screen list. Try again.\n")
			
		elif syncre.match(command):
			moviename = syncre.match(command).group(1)
			print(controller.play_sync(moviefolder + "/Sync/" + moviename, clients, udpport_sync))
		elif command == "quit":
			break
		else:
			pass