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
outpipe = open("fromwebapp", "w")
outpipe.writelines(form["command"].value)
outpipe.close()
inpipe = open("towebapp", "r")
response = inpipe.read()
inpipe.close()
print(response)


os.remove("locked")
