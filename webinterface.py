#!/usr/bin/python3

import os
import json

def webinterface(clients, udpport_sync, moviefolder):
	inpipe_path = "/home/pi/mur/webpage/fromwebapp"
	outpipe_path = "/home/pi/mur/webpage/towebapp"
	
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
			client, moviename = playre.match(command).group(1).split(",")
			response = controller.play_single(moviefolder + "/single/" + moviename + ".mp4", clients[client])
			putmessage(outpipe_path, json.dumps({x : clients[x][1] for x in clients.keys()}))
			
		elif syncre.match(command):
			moviename = syncre.match(command).group(1)
			response = controller.play_sync(moviefolder + "/sync/" + moviename, clients, udpport_sync)
		elif statre.match(command): # here for fun, not used yet
			piname = statre.match(command).group(1)
			if piname == all:
				statstring = ""
				clientrecord = []
				for client in clients.keys():
					clientrecord.append("/".join([client, clients[client][1]]))
		elif command == "quit":
			break
		elif command == "status":
			putmessage(outpipe_path, json.dumps({x : clients[x][1] for x in clients.keys()}))
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
	
