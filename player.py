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
from random import shuffle



def set_background(color):
	# subprocess.call('sudo sh -c "TERM=linux setterm -background ' + color + ' >/dev/tty0"', shell=True)
	# subprocess.call('sudo sh -c "TERM=linux setterm -clear >/dev/tty0"', shell=True)
	subprocess.call('sudo cat image.raw > /dev/fb0 2>> /home/pi/mur.log', shell=True)

def kill_all_omxplayers():
	subprocess.call("sudo killall omxplayer omxplayer.bin 2>>  /home/pi/mur.log", shell=True)

def ready_player(moviefile, stopqueue, duration):
	player = pyomxplayer.OMXPlayer('"' + moviefile + '"', stopqueue, duration, "-o hdmi", True)
	position = player.position
	while player.position == position:
		pass
		
	player.toggle_pause()
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
	status = "starting"
	playlist = [[moviefile, None, get_duration(moviefile)] for moviefile in glob.glob(moviefolder + "*.mp4")]
	shuffle(playlist)
	i = 0
	playlist[i][1] = ready_player(playlist[i][0], incoming_from_controller, playlist[i][2])
	playlist[i][1].toggle_pause()
	status = "playing:" + playlist[i][0]
	while True: ## Main movie playing loop - Listens on incoming_from_controller queue
		print("waiting...")
		message = incoming_from_controller.get() # Wait for currently playing movie to end or for an incoming servermessage
		print("Gotsome")
		if message == "end":
			print("got end")
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
			playlist[nextmovieindex][1] = ready_player(playlist[nextmovieindex][0], incoming_from_controller, playlist[i][2])
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
				
			print("killed players. Starting sync")
			play_synced_movie(message[1], incoming_from_controller, outgoing_to_controller, udpport_sync, clientname)
			print("Got to the end of this fucker")
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
			print(message[1])
			playlist[nextmovieindex][1] = ready_player(message[1], incoming_from_controller, get_duration(message[1]))
			playlist[nextmovieindex][1].toggle_pause() #play next movie
			outgoing_to_controller.put(clientname + " is playing :" + message[1])
			
			
			
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

def controller(incoming_from_controller, outgoing_to_controller, connection, udpport_sync):
	syncre = re.compile(r'^sync:(.*)$')
	skipre = re.compile(r'^skip:(.*)$')
	playre = re.compile(r'^play:(.*)$')
	while (True):
		message = connection.recv(1024).decode("utf-8")
		print(message)
		if message == "skip":
			incoming_from_controller.put(message)
			connection.sendall(outgoing_to_controller.get().encode("utf-8"))
		elif syncre.match(message):
			moviefile = syncre.match(message).group(1)
			incoming_from_controller.put(["sync", moviefile])
			# play_synced_movie(moviefile, outgoing_to_controller, udpport_sync)
			connection.sendall(outgoing_to_controller.get().encode('utf-8'))
			print('Sent GO!')
		elif playre.match(message):
			moviefile = playre.match(message).group(1)
			incoming_from_controller.put(["play", moviefile])
			connection.sendall(outgoing_to_controller.get().encode('utf-8'))
			print("sent done")
		elif skipre.match(message):
			times = playre.match(message).group(1)
			incoming_from_controller.put(["skip", times])
			connection.sendall(outgoing_to_controller.get().encode('utf-8'))
			print("sent")
		elif message == "pause":
			incoming_from_controller.put(message)
			connection.sendall("ready".encode('utf-8'))
		else:
			connection.sendall("error".encode('utf-8'))
	
	
		
def play_synced_movie(moviefile, incoming_from_controller, outgoing_to_controller, udpport_sync, clientname):
	syncqueue = queue.Queue()
	
	print("starting syncthread")
	
	syncThread = SyncThread("willekeur", udpport_sync, syncqueue)
	syncThread.start()
	
	print("syncthread started")
	
	player = ready_player(moviefile + clientname + ".mp4", syncqueue, get_duration(moviefile + clientname + ".mp4"))
	outgoing_to_controller.put("ready") # let the controlling pi know we're ready to go
	
	if syncqueue.get() == "go":
		tolerance = 200000.0
		player.toggle_pause() # Play synced movie
		# print("Got go: playing")
		while True:
			syncmessage = syncqueue.get(True, 10)
			if syncmessage == "end":
				print("gotend")
				incoming_from_controller.put("end")
				break
			else:
				masterposition = float(syncmessage)
				localposition = player.position
				# print("Master: %s <--> Local: %s" % (masterposition, localposition))
				if masterposition + tolerance < localposition:
					player.toggle_pause()
					time.sleep(0.2)
					player.toggle_pause()
				elif masterposition - tolerance > localposition:
					player.increase_speed()
					time.sleep(0.5)
					player.toggle_pause()
		
def sync_listener(udpport_sync, syncqueue):
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind(("", udpport_sync))
	while True:
		data = s.recv(1024).decode("utf-8")
		# print(data)
		syncqueue.put(data)
	

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