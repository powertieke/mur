#!/usr/bin/python
import sys
import os
import pprint
import datetime

def writestatus(theObject):
	tempfile = "/tmp/status.now"
	of = open(tempfile, 'w')
	of.write(datetime.datetime.utcnow())
	pprint.pprint(theObject, of)
	of.close()

