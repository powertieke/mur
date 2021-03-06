#!/usr/bin/python3

import sys
import os
import argparse
import domxplayer
import socket
import pprint
import queue
import time
import subprocess

import player
import client

import controller
import clientfinder
#import interface
import webinterface
import atexit


# Standard ports
tcpport = 50667
statport = 50668
udpport_discovery = 50666
udpport_sync = 50665

# Shared Queue's
slaves = queue.Queue()
incoming_from_controller = queue.Queue()
outgoing_to_controller = queue.Queue()
killqueue = queue.Queue()

syncloops = {"clients": ["pi1", "pi2", "pi3", "pi4", "pi5", "pi6", "pi7", "pi8", "pitlb", "pitlr", "pitlf"], "moviefile" : "Paris", "repeats": 10, "intervalmoviefile" : "Paris"}



def cleanup():
	subprocess.call('sudo sh -c "TERM=linux setterm -cursor on >/dev/tty0"', shell=True)
	if os.path.exists("/home/pi/mur/webpage/locked") :
		os.remove("/home/pi/mur/webpage/locked")
	if os.path.exists("/home/pi/mur/webpage/running") :
		os.remove("/home/pi/mur/webpage/running")
		
	
	player.kill_all_omxplayers()
	
















def main():
	atexit.register(cleanup)
	
	parser = argparse.ArgumentParser(description='Networked display controller with support for playing syncronized movies')
	parser.add_argument('-m', '--master', help='Run as master. This pi will run the controller website, and tell all of the slaves what to do', action='store_true')
	parser.add_argument('-s', '--slave', help='Run as slave. This pi will drive a display. Start/stop/skip/sync commands will be received from master.',action='store_true')
	parser.add_argument("clientname", help='Name of screen for Identification by controller.')
	parser.add_argument("moviepath", help='Specify directory path where movie files are stored.')
	
	args = parser.parse_args()
	# pprint.pprint(args)
	
	if args.master :
		cleanup() # Remove all of the crap left behind after the reboot
		foundclients = clientfinder.clientfinder(udpport_discovery, tcpport, statport) # Listens to discovery broadcasts from unconnected pi's in the same network and sets up a control connection over TCP.
		# interface.interface(foundclients, udpport_sync, args.moviepath)
		controller.startSyncLoop(syncloops, foundclients, udpport_sync, killqueue)
		webinterface.webinterface(foundclients, udpport_sync, args.moviepath, killqueue)
		
		
	if args.slave :
		player.set_background('black')
		bgImage = subprocess.Popen(["/usr/bin/python", "imageblitter.py", args.moviepath, args.clientname], stdin=subprocess.PIPE)
		time.sleep(5)
		loopSingleMoviesThread = player.LoopSingleMoviesThread(args.moviepath, incoming_from_controller, outgoing_to_controller, udpport_sync, args.clientname)
		loopSingleMoviesThread.start()
		while True:
			clientsocket, statsocket = client.find_controller(args.clientname, udpport_discovery, tcpport, statport)
			statThread = player.StatThread("statsocket", statsocket)
			statThread.daemon = True
			statThread.start()
			player.controller(incoming_from_controller, outgoing_to_controller, clientsocket, udpport_sync, udpport_discovery, tcpport, statport, args.clientname)
			# print("controller ended on error. Closing sockets and starting over.")
			clientsocket.close()
			statsocket.close()
		bgImage.communicate()
		
	
	

if __name__ == "__main__":
	main()