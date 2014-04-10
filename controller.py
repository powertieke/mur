#!/usr/bin/python3

import sys
import os
import socket
import threading
import time
import queue
import player
import glob
from muur import syncloops
"""Holds all of the functions used if the app is ran with the -m (master) flag. Uses the network connections supplied by the clientfinder module to tell the screens what to do. Also yells out it's own playing position so the screens can time-correct themselves"""

def startSyncLoop(syncloops):
	if syncloops["clients"] != []:
		if not (all(c in foundclients for c in syncloops["clients"])):
			time.sleep(5)
		else:
			syncLoop = PlaySyncLoopThread("playsyncloop", syncloops["moviefile"], foundclients, udpport_sync, syncqueue, syncloops["repeats"], syncloops["intervalmoviefile"], syncloops["clients"])
			syncloop.run()

def startSyncThread(moviefile, clients, UDPPort_sync, syncqueue):
	syncThread = PlaySyncThread("playsync", moviefile, clients, UDPPort_sync, syncqueue)
	syncThread.run()

def message_to_pi(pi, message):
	"""Sends a message to the socket defined in pi, and returns the response"""
	pi[0].sendall(message.encode("utf-8"))
	pi[0].settimeout(10)
	try:
		result = pi[0].recv(1024).decode("utf-8")
	except socket.timeout:
		result = "TIMEOUT"
	pi[0].settimeout(None)
	return result

def play_single(moviefile, client):
	"""Tell a single client that you want it to play a single movie, blanking out any adjacent screens"""
	if (message_to_pi(client, "play:" + moviefile) == "playing"):
		# wait for interruption by interface or message of Pi
		return "Playing"

class PlaySyncThread(threading.Thread):
	def __init__(self, name, moviefile, clients, UDPPort_sync, syncqueue):
		threading.Thread.__init__(self, name=name)
		self.moviefile = moviefile
		self.clients = clients
		self.UDPPort_sync = UDPPort_sync
		self.syncqueue = syncqueue
		
	def run(self):
		play_sync(moviefile, clients, UDPPort_sync, syncqueue)
		startSyncLoop(syncloops)
		
		
class PlaySyncLoopThread(threading.Thread):
	def __init__(self, name, moviefile, clients, UDPPort_sync, syncqueue, repeats, intervalmovie, clientselection):
		threading.Thread.__init__(self, name=name)
		self.moviefile = moviefile
		self.clients = clients
		self.UDPPort_sync = UDPPort_sync
		self.syncqueue = syncqueue
		self.repeats = repeats
		self.intervalmovie = intervalmovie
		self.clientselection = clientselection
	
	def run(self):
		clientselection = {x : clients[x] for x in clientselection}
		if repeats == 0:
			while True:
				result = play_sync(moviefile, clientselection, UDPPort_sync, syncqueue)
				try:
					player.kill_all_omxplayers()
				except:
					pass
				if result == "stoploop":
					break
		else:
			while True:
				for _ in range(repeats):
					result = play_sync(moviefile, clientselection, UDPPort_sync, syncqueue)
					try:
						player.kill_all_omxplayers()
					except:
						pass
					if result == "stoploop":
						break
				result = play_sync(intervalmovie, clients, UDPPort_sync, syncqueue)
	
	
def play_sync(moviefile, clients, UDPPort_sync, syncqueue):
	for client in clients.keys():
		clients[client][1] = "2"
	"""Tell all of the screens present in 'clients' to get ready for playing 'moviefile'. Waits for every client to respond with 'Ready' (Which means the client has started OMXplayer with the corresponding movie)"""
	interval = 5
	waitforitqueue = queue.Queue()
	syncmessage = queue.Queue()
	# syncqueue = queue.Queue()
	syncplayer = player.ready_player(moviefile + ".mp4", syncqueue, player.get_duration(moviefile + ".mp4"))
	# print(clients)
	for client in clients:
		waitforitqueue.put(True)
	for client in clients:
		tellClientsToSyncThread = TellClientsToSyncThread(client[0], clients[client], moviefile, waitforitqueue)
		tellClientsToSyncThread.start()
	waitforitqueue.join()
	# print('everyone on board')
	time.sleep(1)
	syncScreamerThread = SyncScreamerThread("SCREAMFORME", UDPPort_sync, syncmessage)
	syncScreamerThread.start()
	syncplayer.toggle_pause()
	while True:
		try:
			msg = syncqueue.get(True, 0.5)
			syncmessage.put(msg)
			break
		except queue.Empty:
			syncmessage.put(syncplayer.position)
		else:
			break
	for client in clients.keys():
		clients[client][1] = "0"	
	return msg

def syncscreamer(udpport_sync, syncmessage):
	syncscreamer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	syncscreamer.sendto("go".encode('utf-8'), ("224.0.0.1", udpport_sync))
	while True:
		message = syncmessage.get()
		# print(message)
		syncscreamer.sendto(str(message).encode('utf-8'), ("224.0.0.1", udpport_sync))
		print("message")
		if message == "end":
			break
	syncscreamer.close()

def tell_client_to_sync(pi, movie, waitforitqueue):
	waitforitqueue.get()
	message_to_pi(pi, ("sync:" + movie))
	waitforitqueue.task_done()
	
	
			
class TellClientsToSyncThread(threading.Thread):
	def __init__(self, name, piname, movie, waitforitqueue):
		threading.Thread.__init__(self, name=name)
		self.piname = piname
		self.movie = movie
		self.waitforitqueue = waitforitqueue
	
	def run(self):
		tell_client_to_sync(self.piname, self.movie, self.waitforitqueue)
	
class SyncScreamerThread(threading.Thread):
	def __init__(self, name, UDPPort_sync, syncmessage):
		threading.Thread.__init__(self, name=name)
		self.UDPPort_sync = UDPPort_sync
		self.syncmessage = syncmessage
	
	def run(self):
		syncscreamer(self.UDPPort_sync, self.syncmessage)