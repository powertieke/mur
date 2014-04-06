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

while os.path.exists("locked") :
	time.sleep(0.3)

open("locked", "a")
outpipe = open("outpipe", "w")
outpipe.writelines(form["command"].value)
outpipe.close()
inpipe = open("inpipe", "r")
response = inpipe.read()
inpipe.close()
statusdict = json.loads(response)


os.remove("locked")
