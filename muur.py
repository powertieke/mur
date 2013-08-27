#!/usr/bin/python3

import sys
import os
import argparse
import pyomxplayer
import socket
import pprint
import queue

import player
import client

import controller
import clientfinder
import interface



# Standard ports
tcpport = 50667
udpport_discovery = 50666
udpport_sync = 50665

# Shared Queue's
slaves = queue.Queue()























def main():
	parser = argparse.ArgumentParser(description='Networked display controller with support for playing syncronized movies')
	parser.add_argument('-m', '--master', help='Run as master. This pi will run the controller website, and tell all of the slaves what to do', action='store_true')
	parser.add_argument('-s', '--slave', help='Run as slave. This pi will drive a display. Start/stop/skip/sync commands will be received from master.',action='store_true')
	parser.add_argument("clientname", help='Name of screen for Identification by controller.')
	parser.add_argument("moviepath", help='Specify directory path where movie files are stored.')
	
	args = parser.parse_args()
	pprint.pprint(args)
	
	if args.master :
		foundclients = clientfinder.clientfinder(udpport_discovery, tcpport) # Listens to discovery broadcasts from unconnected pi's in the same network and sets up a control connection over TCP.
		interface.interface(udpport_sync, foundclients)
		
	if args.slave :
		player.loop_single_movies(args.moviepath)
		clientsocket = client.find_controller(args.clientname, udpport_discovery, tcpport)
		
		
	
	

if __name__ == "__main__":
	main()