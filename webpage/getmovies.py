#!/usr/bin/python3
import cgi
import sys
import os
import glob
import json


syncmovies = glob.glob("/media/usb/sync/*.mp4")
syncmovies = list(set([os.path.basename(x)[:-4].split("pi")[0] for x in syncmovies]))



singlemovies = glob.glob("/media/usb/single/*.mp4")
singlemovies = list(set([os.path.basename(x)[:-4].split("pi")[0] for x in singlemovies]))

output = json.dumps([syncmovies, singlemovies])

print(output)