#!/usr/bin/python3

import dbus
import threading
import subprocess
import time
import uuid
import queue

class PlayerProcessThread(threading.Thread):
	def __init__(self, parent, name='playerThread'):
		threading.Thread.__init__(self, name=name)
		self.parent = parent
	def run(self):
		position_loop(self.parent)

def player_process(parent):
	subprocess.call("omxplayer %s --dbus_name %s" % (parent.moviefile, parent.dbusname), shell=True)
	if parent.stopped == false:
		parent.outQueue.put("localend")
	
class OMXPlayer(object):
	def __init__(self, moviefile, outQueue):
		self.paused = False
		self.moviefile = moviefile
		self.dbusname = self.generate_dbusname()
		self.dbusIfaceProp = None
		self.dbusIfaceKey = None
		self.outQueue = outQueue
		self.stopped = False
		self.overshoot = 32000 # very inscientifically defined delay when pause() is called
		self.go()
		
	def go(self):
		playerProcessThread = PlayerProcessThread(self)
		playerProcessThread.start()
		omxplayerdbus = open('/tmp/omxplayerdbus').read().strip()
		bus = dbus.bus.BusConnection(omxplayerdbus)
		# Trying to make a connection to the dbus. Fail until ready.
		while True:
			try:
				dbusobject = bus.get_object(self.dbusname, '/org/mpris/MediaPlayer2', introspect=False)
				break
			except:
				pass
		self.dbusIfaceProp = dbus.Interface(dbusobject, 'org.freedesktop.DBus.Properties')
		self.dbusIfaceKey = dbus.Interface(dbusobject, 'org.mpris.MediaPlayer2.Player')
		
		# position will hang on 0 for a moment. Check until value changes.
		startpos = self.get_position()
		while True:
			if startpos != self.get_position():
				break
		# Try to get as close to pts 0 as possible. Try to guess when we need to press pause.
		delay = (-self.get_position() - self.overshoot)/1000000
		time.sleep(delay)
		self.toggle_pause()
		
		
	def generate_dbusname(self):
		self.dbusname = "org.mpris.MediaPlayer2.omxplayer" + str(uuid.uuid4())
	
	def stop(self):
		self.stopped = True
		self.dbusIfaceKey.stop()
		
	def toggle_pause(self):
		self.dbusIfaceKey.pause()
		self.paused = not self.paused
		
	def get_position(self):
		return self.dbusIfaceProp.Position()
		
	def get_duration(self): 
		return self.dbusIfaceProp.Duration()
		
	def seek(self, microseconds):
		self.dbusIfaceKey.Seek(dbus.Int64(str(microseconds)))