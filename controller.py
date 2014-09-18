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

moviefolder = "/home/pi/movies"

"""Holds all of the functions used if the app is ran with the -m (master) flag. Uses the network connections supplied by the clientfinder module to tell the screens what to do. Also yells out it's own playing position so the screens can time-correct themselves"""

def play_threaded_sync_loop(moviefile, clients, UDPPort_sync, killqueue, repeats, intervalmovie, clientselectionlist):
	
	if repeats == 0:
		while True:
			clientselection = {x : clients[x] for x in clientselectionlist if x in clients}
			result = play_sync(moviefolder + "/Sync/" + moviefile, clientselection, UDPPort_sync, killqueue)
			try:
				player.kill_all_omxplayers()
			except:
				pass
			if result == "kill":
				try:
					player.kill_all_omxplayers()
				except:
					pass
				killqueue.get()
				print("Got to the end of loop")
	else:
		while True:
			for _ in range(repeats):
				clientselection = {x : clients[x] for x in clientselectionlist if x in clients}
				result = play_sync(moviefolder + "/Sync/" + moviefile, clientselection, UDPPort_sync, killqueue)
				print(result)
				try:
					player.kill_all_omxplayers()
				except:
					pass
				if result == "kill":
					try:
						player.kill_all_omxplayers()
					except:
						pass
					# print("wait for another kill")
					killqueue.get()
					print("Got to the end of inner loop")
			result = play_sync(moviefolder + "/Sync/" + intervalmovie, clients, UDPPort_sync, killqueue)
			if result == "kill":
				try:
					player.kill_all_omxplayers()
				except:
					pass
				killqueue.get()
	

def play_threaded_sync(moviefile, clients, UDPPort_sync, killqueue):
	syncqueue = queue.Queue()
	play_sync(moviefile, clients, UDPPort_sync, syncqueue)
	killqueue.put("kill")
	

def startSyncLoop(syncloops, foundclients, UDPPort_sync, killqueue):
	start = False
	while start == False:
		if syncloops["clients"] != []:
			if not (all(c in foundclients for c in syncloops["clients"])):
				# print(foundclients)
				# print("pi's not all here. Stopping for 5")
				time.sleep(5)
			else:
				# print("start syncloop")
				syncloop = PlaySyncLoopThread("playsyncloop", syncloops["moviefile"], foundclients, UDPPort_sync, killqueue, syncloops["repeats"], syncloops["intervalmoviefile"], syncloops["clients"])
				syncloop.start()
				# print("start syncloop done")
				start = True

def startSyncThread(moviefile, clients, UDPPort_sync, killqueue):
	while killqueue.empty() == False:
		time.sleep(0.5)
	syncThread = PlaySyncThread("playsync", moviefile, clients, UDPPort_sync, killqueue)
	syncThread.start()

def message_to_pi(pi, message):
	"""Sends a message to the socket defined in pi, and returns the response"""
	try:
		pi[0].sendall(message.encode("utf-8"))
	except socket.error:
		result = "UNREACH"
		
	pi[0].settimeout(10)
	try:
		result = pi[0].recv(1024).decode("utf-8")
	except socket.timeout:
		result = "TIMEOUT"
	except socket.error:
		result = "DISCONN"
	pi[0].settimeout(None)
	return result

def play_single(moviefile, client):
	"""Tell a single client that you want it to play a single movie, blanking out any adjacent screens"""
	client[1] = message_to_pi(client, "play:" + moviefile)

class PlaySyncThread(threading.Thread):
	def __init__(self, name, moviefile, clients, UDPPort_sync, killqueue):
		threading.Thread.__init__(self, name=name)
		self.moviefile = moviefile
		self.clients = clients
		self.UDPPort_sync = UDPPort_sync
		self.killqueue = killqueue
		
	def run(self):
		play_threaded_sync(self.moviefile, self.clients, self.UDPPort_sync, self.killqueue)
		
		
class PlaySyncLoopThread(threading.Thread):
	def __init__(self, name, moviefile, clients, UDPPort_sync, killqueue, repeats, intervalmovie, clientselection):
		threading.Thread.__init__(self, name=name)
		self.moviefile = moviefile
		self.clients = clients
		self.UDPPort_sync = UDPPort_sync
		self.killqueue = killqueue
		self.repeats = repeats
		self.intervalmovie = intervalmovie
		self.clientselection = clientselection
	
	def run(self):
		play_threaded_sync_loop(self.moviefile, self.clients, self.UDPPort_sync, self.killqueue, self.repeats, self.intervalmovie, self.clientselection)
	
	
def play_sync(moviefile, clients, UDPPort_sync, killqueue):
	for client in clients.keys():
		clients[client][1] = "2"
	"""Tell all of the screens present in 'clients' to get ready for playing 'moviefile'. Waits for every client to respond with 'Ready' (Which means the client has started OMXplayer with the corresponding movie)"""
	interval = 5
	waitforitqueue = queue.Queue()
	syncmessage = queue.Queue()
	syncqueue = queue.Queue()
	syncplayer = player.ready_player(moviefile + ".mp4", syncqueue)
	print(clients)
	for client in clients:
		waitforitqueue.put(True)
	for client in clients:
		tellClientsToSyncThread = TellClientsToSyncThread(client[0], clients[client], moviefile, waitforitqueue)
		tellClientsToSyncThread.start()
	waitforitqueue.join()
	print('everyone on board')
	time.sleep(1)
	syncScreamerThread = SyncScreamerThread("SCREAMFORME", UDPPort_sync, syncmessage)
	syncScreamerThread.start()
	print("Screamer started")
	syncplayer.toggle_pause()
	print("Unpaused movie")
	while True:
		try:
			killmessage = killqueue.get(False)
		except queue.Empty:
			killmessage = False
		if killmessage != False:
			syncqueue.put("end")
		try:
			msg = syncqueue.get(True, 0.5)
			syncmessage.put(msg)
			print("syncmessage: " + msg)
			break
		except queue.Empty:
			try:
				syncmessage.put(syncplayer.get_position())
				print("Sucessfully got position")
			except:
				print("Could not get position for file: " + moviefile)
				pass
		else:
			break
	for client in clients.keys():
		clients[client][1] = "0"
	if killmessage != False:
		msg = killmessage
		print("Got Killmessage")
	return msg

def syncscreamer(udpport_sync, syncmessage):
	syncscreamer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	syncscreamer.sendto("go".encode('utf-8'), ("224.0.0.1", udpport_sync))
	print("Sent: %s" % "go")
	while True:
		message = syncmessage.get()
		print(message)
		syncscreamer.sendto(str(message).encode('utf-8'), ("224.0.0.1", udpport_sync))
		print("Sent: %s" % message)
		if message == "end":
			while syncmessage.empty() == False:
				syncmessage.get()
			break
	syncscreamer.close()

def tell_client_to_sync(pi, movie, waitforitqueue):
	waitforitqueue.get()
	pi[1] = message_to_pi(pi, ("sync:" + movie))
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