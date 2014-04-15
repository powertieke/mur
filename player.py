#!/usr/bin/python3

import sys
import os
import pyomxplayer
import threading
import collections
import glob
import queue
import re
import socket
import time
import subprocess
import client
from random import shuffle



def set_background(color):
	subprocess.call('sudo sh -c "TERM=linux setterm -background ' + color + ' >/dev/tty0"', shell=True)
	subprocess.call('sudo sh -c "TERM=linux setterm -clear >/dev/tty0"', shell=True)
	subprocess.call('sudo sh -c "TERM=linux setterm -cursor off >/dev/tty0"', shell=True)
	# subprocess.call('sudo cat image.raw > /dev/fb0 2>> /home/pi/mur.log', shell=True)

def kill_all_omxplayers():
	subprocess.call("sudo killall omxplayer omxplayer.bin 2>>  /dev/null", shell=True)

def ready_player(moviefile, stopqueue, duration):
	retry = 0
	while True:
		try:
			player = pyomxplayer.OMXPlayer('"' + moviefile + '"', stopqueue, duration, "-o hdmi", True)
		except:
			print("Failed loading: Retry %s" % retry)
			if retry < 2:
				retry = retry + 1
			else:
				raise RuntimeError("Failed to open OMXplayer. Filename: %s" % moviefile)
				status = "-1"
		else:
			break
	position = 200000
	while player.position < position:
		pass
	overshoot = player.position - position
	time.sleep((180000 - overshoot)/1000000)
	player.toggle_pause()
	time.sleep(1)
	return player

def show_splash_screen(image):
	command = "fbi \"%s\"" % image
	return subprocess.Popen(command, shell = True)
	
def get_duration(moviefile):
	proc = subprocess.Popen('/usr/bin/mediainfo --Inform="General;%Duration%" "' + moviefile + '"', shell=True, stdout=subprocess.PIPE)
	duration, rest = proc.communicate()
	# print(duration)
	duration = int(duration) * 1000
	return duration

def loop_single_movies(moviefolder, incoming_from_controller, outgoing_to_controller, udpport_sync, clientname):
	status = "0"
	playlist = [[moviefile, None, get_duration(moviefile)] for moviefile in glob.glob(moviefolder + "*.mp4")]
	shuffle(playlist)
	i = 0
	nextmovieindex = 1
	playlist[i][1] = ready_player(playlist[i][0], incoming_from_controller, playlist[i][2])
	playlist[i][1].toggle_pause()
	while True: ## Main movie playing loop - Listens on incoming_from_controller queue
		message = incoming_from_controller.get() # Wait for currently playing movie to end or for an incoming servermessage
		if message == "end":
			if i == 0:
				nextmovieindex = 1
			elif i == len(playlist) - 1:
				nextmovieindex = 0
			else:
				nextmovieindex = i + 1
			
			try:
				playlist[i][1].stop()
			except:
				pass
			playlist[i][1] = None
			try:
				kill_all_omxplayers()
			except:
				pass
			playlist[nextmovieindex][1] = ready_player(playlist[nextmovieindex][0], incoming_from_controller, playlist[nextmovieindex][2])
			playlist[nextmovieindex][1].toggle_pause() #play next movie
			i = nextmovieindex
		elif message == "status":
			outgoing_to_controller.put(status)
		elif message[0] == "sync":
			print("got sync")
			try:
				playlist[i][1].stop()
			except:
				pass
			playlist[i][1] = None
			try:
				kill_all_omxplayers()
			except:
				pass
				
			play_synced_movie(message[1], incoming_from_controller, outgoing_to_controller, udpport_sync, clientname)
			i = nextmovieindex
		elif message[0] == "play":
			try:
				playlist[i][1].stop()
			except:
				pass
			playlist[i][1] = None
			try:
				kill_all_omxplayers()
			except:
				pass
			try:
				incoming_from_controller.get(True)
			except queue.empty:
				pass
			playlist[nextmovieindex][1] = ready_player(message[1], incoming_from_controller, get_duration(message[1]))
			playlist[nextmovieindex][1].toggle_pause() #play next movie
			outgoing_to_controller.put(clientname + " is playing :" + message[1])
			i = nextmovieindex
			
			
			
class LoopSingleMoviesThread(threading.Thread):
	def __init__(self, moviefolder, incoming_from_controller, outgoing_to_controller, udpport_sync, clientname, name='threadmeister'):
		threading.Thread.__init__(self, name=name)
		self.moviefolder = moviefolder
		self.udpport_sync = udpport_sync
		self.incoming_from_controller = incoming_from_controller
		self.outgoing_to_controller = outgoing_to_controller
		self.clientname = clientname
	def run(self):
		loop_single_movies(self.moviefolder, self.incoming_from_controller, self.outgoing_to_controller, self.udpport_sync, self.clientname)
		
def interruptor(message, argument=None):
	if argument == None:
		messagequeue.put(message)
	else:
		messagequeue.put((message, argument))

def stat(statsocket):
	status = "0"
	while True:
		try:
			message = statsocket.recv(1024).decode("utf-8")
		except:
			status = "-1"
			break
		try:
			statsocket.sendall(status.encode("utf-8"))
		except:
			status = "-1"
			break

def controller(incoming_from_controller, outgoing_to_controller, connection, udpport_sync, udpport_discovery, tcpport, statport, clientname):
	syncre = re.compile(r'^sync:(.*)$')
	skipre = re.compile(r'^skip:(.*)$')
	playre = re.compile(r'^play:(.*)$')
	while (True):
		try:
			message = connection.recv(1024).decode("utf-8")
			print("This just in: %s" % message)
		except:
			print("lostconnection")
			clientsocket, statsocket = client.find_controller(clientname, udpport_discovery, tcpport, statport)
			statThread = StatThread("statthread", statsocket)
			statThread.daemon = True
			statThread.start()
			controller(incoming_from_controller, outgoing_to_controller, clientsocket, udpport_sync, udpport_discovery, tcpport, statport, clientname)
			break
		if message == "skip":
			incoming_from_controller.put(message)
			connection.sendall(outgoing_to_controller.get().encode("utf-8"))
		elif syncre.match(message):
			moviefile = syncre.match(message).group(1)
			incoming_from_controller.put(["sync", moviefile])
			# play_synced_movie(moviefile, outgoing_to_controller, udpport_sync)
			connection.sendall(outgoing_to_controller.get().encode('utf-8'))
		elif playre.match(message):
			moviefile = playre.match(message).group(1)
			incoming_from_controller.put(["play", moviefile])
			connection.sendall(outgoing_to_controller.get().encode('utf-8'))
		elif skipre.match(message):
			times = playre.match(message).group(1)
			incoming_from_controller.put(["skip", times])
			connection.sendall(outgoing_to_controller.get().encode('utf-8'))
		elif message == "pause":
			incoming_from_controller.put(message)
			connection.sendall("ready".encode('utf-8'))
		elif message == "status":
			connection.sendall(status.encode('utf-8'))
			if status == "-1":
				connection.close()
				raise RuntimeError("Failed loading moviefile. Stopping")
		elif message == '':
			connection.close()
			print("lostconnection")
			clientsocket, statsocket = client.find_controller(clientname, udpport_discovery, tcpport, statport)
			statThread = StatThread("statthread", statsocket)
			statThread.daemon = True
			statThread.start()
			controller(incoming_from_controller, outgoing_to_controller, clientsocket, udpport_sync, udpport_discovery, tcpport, statport, clientname)
			break
		else:
			connection.sendall("error".encode('utf-8'))
	
	
		
def play_synced_movie(moviefile, incoming_from_controller, outgoing_to_controller, udpport_sync, clientname):
	syncqueue = queue.Queue()
	
	syncThread = SyncThread("willekeur", udpport_sync, syncqueue)
	syncThread.start()
	
	
	if os.path.exists(moviefile + clientname + ".mp4"):
		player = ready_player(moviefile + clientname + ".mp4", syncqueue, get_duration(moviefile + clientname + ".mp4"))
	elif os.path.exists(moviefile + ".mp4"):
		player = ready_player(moviefile + ".mp4", syncqueue, get_duration(moviefile + ".mp4"))
		
	while syncqueue.empty() == False:
		syncqueue.get()
	outgoing_to_controller.put("ready") # let the controlling pi know we're ready to go
	
	if syncqueue.get() == "go":
		tolerance = 500000.0
		player.toggle_pause() # Play synced movie
		# print("Got go: playing")
		insync = 0
		while True:
			syncmessage = syncqueue.get()
			if syncmessage == "end":
				player.stop()
				try:
					kill_all_omxplayers()
				except:
					pass
					
				# incoming_from_controller.put("end")
				break
			elif insync > 6:
				pass # Stayed in sync for three seconds
				masterposition = float(syncmessage)
				localposition = player.position
			else:
				masterposition = float(syncmessage)
				localposition = player.position
				syncqueue.put(True)
				if masterposition + tolerance < localposition:
					adjustment = (localposition - masterposition) / 1000000.
					delay = adjustment - 0.05
					player.toggle_pause()
					if delay < 0.2:
						delay = 0
					time.sleep(delay)
					player.toggle_pause()
					insync = 0
					syncqueue.get()
				elif masterposition - tolerance > localposition:
					player.increase_speed()
					adjustment = (masterposition - localposition) / 1000000.
					delay = (adjustment * 2.0)
					if delay < 0.1:
						 delay = 0.1
					time.sleep(delay)
					player.decrease_speed()
					insync = 0
					syncqueue.get()
				else :
					insync = insync + 1
					syncqueue.get()
				
def sync_listener(udpport_sync, syncqueue):
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind(("", udpport_sync))
	while True:
		data = s.recv(1024).decode("utf-8")
		if syncqueue.empty():
			syncqueue.put(data)
		if data == "end":
			syncqueue.put(data)
			s.close()
			break
	
class StatThread(threading.Thread):
	def __init__(self, name, statsocket):
		threading.Thread.__init__(self, name=name)
		self.statsocket = statsocket
	def run(self):
		stat(self.statsocket)

class SyncThread(threading.Thread):
	def __init__(self, name, udpport_sync, syncqueue):
		threading.Thread.__init__(self, name=name)
		self.udpport = udpport_sync
		self.syncqueue = syncqueue
	def run(self):
		sync_listener(self.udpport, self.syncqueue)

def test(moviefolder):
	loop_single_movies(moviefolder)
		
if __name__ == "__main__":
	test("~/movies/")