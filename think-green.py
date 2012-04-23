import logging
import random
import sys
import time

import pygame

SCREEN_SIZE = (748, 600)
GRID_OFFSET = (231, 215)
GRID_WIDTH = 22
GRID_HEIGHT = 22
GRID_SQUARE_SIZE = 13

try:
    level = logging.DEBUG if sys.argv[1] == 'debug' else logging.WARNING
except IndexError:
    level = logging.WARNING
logging.basicConfig(level=level)

# Initialize pygame
logging.info("Initializing pygame")
pygame.mixer.pre_init(44100)
pygame.init()
pygame.key.set_repeat(100, 50)

logging.info("Loading images and objects")

class Entity(object):

    def move(self, grid, coordinates_delta, direction=None):
        global combo
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
                    grid.score += 500 * (grid.combo)**2
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
                    grid.score += (grid.combo)**2 * 20
                    combo = True
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
    green_planet = pygame.image.load('images/green_planet.png')
    red_planet = pygame.image.load('images/red_planet.png')
    title_image = pygame.image.load('images/title.png')
    continue_image = pygame.image.load('images/continue.png')
    explain_image = pygame.image.load('images/explain.png')

    @property
    def background(self):
        return self.green_planet if not self.is_dead else self.red_planet

    @property
    def is_complete(self):
        return self.is_dead

    @property
    def message(self):
        if self.show_title:
            return self.title_image
        elif self.show_continue:
            return self.continue_image
        elif self.show_explain:
            return self.explain_image
        else:
            return None

    def __init__(self, offset, width, height, square_size):
        self.grid_offset = offset
        self.width = width
        self.height = height
        self.square_size = square_size
        self.entities = {}
        self.tick_count = 0
        self.is_dead = False
        self.collect = None
        self.show_title = False
        self.show_continue = False
        self.show_explain = False
        self.show_score = False
        self.score = 100
        self.combo = 1

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
        if self.message:
            screen.blit(self.message, (0, screen.get_height() - 75))
        if self.show_score:
            self.draw_score(screen)
        for coordinates, entity in self.entities.iteritems():
            screen.blit(entity.image, self.grid_pixels(coordinates))

    def draw_score(self, screen):
        f = pygame.font.SysFont('DejaVu Sans', 14, True)
        s = f.render(str(self.score), True, (0x2e, 0x34, 0x36))
        screen.blit(s, (screen.get_width() - s.get_width() - 25,
                        screen.get_height() - 60))

    def get_coordinates(self, entity):
        for coordinates, e in self.entities.iteritems():
            if e is entity:
                return coordinates

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
        return (random.choice(range(1, self.width - 1)),
                random.choice(range(1, self.height - 1)))

    def remove_entity(self, coordinates):
        del self.entities[coordinates]

    def setup(self):
        self.collect = Collect()
        grid.add_entity(self.collect, (grid.width // 2, grid.height // 2))
        self.spawn_entity(Recycle, 25)
        self.spawn_entity(Receptor, 7)
        self.spawn_entity(Hazard, 5)
        self.show_explain = True
        self.show_score = True

    def spawn_entity(self, type, number=1):
        logging.debug("Spawning {} {}".format(number, type))
        for i in range(number):
            success = False
            while not success:
                coordinates = self.random_coordinates()
                if coordinates not in self.collect.clear_coordinates(grid):
                    try:
                        self.add_entity(type(), coordinates)
                        success = True
                    except CollisionError:
                        pass

    def tick(self):
        self.score -= 1
        self.tick_count += 1
        logging.debug("Grid.tick_count={}".format(self.tick_count))
        tc = self.tick_count ** 0.5
        if (self.tick_count % ((tc + 200) // tc) == 0 or
                self.count_entities(Recycle) < 3):
            self.spawn_entity(Recycle)
        if (self.tick_count % ((tc + 700) // tc) == 120 or
                self.count_entities(Receptor) < 1):
            self.spawn_entity(Receptor)
        if (self.tick_count % ((tc + 700) // tc) == 0 or
                self.count_entities(Hazard) < 1):
            self.spawn_entity(Hazard)


class Collect(Entity):
    image_right = pygame.image.load('images/collect.png')

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

    def clear_coordinates(self, grid):
        w, h = grid.get_coordinates(self)
        return ([(w, n) for n in range(0, grid.height)] +
                [(n, h) for n in range(0, grid.width)])

class Death(Entity):
    image = pygame.image.load('images/death.png')

class Hazard(Entity):
    image = pygame.image.load('images/hazard.png')

class Neutralize(Entity):
    image = pygame.image.load('images/neutralize.png')

class Receptor(Entity):
    images = []
    images.append(pygame.image.load('images/receptor0.png'))
    images.append(pygame.image.load('images/receptor4.png'))
    images.append(pygame.image.load('images/receptor3.png'))
    images.append(pygame.image.load('images/receptor2.png'))
    images.append(pygame.image.load('images/receptor1.png'))

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
    image = pygame.image.load('images/recycle.png')

class CollisionError(Exception):
    pass

class DeathError(Exception):
    pass

class Exit(Exception):
    pass

class OutOfBoundsError(Exception):
    pass

def wait_for_continue(clock, grid, pause=0):
    count = 0
    while True:
        clock.tick(60)
        count += 1
        if count == pause:
            grid.show_title = False
            grid.show_continue = True
        grid.draw(screen)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logging.debug("[event]pygame.QUIT")
                raise Exit
            if event.type == pygame.KEYDOWN:
                logging.debug("[event]pygame.KEYDOWN "
                              "event.key={}".format(event.key))
                if (event.key in (pygame.K_RETURN, pygame.K_SPACE) and
                        count > pause):
                    return

def play_music(music_id):
    if music_id == 1:
        pygame.mixer.music.set_volume(0.7)
        pygame.mixer.music.load('music/tiny_world.ogg')
        pygame.mixer.music.play(-1)
    if music_id == 2:
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.load('music/recycling_is_fun.ogg')
        pygame.mixer.music.play(-1)
    if music_id == 3:
        pygame.mixer.music.set_volume(0.8)
        pygame.mixer.music.load('music/death_error.ogg')
        pygame.mixer.music.play(0)

combo = False

# Set up display
pygame.display.set_caption("Think Green")
pygame.display.set_icon(pygame.image.load('images/icon.gif'))
screen = pygame.display.set_mode(SCREEN_SIZE)
clock = pygame.time.Clock()
try:
    # Title screen
    play_music(1)
    grid = Grid(GRID_OFFSET, GRID_WIDTH, GRID_HEIGHT, GRID_SQUARE_SIZE)
    grid.show_title = True
    while True:
        wait_for_continue(clock, grid, pause=200)
        # Switch music
        pygame.mixer.music.fadeout(600)
        play_music(2)
        logging.info("Generating new level")
        grid = Grid(GRID_OFFSET, GRID_WIDTH, GRID_HEIGHT, GRID_SQUARE_SIZE)
        grid.setup()
        while True:
            clock.tick(60)
            # Process events
            combo = False # This is pretty hackish
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    logging.debug("[event]pygame.QUIT")
                    raise Exit
                if event.type == pygame.KEYDOWN:
                    logging.debug("[event]pygame.KEYDOWN "
                                  "event.key={}".format(event.key))
                    coordinates = None
                    if event.key in (pygame.K_LEFT, pygame.K_h):
                        coordinates, direction = (-1, 0), 'left'
                    elif event.key in (pygame.K_DOWN, pygame.K_j):
                        coordinates, direction = (0, 1), 'down'
                    elif event.key in (pygame.K_UP, pygame.K_k):
                        coordinates, direction = (0, -1), 'up'
                    elif event.key in (pygame.K_RIGHT, pygame.K_l):
                        coordinates, direction = (1, 0), 'right'
                    if coordinates:
                        try:
                            grid.collect.move(grid, coordinates, direction)
                        except OutOfBoundsError:
                            pass
                        except DeathError:
                            grid.is_dead = True
                            play_music(3)
                        else:
                            if combo:
                                grid.combo += 1
                            else:
                                grid.combo = 1
                            grid.tick()
            # Draw updates
            grid.draw(screen)
            pygame.display.flip()
            # Break if done
            if grid.is_complete:
                grid.show_explain = False
                grid.draw(screen)
                pygame.display.flip()
                break

except Exit:
    logging.info("Exiting")
    pygame.display.quit()
    pygame.quit()
