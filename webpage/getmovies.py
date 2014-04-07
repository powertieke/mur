#!/usr/bin/python3
import cgi
import sys
import os
import glob
import json


syncmovies = glob.glob("/media/usb/sync/*.mp4")
syncmovies = list(set([os.path.basename(x).split("pi")[0] for x in syncmovies]))
outputsync = json.dumps(syncmovies)


singlemovies = glob.glob("/media/usb/single/*.mp4")
singlemovies = list(set([os.path.basename(x).split("pi")[0] for x in singlemovies]))
outputsingle = json.dumps(singlemovies)

print("<script>")
print("var syncmovies = %s;" % [outputsync])
print("var singlemovies = %s;" % [outputsingle])
print("</script>")


print("<pre>")
print("var syncmovies = %s;" % [outputsync])
print("var singlemovies = %s;" % [outputsingle])
print("</pre>")

