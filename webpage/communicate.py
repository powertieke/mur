#!/usr/bin/python3

#!/usr/bin/python3
import cgi
import cgitb

cgitb.enable()

import sys
import os
import time
import json

form = cgi.FieldStorage()

if os.path.exists("/tmp/running") :
	while os.path.exists("/tmp/locked") :
		time.sleep(0.3)
		
	open("/tmp/locked", "a")
	outpipe = open("/tmp/fromwebapp", "w")
	outpipe.writelines(form["command"].value)
	outpipe.close()
	inpipe = open("/tmp/towebapp", "r")
	response = inpipe.read()
	inpipe.close()
	print(response)
	os.remove("/tmp/locked")
else:
	print(json.dumps(False))