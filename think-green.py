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
logging.info("Loading images and objects")

class Grid(object):

    # Load the two backdrops
    green_planet = pygame.image.load('green_planet.png')
    red_planet = pygame.image.load('red_planet.png')

    @property
    def background(self):
        if self.count_entities() < 50:
            return self.green_planet
        else:
            return self.red_planet

    def __init__(self):
        self.screen_size = (748, 600)
        self.grid_offset = (231, 220)
        self.width = 22
        self.height = 22
        self.square_size = 13
        self.entities = {}
        self.draw_count = 0

    def add_entity(self, entity, coordinates):
        w, h = coordinates
        if not 0 <= w < self.width or not 0 <= h < self.height:
            raise IndexError("Coordinates out of bounds")
        self.entities.setdefault((w, h), []).append(entity)

    def count_entities(self):
        return sum(len(x) for x in self.entities.itervalues())

    def pop_entity(self, entity):
        for coordinates, entities in self.entities.iteritems():
            if entity in entities:
                self.entities[coordinates].remove(entity)
                if len(self.entities[coordinates]) == 0:
                    del self.entities[coordinates]
                return coordinates

    def draw(self, screen):
        self.draw_count = (self.draw_count + 1) % 240
        screen.blit(self.background, (0, 0))
        for coordinates, entities in self.entities.iteritems():
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
        elif self.direction == 'up':
            return pygame.transform.rotate(self.image_right, 90)
        elif self.direction == 'left':
            return pygame.transform.rotate(self.image_right, 180)
        elif self.direction == 'down':
            return pygame.transform.rotate(self.image_right, -90)

    def move(self, grid, coordinates_delta, direction):
        self.direction = direction
        coordinates = grid.pop_entity(self)
        new_coordinates = tuple(sum(x) for x in zip(coordinates,
                                                    coordinates_delta))
        try:
            grid.add_entity(self, new_coordinates)
        except IndexError:
            grid.add_entity(self, coordinates)

class Recycle(Entity):
    image = pygame.image.load('recycle.png')

class Hazard(Entity):
    image = pygame.image.load('hazard.png')

class Exit(Exception):
    pass


# Make a Grid and a Collect
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
                    collect.move(grid, (-1, 0), 'left')
                elif event.key in (pygame.K_DOWN, pygame.K_j):
                    collect.move(grid, (0, 1), 'down')
                elif event.key in (pygame.K_UP, pygame.K_k):
                    collect.move(grid, (0, -1), 'up')
                elif event.key in (pygame.K_RIGHT, pygame.K_l):
                    collect.move(grid, (1, 0), 'right')
except Exit:
    logging.info("Exiting")
    pygame.display.quit()
    pygame.quit()
