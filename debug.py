#!/usr/bin/python
import sys
import os
import pprint
import datetime

def writestatus(theObject):
	tempfile = "/tmp/status.now"
	of = open(tempfile, 'w')
	of.write(str(datetime.datetime.utcnow()))
	pprint.pprint(theObject.__dict__, of)
	of.close()

