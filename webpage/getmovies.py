#!/usr/bin/python3
import cgi
import sys
import os
import glob
import json


syncmovies = glob.glob("/home/pi/movies/sync/*.mp4")
syncmovies = list(set([os.path.basename(x)[:-4].split("pi")[0] for x in syncmovies]))



singlemovies = glob.glob("/home/pi/movies/single/*.mp4")
singlemovies = list(set([os.path.basename(x)[:-4].split("pi")[0] for x in singlemovies]))

output = json.dumps([syncmovies, singlemovies])

print(output)