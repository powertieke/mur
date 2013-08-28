#!/usr/bin/python3

import sys
import os
import socket
import threading
import time
import queue
import player
import glob

def message_to_pi(pi, message):
	pi[0].sendall(message.encode("utf-8"))
	pi[0].settimeout(5)
	try:
		result = pi[0].recv(1024).decode("utf-8")
	except socket.timeout:
		result = "TIMEOUT"
	pi[0].settimeout(None)
	return result
	
def play_sync(moviefile, clients, UDPPort_sync):
	interval = 5
	waitforitqueue = queue.Queue()
	syncmessage = queue.Queue()
	syncqueue = queue.Queue()
	syncplayer = player.ready_player(glob.glob(moviefile + "*.mp4")[0], syncqueue)
	print(clients)
	for client in clients:
		waitforitqueue.put(True)
	for client in clients:
		tellClientsToSyncThread = TellClientsToSyncThread(client[0], clients[client], moviefile, waitforitqueue)
		tellClientsToSyncThread.start()
	waitforitqueue.join()
	print('everyone on board')
	syncScreamerThread = SyncScreamerThread("SCREAMFORME", UDPPort_sync, syncmessage)
	syncScreamerThread.start()
	while True:
		try:
			syncqueue.get(True, 5)
		except queue.Empty:
			syncmessage.put(syncplayer.position)
		else:
			break

def syncscreamer(udpport_sync, syncmessage):
	syncscreamer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	syncscreamer.sendto("go".encode('utf-8'), ("224.0.0.1", udpport_sync))
	while True:
		message = syncmessage.get()
		print(message)
		syncscreamer.sendto(str(message).encode('utf-8'), ("224.0.0.1", udpport_sync))
		if message == "end":
			break

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