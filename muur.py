#!/usr/bin/python3

import sys
import os
import argparse
import pyomxplayer
import socket
import pprint
import queue
import time

import player
import client

import controller
import clientfinder
#import interface
import webinterface
import atexit


# Standard ports
tcpport = 50667
udpport_discovery = 50666
udpport_sync = 50665

# Shared Queue's
slaves = queue.Queue()
incoming_from_controller = queue.Queue()
outgoing_to_controller = queue.Queue()
killqueue = queue.Queue()

syncloops = {"clients": ["pitm", "pi1"], "moviefile" : "Screen", "repeats": 10, "intervalmoviefile" : "run"}
foundclients = {}




















def main():
	atexit.register(player.set_background, 'black')
	atexit.register(player.kill_all_omxplayers)
	
	parser = argparse.ArgumentParser(description='Networked display controller with support for playing syncronized movies')
	parser.add_argument('-m', '--master', help='Run as master. This pi will run the controller website, and tell all of the slaves what to do', action='store_true')
	parser.add_argument('-s', '--slave', help='Run as slave. This pi will drive a display. Start/stop/skip/sync commands will be received from master.',action='store_true')
	parser.add_argument("clientname", help='Name of screen for Identification by controller.')
	parser.add_argument("moviepath", help='Specify directory path where movie files are stored.')
	
	args = parser.parse_args()
	# pprint.pprint(args)
	
	if args.master :
		foundclients = clientfinder.clientfinder(udpport_discovery, tcpport) # Listens to discovery broadcasts from unconnected pi's in the same network and sets up a control connection over TCP.
		# interface.interface(foundclients, udpport_sync, args.moviepath)
		webinterface.webinterface(foundclients, udpport_sync, args.moviepath, killqueue)
		controller.startSyncLoop(syncloops)
		
	if args.slave :
		player.set_background('white')
		loopSingleMoviesThread = player.LoopSingleMoviesThread(args.moviepath, incoming_from_controller, outgoing_to_controller, udpport_sync, args.clientname)
		loopSingleMoviesThread.start()
		clientsocket = client.find_controller(args.clientname, udpport_discovery, tcpport)
		player.controller(incoming_from_controller, outgoing_to_controller, clientsocket, udpport_sync)
		
		
	
	

if __name__ == "__main__":
	main()