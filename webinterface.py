#!/usr/bin/python3
import sys
import controller
import re
import os
import json
import queue

def webinterface(clients, udpport_sync, moviefolder, syncqueue):
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
			print("gotnuthin")
			putmessage(outpipe_path, "")
		elif playre.match(command):
			print("play")
			client, moviename = playre.match(command).group(1).split(",")
			response = controller.play_single(moviefolder + "/single/" + moviename + ".mp4", clients[client])
			putmessage(outpipe_path, json.dumps({x : clients[x][1] for x in clients.keys()}))
			
		elif syncre.match(command):
			print("gotsync")
			moviename = syncre.match(command).group(1)
			syncqueue.put("endloop")
			controller.startSyncThread(moviefolder + "/sync/" + moviename, clients, udpport_sync, syncqueues)
			putmessage(outpipe_path, json.dumps({x : clients[x][1] for x in clients.keys()}))
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
			print("gotstatus")
			putmessage(outpipe_path, json.dumps({x : clients[x][1] for x in clients.keys()}))
		else:
			print(command)
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
	
