#!/usr/bin/python3

import os

def webinterface():
	inpipe_path = "/home/pi/fromwebapp"
	outpipe_path = "/home/pi/towebapp"
	
	if not os.path.exists(inpipe_path):
		os.mkfifo(inpipe_path)
	
	if not os.path.exists(outpipe_path):
		os.mkfifo(outpipe_path)
		
	syncre = re.compile(r'^sync:(.*)$')
	playre = re.compile(r'^play:(.*)$')
	statre = re.compile(r'^stat:(.*)$')
	while True:
		command = getmessage(inpipe_path)
		if command == '':
			putmessage(outpipe_path, "")
		elif playre.match(command):
			moviename = playre.match(command).group(1)
			print("Which screen?\n")
			for key in clients.keys():
				putmessage()
			while True:
				client = input("--> Type the name of the screen you would like to show the presentation on or type cancel:")
				if client in clients.keys():
					print(controller.play_single(moviefolder + "/single/" + moviename + ".mp4", clients[client]))
					break
				elif client == "cancel":
					break
				else:
					print(client + " not in screen list. Try again.\n")
			
		elif syncre.match(command):
			moviename = syncre.match(command).group(1)
			print(controller.play_sync(moviefolder + "/sync/" + moviename, clients, udpport_sync))
		elif statre.match(command):
			piname = statre.match(command).group(1)
			if piname == all:
				statstring = ""
				clientrecord = []
				for client in clients.keys():
					clientrecord.append("/".join([client, clients[client][1]]))
		elif command == "quit":
			break
		elif command == "status":
			putmessage(outpipe_path, status)
		else:
			pass
		

def getmessage(pipe_path):
	pipe = open(pipe_path, 'r')
	message = pipe.read()
	pipe.close()
	return message
	
def putmessage(pipe_path, message):
	pipe = open(pipe_path, 'w')
	message = pipe.writelines(message)
	pipe.close()
	
