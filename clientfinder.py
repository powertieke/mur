#!/usr/bin/python3

import socket
import threading
import queue
import time

def discovery_server(discovered, port):
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind(('', port))
	while True:
		data, sender_addr = s.recvfrom(1024)
		discovered.put([data.decode('UTF-8'), sender_addr])
		
def make_control_socket(socketdict, discovered, port):
	while True:
		client = discovered.get()
		clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		clientSocket.connect((client[1][0], port))
		clientSocket.sendall('status'.encode('UTF-8'))
		answer = clientSocket.recv(1024).decode('UTF-8')
		socketdict[client[0]] = [clientSocket, answer]
		discovered.task_done()

class ClientFinderThread(threading.Thread):
	def __init__(self, discovered, port, name):
		threading.Thread.__init__(self, name=name)
		self.discovered = discovered
		self.port = port
	def run(self):
		discovery_server(self.discovered, self.port)
		
class MakeControlSocketThread(threading.Thread):
	def __init__(self, socketdict, discovered, port, name):
		threading.Thread.__init__(self, name=name)
		self.socketdict = socketdict
		self.discovered = discovered
		self.port = port
	def run(self):
		make_control_socket(self.socketdict, self.discovered, self.port)

def clientfinder(udpport, tcpport):
	discovered = queue.Queue()
	socketdict = {}
	clientFinderThread = ClientFinderThread(discovered, udpport, "Clientfinder")
	clientFinderThread.start()
	makeControlSocketThread = MakeControlSocketThread(socketdict, discovered, tcpport, "socketmaker")
	makeControlSocketThread.start()
	discovered.join()
	return socketdict

def test():
	discovered = queue.Queue()
	socketdict = {}
	udpport = 6666
	tcpport = 6667
	clientFinderThread = ClientFinderThread(discovered, udpport, "Clientfinder")
	clientFinderThread.start()
	makeControlSocketThread = MakeControlSocketThread(socketdict, discovered, tcpport, "socketmaker")
	makeControlSocketThread.start()
	time.sleep(5)
	while True:
		if len(socketdict) > 0 :
			for name in socketdict:
				print(name + " : ")
				socketdict[name][0].sendall("status".encode('UTF-8'))
				print(socketdict[name][0].recv(1024).decode('UTF-8') + "\n")
		time.sleep(5)
	
if __name__ == "__main__":
	test()