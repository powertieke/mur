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

messagequeue = queue.Queue()

def set_background(color):
	subprocess.call('sudo sh -c "TERM=linux setterm -background ' + color + ' >/dev/tty0"', shell=True)
	subprocess.call('sudo sh -c "TERM=linux setterm -clear >/dev/tty0"', shell=True)
	subprocess.call('sudo cat image.raw > /dev/fb0', shell=True)

def kill_all_omxplayers():
	subprocess.call("sudo killall omxplayer omxplayer.bin", shell=True)

def ready_player(moviefile, stopqueue, duration):
	player = pyomxplayer.OMXPlayer('"' + moviefile + '"', stopqueue, duration, None, True)
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
	print(duration)
	duration = int(duration) * 1000
	return duration

def loop_single_movies(moviefolder):
	playlist = [[moviefile, None, get_duration(moviefile)] for moviefile in glob.glob(moviefolder + "*.mp4")]
	i = 0
	playlist[i][1] = ready_player(playlist[i][0], messagequeue, playlist[i][2])
	playlist[i][1].toggle_pause()
	while True:
		if i == 0:
			nextmovieindex = 1
		elif i == len(playlist) - 1:
			nextmovieindex = 0
		else:
			nextmovieindex = i + 1
			
		message = messagequeue.get() # Wait for currently playing movie to end
		if message == "end":
			playlist[i][1].stop()
			playlist[i][1] = None
			try:
				kill_all_omxplayers()
			except:
				pass
			playlist[nextmovieindex][1] = ready_player(playlist[nextmovieindex][0], messagequeue, playlist[i][2])
			playlist[nextmovieindex][1].toggle_pause() #play next movie
			i = nextmovieindex
		elif message == "pause":
			playlist[i][1].toggle_pause()
		elif message == "endloop":
			playlist[i][1].stop()
			playlist[i][1] = None
			try:
				kill_all_omxplayers()
			except:
				pass
			break
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

def controller(incoming_from_controller, outgoing_to_controller, connection, udpport_sync):
	syncre = re.compile(r'^sync:(.*)')
	message = connection.recv(1024).decode("utf-8")
	print(message)
	if message == "skip":
		incoming_from_controller.put(message)
		connection.sendall(outgoing_to_controller.get().encode("utf-8"))
	elif syncre.match(message):
		moviefile = syncre.match(message).groups()[0]
		play_synced_movie(moviefile, outgoing_to_controller, udpport_sync)
		connection.sendall(outgoing_to_controller.get().encode('utf-8'))
		print('Sent GO!')
	elif message == "pause":
		incoming_from_controller.put(message)
		connection.sendall("ready".encode('utf-8'))
	else:
		connection.sendall("error".encode('utf-8'))
	
		
def play_synced_movie(moviefile, controllermessage, udpport_sync):
	syncqueue = queue.Queue()
	
	interruptor("endloop") # Kill main loop
	try:
		subprocess.call("sudo killall omxplayer omxplayer.bin", shell=True)
	except:
		pass
	
	syncThread = SyncThread("willekeur", udpport_sync, syncqueue)
	syncThread.start()
	
	player = ready_player(glob.glob(moviefile + "*.mp4")[0], syncqueue, get_duration(glob.glob(moviefile + "*.mp4")[0]))
	controllermessage.put("ready") # let the controlling pi know we're ready to go
	
	if syncqueue.get() == "go":
		tolerance = 200000.0
		player.toggle_pause() # Play synced movie
		print("Got go: playing")
		while True:
			syncmessage = syncqueue.get()
			if syncmessage == "pause":
				interruptor("pause")
				player.stop()
			elif syncmessage == "end":
				interruptor("pause") # Run main loop
				break
			else:
				masterposition = float(syncmessage)
				localposition = player.position
				print("Master: %s <--> Local: %s" % (masterposition, localposition))
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
		print(data)
		syncqueue.put(data)
	
class KillThread(threading.Thread):
	def __init__(self, name, duration, messagequeue):
		threading.Thread.__init__(self, name=name)
		self.duration = udpport_sync
		self.messagequeue = syncqueue
	def run(self):
		player_killtimer(self.duration, self.messagequeue)
		

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