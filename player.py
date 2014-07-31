#!/usr/bin/python3

import sys
import os
import pyomxplayer
import domxplayer

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

status = "0"

def clearqueue(thequeue):
	while thequeue.empty() == False:
		thequeue.get()

def set_background(color):
	subprocess.call('sudo sh -c "TERM=linux setterm -background ' + color + ' >/dev/tty0"', shell=True)
	subprocess.call('sudo sh -c "TERM=linux setterm -clear >/dev/tty0"', shell=True)
	subprocess.call('sudo sh -c "TERM=linux setterm -cursor off >/dev/tty0"', shell=True)
	# subprocess.call('sudo cat image.raw > /dev/fb0 2>> /home/pi/mur.log', shell=True)

def kill_all_omxplayers():
	subprocess.call("sudo killall omxplayer omxplayer.bin 2>>  /dev/null", shell=True)

def ready_player(moviefile, stopqueue):
	player = domxplayer.OMXPlayer(moviefile, stopqueue)
	return player

def show_splash_screen(image):
	command = "fbi \"%s\"" % image
	return subprocess.Popen(command, shell = True)
	
def get_duration(moviefile):
	retry = 0
	while True:
		try:
			proc = subprocess.Popen('/usr/bin/mediainfo --Inform="General;%Duration%" "' + moviefile + '"', shell=True, stdout=subprocess.PIPE)
			duration, rest = proc.communicate()
			# print(duration)
			duration = int(duration) * 1000
		except ValueError:
			if retry < 2:
				retry = retry + 1
				time.sleep(0.5)
			else:
				reboot()
		else:
			break
	return duration

def loop_single_movies(moviefolder, incoming_from_controller, outgoing_to_controller, udpport_sync, clientname):
	global status
	playlist = [[moviefile, None] for moviefile in glob.glob(moviefolder + "*.mp4")]
	shuffle(playlist)
	i = 0
	nextmovieindex = 1
	playlist[i][1] = ready_player(playlist[i][0], incoming_from_controller)
	playlist[i][1].toggle_pause()
	playlist[nextmovieindex][1] = ready_player(playlist[nextmovieindex][0], incoming_from_controller)
	while True: ## Main movie playing loop - Listens on incoming_from_controller queue
		message = incoming_from_controller.get() # Wait for currently playing movie to end or for an incoming servermessage
		if message == "end":
			print("I ARE ENDED")
			status = "0"
			if i == 0:
				nextmovieindex = 1
			elif i == len(playlist) - 1:
				nextmovieindex = 0
			else:
				nextmovieindex = i + 1
			
			playlist[nextmovieindex][1].toggle_pause() #play next movie
			if not playlist[i][1].stopped:
				playlist[i][1].stop()
			playlist[i][1] = None
			i = nextmovieindex
			if i == 0:
				nextmovieindex = 1
			elif i == len(playlist) - 1:
				nextmovieindex = 0
			else:
				nextmovieindex = i + 1
			playlist[nextmovieindex][1] = ready_player(playlist[nextmovieindex][0], incoming_from_controller)
		elif message == "status":
			outgoing_to_controller.put(status)
		elif message[0] == "sync":
			status = "1"
			if i == 0:
				nextmovieindex = 1
			elif i == len(playlist) - 1:
				nextmovieindex = 0
			else:
				nextmovieindex = i + 1
			
			# print("got sync")
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
			playlist[nextmovieindex][1].toggle_pause() #play next movie
			i = nextmovieindex
		elif message[0] == "play":
			status = "2"
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
				incoming_from_controller.get(False)
			except queue.Empty:
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
	global status
	while True:
		try:
			statsocket.settimeout(5)
			data = statsocket.recv(1024)
			message = data.decode("utf-8")
			# print("Statsocket in : %s" % message)
			statsocket.settimeout(None)
		except socket.error:
			status = "-1"
			# print("Error on reading from statsocket. Closing.")
			statsocket.close()
			break
		except socket.timeout:
			status = "-1"
			# print("Timeout on reading from statsocket. Closing.")
			statsocket.close()
			break
		try:
			statsocket.sendall(status.encode("utf-8"))
		except socket.error:
			status = "-1"
			# print("Error on writing to statsocket. Closing")
			statsocket.close()
			break
		if data == b'':
			status = "-1"
			# print("Timeout on reading from statsocket. Closing.")
			statsocket.close()
			break
			

def controller(incoming_from_controller, outgoing_to_controller, connection, udpport_sync, udpport_discovery, tcpport, statport, clientname):
	syncre = re.compile(r'^sync:(.*)$')
	skipre = re.compile(r'^skip:(.*)$')
	playre = re.compile(r'^play:(.*)$')
	while (True):
		try:
			data = connection.recv(1024)
			if data == b'':
				# print("lostconnection to broken connection")
				break
			message = data.decode("utf-8")
		except:
			# print("lostconnection to error")
			break
		if message == "skip":
			incoming_from_controller.put(message)
			connection.sendall(outgoing_to_controller.get().encode("utf-8"))
		elif syncre.match(message):
			moviefile = syncre.match(message).group(1)
			incoming_from_controller.put(["sync", moviefile])
			# play_synced_movie(moviefile, outgoing_to_controller, udpport_sync)
			connection.settimeout(15)
			try:
				connection.sendall(outgoing_to_controller.get(True, 15).encode('utf-8'))
			except queue.Empty:
				# print("Response timed out on Player side.")
				connection.settimeout(None)
				clearqueue(outgoing_to_controller)
				pass
			except socket.timeout:
				# print("Response timed out while sending.")
				connection.settimeout(None)
				clearqueue(outgoing_to_controller)
				pass
			except socket.error:
				# print("Something is wrong with the connection, will handle later")
				connection.settimeout(None)
				clearqueue(outgoing_to_controller)
				break
			connection.settimeout(None)
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
		elif message == "reboot":
			connection.sendall("-1".encode('utf-8'))
			reboot()
		elif message == "update":
			connection.sendall("-1".encode('utf-8'))
			reboot(True)
		elif message == "shutdown":
			connection.sendall("-1".encode('utf-8'))
			shutdown()
		elif message == "status":
			connection.sendall(status.encode('utf-8'))
		elif message == '':
			pass
		else:
			connection.sendall("error".encode('utf-8'))
	
	
	
		
def play_synced_movie(moviefile, incoming_from_controller, outgoing_to_controller, udpport_sync, clientname):
	syncqueue = queue.Queue()
	killsyncqueue = queue.Queue()
	
	syncThread = SyncThread("willekeur", udpport_sync, syncqueue, killsyncqueue)
	syncThread.start()
	
	if os.path.exists(moviefile + clientname + ".mp4"):
		player = ready_player(moviefile + clientname + ".mp4", syncqueue)
	elif os.path.exists(moviefile + ".mp4"):
		player = ready_player(moviefile + ".mp4", syncqueue)
		
	while syncqueue.empty() == False:
		syncqueue.get()
	outgoing_to_controller.put("ready") # let the controlling pi know we're ready to go
	try:
		if syncqueue.get(True, 10) == "go":
			tolerance = 500000.0
			player.toggle_pause() # Play synced movie
			# print("Got go: playing")
			insync = 0
			while True:
				try:
					syncmessage = syncqueue.get(True, 10)
				except queue.Empty:
					# print("Message timed out. Ending it")
					syncmessage == "end"
				# print(syncmessage)
				if (syncmessage == "end") or (syncmessage == "go"):
					player.stop()
					break
				elif insync > 6:
					pass # Stayed in sync for three seconds
					masterposition = float(syncmessage)
					localposition = player.get_position()
				else:
					masterposition = float(syncmessage)
					localposition = player.get_position()
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
		else:
			# print("Got something else instead of go. Resuming normal play")
			clearqueue(outgoing_to_controller)
			try:
				player.stop()
			except:
				pass
	except queue.Empty:
		clearqueue(outgoing_to_controller)
		# print("Timed Out while waiting for the go")
		try:
			player.stop()
		except:
			pass
	except UnboundLocalError:
		clearqueue(outgoing_to_controller)
		# print("OMXplayer got killed before we got the go")
		try:
			player.stop()
		except:
			pass
	killsyncqueue.put(True)
		
		
def sync_listener(udpport_sync, syncqueue, killsyncqueue):
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind(("", udpport_sync))
	while True:
		try:
			killsyncqueue.get(False)
		except queue.Empty:
			pass
		else:
			break
		s.settimeout(10)
		try:
			data = s.recv(1024).decode("utf-8")
		except socket.timeout:
			break
		if syncqueue.empty():
			syncqueue.put(data)
		if data == "end":
			break
	syncqueue.put("end")
	s.close()
	# print("syncthread finished")
	
class StatThread(threading.Thread):
	def __init__(self, name, statsocket):
		threading.Thread.__init__(self, name=name)
		self.statsocket = statsocket
	def run(self):
		stat(self.statsocket)

class SyncThread(threading.Thread):
	def __init__(self, name, udpport_sync, syncqueue, killsyncqueue):
		threading.Thread.__init__(self, name=name)
		self.udpport = udpport_sync
		self.syncqueue = syncqueue
		self.killsyncqueue = killsyncqueue
	def run(self):
		sync_listener(self.udpport, self.syncqueue, self.killsyncqueue)

def reboot(update=False):
	if update == True:
		thecommand = "cd /home/mur; git pull; reboot"
	else:
		thecommand = "reboot"
	subprocess.call(thecommand, shell=True)
	
def shutdown(update=False):
	if update == True:
		thecommand = "cd /home/mur; git pull; shutdown -h now"
	else:
		thecommand = "shutdown -h now"
	subprocess.call(thecommand, shell=True)


def test(moviefolder):
	loop_single_movies(moviefolder)
		
if __name__ == "__main__":
	test("~/movies/")