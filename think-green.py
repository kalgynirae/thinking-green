import time

import pygame

class Entity(object):
    pass

class Collect(Entity):
    image = pygame.image.load('collect.png')

class Recycle(Entity):
    image = pygame.image.load('recycle.png')

class Hazard(Entity):
    image = pygame.image.load('hazard.png')

pygame.init()

green_planet = pygame.image.load('green_planet.png')
red_planet = pygame.image.load('red_planet.png')

screen_size = green_planet.get_size()
screen = pygame.display.set_mode(screen_size)
screen.blit(green_planet, (0, 0))

pygame.display.flip()
time.sleep(5)
