#!/usr/bin/python3
import sys
import controller
import re
import os
import json
import queue
import time
import subprocess
import player

def webinterface(clients, udpport_sync, moviefolder, killqueue):
	inpipe_path = "/home/pi/mur/webpage/fromwebapp"
	outpipe_path = "/home/pi/mur/webpage/towebapp"
	lockfile_path = "/home/pi/mur/webpage/locked"
	runningfile_path = "/home/pi/mur/webpage/running"
	
	if os.path.exists(lockfile_path):
		os.remove(lockfile_path)
	
	if not os.path.exists(runningfile_path):
		open(runningfile_path, "a")
	
	if not os.path.exists(inpipe_path):
		os.mkfifo(inpipe_path)
	
	if not os.path.exists(outpipe_path):
		os.mkfifo(outpipe_path)
		
	syncre = re.compile(r'^sync:(.*)$')
	playre = re.compile(r'^play:(.*)$')
	statre = re.compile(r'^stat:(.*)$')
	stopre = re.compile(r'^stop:(.*)$')
	bootre = re.compile(r'^boot:(.*)$')
	while True:
		command = getmessage(inpipe_path)
		if command == '':
			putmessage(outpipe_path, "")
		elif playre.match(command):
			client, moviename = playre.match(command).group(1).split(",")
			controller.play_single(moviefolder + "/single/" + moviename + ".mp4", clients[client])
			putmessage(outpipe_path, json.dumps({x : clients[x][1] for x in clients.keys()}))
			
		elif syncre.match(command):
			moviename = syncre.match(command).group(1)
			killqueue.put("kill")
			controller.startSyncThread(moviefolder + "/sync/" + moviename, clients, udpport_sync, killqueue)
			putmessage(outpipe_path, json.dumps({x : clients[x][1] for x in clients.keys()}))
		elif statre.match(command): # here for fun, not used yet
			piname = statre.match(command).group(1)
			if piname == all:
				statstring = ""
				clientrecord = []
				for client in clients.keys():
					clientrecord.append("/".join([client, clients[client][1]]))
		elif stopre.match(command):
			client = stopre.match(command).group(1)
			clients[client][1] = controller.message_to_pi(clients[client], 'shutdown')
			putmessage(outpipe_path, json.dumps({x : clients[x][1] for x in clients.keys()}))
		elif bootre.match(command):
			client = bootre.match(command).group(1)
			clients[client][1] = controller.message_to_pi(clients[client], 'reboot')
			putmessage(outpipe_path, json.dumps({x : clients[x][1] for x in clients.keys()}))
		elif command == "updateall":
			for client in clients.keys():
				clients[client][1] = controller.message_to_pi(clients[client], 'update')
			putmessage(outpipe_path, json.dumps({x : clients[x][1] for x in clients.keys()}))
		elif command == "quit":
			for client in clients.keys():
				clients[client][1] = controller.message_to_pi(clients[client], 'shutdown')
			putmessage(outpipe_path, json.dumps({x : clients[x][1] for x in clients.keys()}))
		elif command == "status":
			putmessage(outpipe_path, json.dumps({x : clients[x][1] for x in clients.keys()}))
		elif command == "quit_c":
			putmessage(outpipe_path, json.dumps({"shutdown":True}))
			while os.path.exists(lockfile_path) :
				time.sleep(0.1)
			if os.path.exists(runningfile_path) :
				os.remove(runningfile_path)
				
			# os.remove(runningfile_path)
			player.shutdown()
		else:
			# print(command)
			putmessage(outpipe_path, json.dumps({x : clients[x][1] for x in clients.keys()}))
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
	
