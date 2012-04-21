import logging
import random
import time

import pygame

SCREEN_SIZE = (748, 600)
GRID_OFFSET = (231, 220)
GRID_WIDTH = 22
GRID_HEIGHT = 22
GRID_SQUARE_SIZE = 13

logging.basicConfig(level=logging.DEBUG)

# Initialize pygame
logging.info("Initializing pygame")
pygame.init()
# Set up key repeat (delay, interval)
pygame.key.set_repeat(400, 50)

# Define objects and load images
logging.info("Loading images and objects")

class Entity(object):
    pass

class Grid(object):

    # Load the two backdrops
    green_planet = pygame.image.load('green_planet.png')
    red_planet = pygame.image.load('red_planet.png')

    @property
    def background(self):
        if self.count_entities(Hazard) < 10:
            return self.green_planet
        else:
            return self.red_planet

    def __init__(self, offset, width, height, square_size):
        self.grid_offset = offset
        self.width = width
        self.height = height
        self.square_size = square_size
        self.entities = {}
        self.tick_count = 0

    def add_entity(self, entity, coordinates):
        w, h = coordinates
        if not 0 <= w < self.width or not 0 <= h < self.height:
            raise IndexError("Coordinates out of bounds")
        if (w, h) in self.entities:
            raise SquareFilledError
        else:
            self.entities[(w, h)] = entity

    def count_entities(self, type=Entity):
        return sum(1 for entity in self.entities.itervalues()
                   if isinstance(entity, type))

    def draw(self, screen):
        screen.blit(self.background, (0, 0))
        for coordinates, entity in self.entities.iteritems():
            screen.blit(entity.image, self.grid_pixels(coordinates))

    def grid_pixels(self, coordinates):
        return (coordinates[0] * self.square_size + self.grid_offset[0],
                coordinates[1] * self.square_size + self.grid_offset[1])

    def is_complete(self):
        return self.count_entities(Recycle) == 0

    def pop_entity(self, entity):
        for coordinates, e in self.entities.iteritems():
            if e is entity:
                del self.entities[coordinates]
                return coordinates

    def random_coordinates(self):
        return (random.choice(range(self.width)),
                random.choice(range(self.height)))

    def setup(self):
        # Spawn 10 Recycles in random locations
        for i in range(10):
            success = False
            while not success:
                try:
                    self.add_entity(Recycle(), self.random_coordinates())
                    success = True
                except SquareFilledError:
                    pass

    def tick(self):
        self.tick_count += 1
        logging.debug("Grid.tick_count={}".format(self.tick_count))
        if self.tick_count % 10 == 0:
            # Spawn new hazards
            logging.debug("Spawning new hazards")
            success = False
            for i in range(2):
                while not success:
                    try:
                        self.add_entity(Hazard(), self.random_coordinates())
                        success = True
                    except SquareFilledError:
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

    def move(self, grid, coordinates_delta, direction=None):
        coordinates = grid.pop_entity(self)
        new_coordinates = tuple(sum(x) for x in zip(coordinates,
                                                    coordinates_delta))
        try:
            grid.add_entity(self, new_coordinates)
        except IndexError:
            grid.add_entity(self, coordinates)
        self.direction = direction

class Recycle(Entity):
    image = pygame.image.load('recycle.png')

class Hazard(Entity):
    image = pygame.image.load('hazard.png')

class Exit(Exception):
    pass

class SquareFilledError(Exception):
    pass

screen = pygame.display.set_mode(SCREEN_SIZE)
clock = pygame.time.Clock()
try:
    while True:
        # Generate levels
        logging.info("Generating new level")
        grid = Grid(GRID_OFFSET, GRID_WIDTH, GRID_HEIGHT, GRID_SQUARE_SIZE)
        collect = Collect()
        grid.add_entity(collect, grid.random_coordinates())
        grid.setup()
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
                        grid.tick()
                        collect.move(grid, (-1, 0), 'left')
                    elif event.key in (pygame.K_DOWN, pygame.K_j):
                        grid.tick()
                        collect.move(grid, (0, 1), 'down')
                    elif event.key in (pygame.K_UP, pygame.K_k):
                        grid.tick()
                        collect.move(grid, (0, -1), 'up')
                    elif event.key in (pygame.K_RIGHT, pygame.K_l):
                        grid.tick()
                        collect.move(grid, (1, 0), 'right')
            if grid.is_complete():
                break

except Exit:
    logging.info("Exiting")
    pygame.display.quit()
    pygame.quit()
