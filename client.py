#!/usr/bin/python3

import sys
import os
import socket
import time
import threading
import queue

"""This is where the client networking and controller discovery functions live"""



def listener(port, outqueue):
	"""Listens for incoming TCP connection requests and returns the connection"""
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind(("", port))
	s.listen(1)
	conn, addr = s.accept()
	conn.recv(1024)
	conn.sendall('0'.encode('utf-8'))
	outqueue.put(conn)
	
def screamer(clientname, udpport_discovery):
	"""Screams it's name through UDP out over the local network in search of a controller pi"""
	time.sleep(5) # give the main thread a couple of seconds to ready the connection before it starts yelling it's name - Fix better later (using a thread and a queue)
	while 1:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		try:
			s.sendto(clientname.encode('utf-8'), ("224.0.0.1", udpport_discovery))
		except socket.error:
			pass
		# print('%s: AARGGGH' % clientname)
		time.sleep(2)
		if exitflag == 1:
			break
	
class ListenerThread(threading.Thread):
	def __init__(self, port, outqueue, name):
		threading.Thread.__init__(self, name=name)
		self.clientname = clientname
		self.port = port
		self.outqueue = outqueue
	def run(self):
		listener(self.port, self.outqueue)
	
		
class ScreamerThread(threading.Thread):
	"""The tread running the screaming process. Else we could not do anything while the pi is looking for a server."""
	def __init__(self, clientname, udpport, name):
		threading.Thread.__init__(self, name=name)
		self.clientname = clientname
		self.udpport = udpport
		self.name = name
	def run(self):
		screamer(self.clientname, self.udpport)

def find_controller(clientname, udpport, tcpport, statport):
	"""Opens a listening TCP socket, and starts yelling around for the controller. Returns a connection with the controller (when found)."""
	global exitflag
	exitflag = 0
	cqueue = queue.Queue()
	squeue = queue.Queue()
	clistener = ListenerThread(tcpport, cqueue, "controlportthread")
	clistener.start()
	slistener = ListenerThread(statport, squeue,"controlportthread")
	slistener.start()
	screamerThread = ScreamerThread(clientname, udpport, "screamer1")
	screamerThread.start()
	controlSocket = cqueue.get()
	statsocket = squeue.get()
	exitflag = 1
	return controlSocket, statsocket

def test():
	s = find_controller("testpi1", 6666, 6667)
	
	while True:
		s.recv(1024)
		# print("Got some!")
		s.sendall("ok".encode('UTF-8'))

if __name__ == "__main__":
	test()