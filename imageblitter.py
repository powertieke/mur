#!/usr/bin/python

import pygame
import argparse
import glob

def main():
	parser = argparse.ArgumentParser(description='utillity for overlaying an image')
	parser.add_argument('-f', '--fifo', help='Define which fifo is used for communication')
	parser.add_argument("imagefolder", help='Location of image')
	
	args = parser.parse_args()
	
	pygame.init()
	w = 0
	h = 0
	size = (w, h)
	screen = pygame.display.set_mode(size)
	
	image = pygame.image.load(glob.glob(args.imagefolder + "*.png")[0])
	screen.blit(image, (0,0))
	pygame.display.flip()
	
	
	
	
if __name__ == "__main__":
	main()