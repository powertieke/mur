#!/usr/bin/python3

import socket
import threading
import queue
import time

def check_clients(socketdict):
	while True:
		time.sleep(1)
		removefromdict = []
		for pi in list(socketdict.keys()):
			clientSocket = socketdict[pi][3]
			#try:
			clientSocket.sendall('status'.encode('UTF-8'))
			#except:
			#	removefromdict.append(pi)
			else:
				#try:
					socketdict[pi][1] = clientSocket.recv(1024).decode('UTF-8')
				#except:
				#	removefromdict.append(pi)
		for pi in removefromdict:
			try:
				print("bad response from check. Close sockets on %s and remove from list" % pi)
				socketdict[pi][0].close()
				socketdict[pi][3].close()
			except:
				pass
			del socketdict[pi]
		

def discovery_server(discovered, port):
	"""Listens for screaming clients, and dumps their info into the Discovered queue for processing by the make_control_socket function."""
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind(('', port))
	while True:
		data, sender_addr = s.recvfrom(1024)
		print("found %s" % data.decode('UTF-8'))
		discovered.put([data.decode('UTF-8'), sender_addr])
		
def make_control_socket(socketdict, discovered, port, statport):
	"""Gets info from the discovered queue and sets up a control connection. Shoves these into the socketdict variable (Which is a global)"""
	while True:
		client = discovered.get()
		clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			clientSocket.connect((client[1][0], port))
		except socket.error:
			print("%s refused connection on tcpport. Letting go for now" % client[0])
			continue
		clientSocket.sendall('status'.encode('UTF-8'))
		answer = clientSocket.recv(1024).decode('UTF-8')
		statSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			statSocket.connect((client[1][0], statport))
		except socket.error:
			print("%s refused connection in statport. Letting go for now" % client[0])
			continue
		statSocket.sendall('status'.encode('UTF-8'))
		answer = statSocket.recv(1024).decode('UTF-8')
		socketdict[client[0]] = [clientSocket, answer, client[1][0], statSocket]
		# print(socketdict)

class CheckClientsThread(threading.Thread):
	"""thread polling clients"""
	def __init__(self, socketdict, name):
		threading.Thread.__init__(self, name=name)
		self.socketdict = socketdict
	def run(self):
		check_clients(self.socketdict)

class ClientFinderThread(threading.Thread):
	"""Thread running the discovery server"""
	def __init__(self, discovered, port, name):
		threading.Thread.__init__(self, name=name)
		self.discovered = discovered
		self.port = port
	def run(self):
		discovery_server(self.discovered, self.port)
		
class MakeControlSocketThread(threading.Thread):
	"""Thread running the make_control_socket function"""
	def __init__(self, socketdict, discovered, port, statport, name):
		threading.Thread.__init__(self, name=name)
		self.socketdict = socketdict
		self.discovered = discovered
		self.port = port
		self.statport = statport
	def run(self):
		make_control_socket(self.socketdict, self.discovered, self.port, self.statport)

def clientfinder(udpport, tcpport, statport):
	"""Starts the neccesary threads for finding and connecting to the clients. Returns the shared Socketdict variable"""
	discovered = queue.Queue()
	socketdict = {}
	clientFinderThread = ClientFinderThread(discovered, udpport, "Clientfinder")
	clientFinderThread.daemon = True
	clientFinderThread.start()
	makeControlSocketThread = MakeControlSocketThread(socketdict, discovered, tcpport, statport, "socketmaker")
	makeControlSocketThread.daemon = True
	makeControlSocketThread.start()
	checkClientsThread = CheckClientsThread(socketdict, "checkclients")
	checkClientsThread.daemon = True
	checkClientsThread.start()
	return socketdict

def test():
	discovered = queue.Queue()
	socketdict = {}
	udpport = 6666
	tcpport = 6667
	clientFinderThread = ClientFinderThread(discovered, udpport, "Clientfinder")
	clientFinderThread.daemon = True
	clientFinderThread.start()
	makeControlSocketThread = MakeControlSocketThread(socketdict, discovered, tcpport, "socketmaker")
	makeControlSocketThread.start()
	time.sleep(5)
	while True:
		if len(socketdict) > 0 :
			for name in socketdict:
				# print(name + " : ")
				socketdict[name][0].sendall("status".encode('UTF-8'))
				# print(socketdict[name][0].recv(1024).decode('UTF-8') + "\n")
		time.sleep(5)
	
if __name__ == "__main__":
	test()