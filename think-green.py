import logging
import time

import pygame

logging.basicConfig(level=logging.DEBUG)

# Initialize pygame
logging.info("Initializing pygame")
pygame.init()
# Set up key repeat (delay, interval)
pygame.key.set_repeat(400, 50)

def pixels(coordinates):
    if isinstance(coordinates, tuple):
        return tuple(x * 13 for x in coordinates)
    else:
        return coordinates * 13

# Define objects and load images
logging.info("Loading images")
class Entity(object):
    pass

class Collect(Entity):
    image = pygame.image.load('collect.png')

class Recycle(Entity):
    image = pygame.image.load('recycle.png')

class Hazard(Entity):
    image = pygame.image.load('hazard.png')

class Exit(Exception):
    pass

# Load the two backdrops
green_planet = pygame.image.load('green_planet.png')
red_planet = pygame.image.load('red_planet.png')
screen_size = (748, 600)
grid_offset = (231, 218)

# Paint the backdrop
screen = pygame.display.set_mode(screen_size)
screen.blit(green_planet, (0, 0))

pygame.display.flip()

try:
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logging.debug("[event]pygame.QUIT")
                raise Exit
            if event.type == pygame.KEYDOWN:
                logging.debug("[event]pygame.KEYDOWN "
                              "event.key={}".format(event.key))
except Exit:
    logging.info("Exiting")
    pass
