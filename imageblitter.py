#!/usr/bin/python

import pygame
import argparse
import glob
import time

def main():
	parser = argparse.ArgumentParser(description='utillity for overlaying an image')
	parser.add_argument('-f', '--fifo', help='Define which fifo is used for communication')
	parser.add_argument("imagefolder", help='Location of image')
	parser.add_argument("hostname", help="Hostname of pi")	
	args = parser.parse_args()
	
	pygame.init()
	pygame.mouse.set_visible(False)
	print pygame.display.list_modes()
	w = 0
	h = 0
	size = (w, h)
	screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
	theImage = glob.glob(args.imagefolder + "*" + args.hostname + ".png")
	try:
		if theImage != []:
			theImage = theImage[0]
		else:
			theImage = glob.glob(args.imagefolder + "*.png")[0]
		
		image = pygame.image.load(theImage).convert()
		screen.blit(image, (0,0))
		pygame.display.flip()
	except:
		pass
	
	raw_input()
	
	
if __name__ == "__main__":
	main()