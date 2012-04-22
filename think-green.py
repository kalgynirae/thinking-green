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

    def move(self, grid, coordinates_delta, direction=None):
        coordinates = grid.pop_entity(self)
        new_coordinates = tuple(sum(x) for x in zip(coordinates,
                                                    coordinates_delta))
        move, vanish = False, False
        # Check for entities ahead of us
        try:
            entity = grid.get_entity(new_coordinates)
        except IndexError:
            # new_coordinates is out of bounds; don't move
            move, vanish = False, False
            raise OutOfBoundsError
        except KeyError:
            # The square is empty; move there.
            move, vanish = True, False
        else:
            # There is an entity there, figure out what to do
            if isinstance(entity, Hazard):
                if isinstance(self, Neutralize):
                    # If we're a Neutralize and it's a Hazard, remove both
                    grid.remove_entity(new_coordinates)
                    move, vanish = True, True
                else:
                    # Everything explodes
                    grid.remove_entity(new_coordinates)
                    grid.add_entity(Death(), new_coordinates)
                    move, vanish = True, True
                    raise DeathError
            elif isinstance(entity, Receptor):
                if isinstance(self, Recycle):
                    entity.increment(grid)
                    move, vanish = True, True
                else:
                    move, vanish = False, False
                    raise OutOfBoundsError # This is a hack
            else:
                try:
                    entity.move(grid, coordinates_delta, direction)
                except OutOfBoundsError:
                    move, vanish = False, False
                    raise OutOfBoundsError
                except DeathError:
                    move, vanish = True, False
                    raise DeathError
                else:
                    move, vanish = True, False
        finally:
            if move:
                if not vanish:
                    grid.add_entity(self, new_coordinates)
            else:
                grid.add_entity(self, coordinates)
        self.direction = direction

class Grid(object):

    # Load the two backdrops
    green_planet = pygame.image.load('green_planet.png')
    red_planet = pygame.image.load('red_planet.png')

    @property
    def background(self):
        return self.green_planet if not self.is_dead else self.red_planet

    @property
    def is_complete(self):
        return self.is_dead or self.count_entities(Hazard) == 0

    def __init__(self, offset, width, height, square_size):
        self.grid_offset = offset
        self.width = width
        self.height = height
        self.square_size = square_size
        self.entities = {}
        self.tick_count = 0
        self.is_dead = False

    def add_entity(self, entity, coordinates):
        w, h = coordinates
        if not 0 <= w < self.width or not 0 <= h < self.height:
            raise IndexError("Coordinates out of bounds")
        if (w, h) in self.entities:
            raise CollisionError
        else:
            self.entities[(w, h)] = entity

    def count_entities(self, type=Entity):
        return sum(1 for entity in self.entities.itervalues()
                   if isinstance(entity, type))

    def draw(self, screen):
        screen.blit(self.background, (0, 0))
        for coordinates, entity in self.entities.iteritems():
            screen.blit(entity.image, self.grid_pixels(coordinates))

    def get_entity(self, coordinates):
        w, h = coordinates
        if not 0 <= w < self.width or not 0 <= h < self.height:
            raise IndexError("Coordinates out of bounds")
        return self.entities[coordinates]

    def grid_pixels(self, coordinates):
        return (coordinates[0] * self.square_size + self.grid_offset[0],
                coordinates[1] * self.square_size + self.grid_offset[1])

    def pop_entity(self, entity):
        for coordinates, e in self.entities.iteritems():
            if e is entity:
                del self.entities[coordinates]
                return coordinates

    def random_coordinates(self):
        return (random.choice(range(self.width)),
                random.choice(range(self.height)))

    def remove_entity(self, coordinates):
        del self.entities[coordinates]

    def setup(self):
        self.spawn_entity(Recycle, 20)
        self.spawn_entity(Receptor, 5)
        self.spawn_entity(Hazard, 3)
        # Spawn 10 Recycles in random locations
        # Same for a few hazards

    def spawn_entity(self, type, number=1):
        for i in range(number):
            success = False
            while not success:
                try:
                    self.add_entity(type(), self.random_coordinates())
                    success = True
                except CollisionError:
                    pass

    def tick(self):
        self.tick_count += 1
        logging.debug("Grid.tick_count={}".format(self.tick_count))
        if self.tick_count % 30 == 0:
            self.tick_count = 0
            # Spawn new hazard
            logging.debug("Spawning new hazard")
            self.spawn_entity(Hazard)

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

class Death(Entity):
    image = pygame.image.load('death.png')

class Hazard(Entity):
    image = pygame.image.load('hazard.png')

class Neutralize(Entity):
    image = pygame.image.load('neutralize.png')

class Receptor(Entity):
    images = []
    images.append(pygame.image.load('receptor0.png'))
    images.append(pygame.image.load('receptor1.png'))
    images.append(pygame.image.load('receptor2.png'))
    images.append(pygame.image.load('receptor3.png'))
    images.append(pygame.image.load('receptor4.png'))

    @property
    def image(self):
        return self.images[self.fuel]

    def __init__(self):
        self.fuel = 0

    def increment(self, grid):
        self.fuel += 1
        if self.fuel == 5:
            coordinates = grid.pop_entity(self)
            grid.add_entity(Neutralize(), coordinates)

class Recycle(Entity):
    image = pygame.image.load('recycle.png')

class CollisionError(Exception):
    pass

class DeathError(Exception):
    pass

class Exit(Exception):
    pass

class OutOfBoundsError(Exception):
    pass

screen = pygame.display.set_mode(SCREEN_SIZE)
clock = pygame.time.Clock()
try:
    while True:
        # Generate levels
        logging.info("Generating new level")
        grid = Grid(GRID_OFFSET, GRID_WIDTH, GRID_HEIGHT, GRID_SQUARE_SIZE)
        collect = Collect()
        grid.add_entity(collect, (grid.width // 2, grid.height // 2))
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
                        coordinates, direction = (-1, 0), 'left'
                    elif event.key in (pygame.K_DOWN, pygame.K_j):
                        coordinates, direction = (0, 1), 'down'
                    elif event.key in (pygame.K_UP, pygame.K_k):
                        coordinates, direction = (0, -1), 'up'
                    elif event.key in (pygame.K_RIGHT, pygame.K_l):
                        coordinates, direction = (1, 0), 'right'
                    try:
                        collect.move(grid, coordinates, direction)
                    except OutOfBoundsError:
                        pass
                    except DeathError:
                        grid.is_dead = True
                    else:
                        grid.tick()
            if grid.is_complete:
                break
        # wait for any keypress
        grid.draw(screen)
        pygame.display.flip()
        time.sleep(3)

except Exit:
    logging.info("Exiting")
    pygame.display.quit()
    pygame.quit()
