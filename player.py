#!/usr/bin/python3

import sys
import os
import pyomxplayer
import threading
import collections
import glob
import queue
import re

messagequeue = queue.Queue()

def ready_player(moviefile, stopqueue):
	player = pyomxplayer.OMXPlayer('"' + moviefile + '"', stopqueue, None, True)
	position = player.position
	while player.position == position:
		pass
		
	player.toggle_pause()
	return player
	
def loop_single_movies(moviefolder):
	playlist = [[moviefile, None] for moviefile in glob.glob(moviefolder + "*.mp4")]
	i = 0
	playlist[i][1] = ready_player(playlist[i][0], messagequeue)
	playlist[i][1].toggle_pause()
	while True:
		if i == 0:
			nextmovieindex = 1
		elif i == len(playlist) - 1:
			nextmovieindex = 0
		else:
			nextmovieindex = i + 1
			
		playlist[nextmovieindex][1] = ready_player(playlist[nextmovieindex][0], messagequeue)
		message = messagequeue.get() # Wait for currently playing movie to end
		if message == "end":
			playlist[nextmovieindex][1].toggle_pause() #play next movie
			playlist[i][1].stop()
			playlist[i][1] = None
			i = nextmovieindex
		elif message == "pause":
				playlist[i][1].toggle_pause()
		elif message[0] == "skip":
			if message[1] != None:
				nextmovieindex = message[1]
			playlist[nextmovieindex][1].toggle_pause()
			playlist[i][1].stop()
			playlist[i][1] = None
			i = nextmovieindex
		
			
class LoopSingleMoviesThread(threading.Thread):
	def __init__(self, moviefolder, name='threadmeister'):
		threading.Thread.__init__(self, name=name)
		self.moviefolder = moviefolder
	def run(self):
		loop_single_movies(self.moviefolder)
		
def interruptor(message, argument=None):
	if argument == None:
		messagequeue.put(message)
	else:
		messagequeue.put((message, argument))

def controller(incoming_from_controller, outgoing_to_controller, connection):
	syncre = re.compile(r'^sync:(.*)')
	message = connection.recv(1024).decode("utf-8")
	print(message)
	if message == "skip":
		incoming_from_controller.put(message)
		connection.sendall(outgoing_to_controller.get().encode("utf-8"))
	elif syncre.match(message):
		moviefile = syncre.match(message).groups()[0]
		play_synced_movie(moviefile, outgoing_to_controller)
		connection.sendall(outgoing_to_controller.get().encode('utf-8'))
	elif message == "pause":
		incoming_from_controller.put(message)
		connection.sendall("ready".encode('utf-8'))
	else:
		connection.sendall("error".encode('utf-8'))
	
		
def play_synced_movie(moviefile, controllermessage):
	syncqueue = queue.Queue()
	
	syncThread = SyncThread(udpport_sync)
	syncThread.start()
	
	player = ready_player(glob.glob(moviefile + "*.mp4")[0])
	controllermessage.put("ready") # let the controlling pi know we're ready to go
	
	if syncqueue.get() == "go":
		player.toggle_pause() # Play synced movie
		interruptor("pause") # Pause main loop
		syncmessage = syncqueue.get()
		if syncmessage == "pause":
			interruptor("pause")
			player.stop()
		else:
			masterposition = int(syncmessage)
			if masterposition + tolerance > player.position:
				player.toggle_pause()
				time.sleep(0.1)
				player.toggle_pause()
			elif masterposition - tolerance < player.position:
				player.increase_speed()
				time.sleep(0.5)
				player.toggle_pause()
		
def sync_listener(udpport_sync, syncqueue):
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind(("", udpport_sync))
	while True:
		data = s.recv(1024).decode("utf-8")
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