import logging
import time

import pygame

logging.basicConfig(level=logging.DEBUG)

# Initialize pygame
logging.info("Initializing pygame")
pygame.init()
# Set up key repeat (delay, interval)
pygame.key.set_repeat(400, 50)

# Define objects and load images
logging.info("Loading images")
class NoWrapList(list):
    """A list that doesn't allow negative indices"""

    def __getitem__(self, key):
        if not 0 <= key < len(self):
            raise IndexError
        else:
            return super(NoWrapList, self).__getitem__(key)

class Grid(object):

    # Load the two backdrops
    green_planet = pygame.image.load('green_planet.png')
    red_planet = pygame.image.load('red_planet.png')

    @property
    def background(self):
        return self.green_planet

    def __init__(self):
        self.screen_size = (748, 600)
        self.grid_offset = (231, 218)
        self.width = 22
        self.height = 22
        self.square_size = 13
        self.entities = [[list() for square in range(self.height)]
                         for column in range(self.width)]

    def add_entity(self, entity, coordinates):
        column, square = coordinates
        self.entities[column][square].append(entity)

    def draw(self, screen):
        screen.blit(self.background, (0, 0))
        for column, squares in enumerate(self.entities):
            for square, entities in enumerate(squares):
                coordinates = (column, square)
                for entity in entities:
                    screen.blit(entity.image, self.grid_pixels(coordinates))

    def grid_pixels(self, coordinates):
        return (coordinates[0] * self.square_size + self.grid_offset[0],
                coordinates[1] * self.square_size + self.grid_offset[1])

class Entity(object):
    pass

class Collect(Entity):
    image_right = pygame.image.load('collect.png')

    def __init__(self):
        self.direction = 'right'

    @property
    def image(self):
        if self.direction == 'right':
            return self.image_right
        if self.direction == 'down':
            return pygame.transform.rotate(self.image_right, 90)
        if self.direction == 'left':
            return pygame.transform.rotate(self.image_right, 180)
        if self.direction == 'up':
            return pygame.transform.rotate(self.image_right, -90)

    def move(self, left=None, down=None, up=None, right=None):
        

class Recycle(Entity):
    image = pygame.image.load('recycle.png')

class Hazard(Entity):
    image = pygame.image.load('hazard.png')

class Exit(Exception):
    pass


# Make a grid and a Collect
grid = Grid()
collect = Collect()
grid.add_entity(collect, (0, 0))

screen = pygame.display.set_mode(grid.screen_size)
clock = pygame.time.Clock()
try:
    while True:
        clock.tick(60)
        # Paint the backdrop
        grid.draw(screen)
        pygame.display.flip()
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logging.debug("[event]pygame.QUIT")
                raise Exit
            if event.type == pygame.KEYDOWN:
                logging.debug("[event]pygame.KEYDOWN "
                              "event.key={}".format(event.key))
                if event.key in (pygame.K_LEFT, pygame.K_h):
                    collect.move(left=1)
                elif event.key in (pygame.K_DOWN, pygame.K_j):
                    collect.move(down=1)
                elif event.key in (pygame.K_UP, pygame.K_k):
                    collect.move(up=1)
                elif event.key in (pygame.K_RIGHT, pygame.K_l):
                    collect.move(right=1)
except Exit:
    logging.info("Exiting")
    pass
