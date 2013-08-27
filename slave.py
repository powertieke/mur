#!/usr/bin/python3

import socket
import threading
import pickle

class Slave:
	def __init__(self, ip, port, name):
		self.ip = ip
		self.port = port
		self.name = name
		self.playlist = []
		self.syncedlist = []
		self.status = none
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((self.ip, self.port))
		self.update()
		
		
	
	def update(self):
		self.sock.sendall("status")
		self.status = self.sock.recv(1024)
		self.sock.sendall("playlist")
		self.playlist = pickle.loads(self.sock.recv(4096))
		self.sock.sendall("syncedlist")
		self.syncedlist = pickle.loads(self.sock.recv(4096))
		
	def play(self):
		self.sock.sendall("play")
		self.status = self.sock.recv(4096)
		
	def skip_forward(self):
		self.sock.sendall("skipforward")
		self.status = self.sock.recv(4096)
		
	def skip_backward(self):
		self.sock.sendall("skipbackward")
		self.status = self.sock.recv(4096)