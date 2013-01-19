#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import os.path
import re
import glob
import logging
import random

import pygame
from pygame.locals import *

# Some pseudo-constants
SCREEN_TOP = 16
SCREEN_BOTTOM = 695
SCREEN_LEFT = 16
SCREEN_RIGHT = 784

SHIP_Y = SCREEN_BOTTOM - 64
SPEEDBAR_X = 170
SPEEDBAR_Y = SCREEN_BOTTOM + 16 + 6

#from time import clock

class GraphicStore(object):
    """
    Loads and stores all the graphics used in the game. The graphics are stored
    in a dictionary keyed on the name (without extension) of the graphic.
    """
    
    def load(self, path):
        """
        Loads all the graphics from the specified path.
        """
        self.items = {}
        files = glob.glob(os.path.join(path, "*.png"))
        for imagefile in files:
            image = pygame.image.load(imagefile).convert_alpha()
            key, ext = os.path.splitext(os.path.basename(imagefile))
            self.items[key] = image
  
    def __getitem__(self, key):
        return self.items[key]

class SoundStore(object):
    """
    Loads and stores all the sounds used in the game. The sounds are stored in
    a dictionary keyed on the name (without extension) of the graphic.
    """
    
    def load(self, path):
        """
        Loads all the sounds from the specified path.
        """
        self.items = {}
        files = glob.glob(os.path.join(path, "*.ogg"))
        for soundfile in files:
            sound = pygame.mixer.Sound(soundfile)
            key, ext = os.path.splitext(os.path.basename(soundfile))
            self.items[key] = sound
            
    def __getitem__(self, key):
        return self.items[key]

# ==============================================================================
# g_store: GLOBAL VARIABLE!!!!
# ==============================================================================
# The GraphicsStore() class is used by many of the sprite classes. Rather than
# have them each create their own (which would defeat the purpose of the class,
# which is to prevent creating multiple instances of shared graphics), or having
# an instance created in the main Game class and then passed to each sprite
# class as a parameter (which seems clumsy), this global instance is available
# to all the classes. Each class knows which graphics it needs.
#
# This variable is actually initialised in the Game() class, as pygame.display
# has to be initialised before the class can be created.
g_store = GraphicStore()

# ==============================================================================
# s_store: GLOBAL VARIABLE!!!!
# ==============================================================================
# This is similar to the GraphicStore() class above, and allows all the other
# classes to have access to the sound files.
s_store = SoundStore()

class Label(object):
    """
    Simple class to render a label on-screen. Create an instance and call
    the draw() method.
    """
    
    def __init__(self, text, x, y):
        self.set_font(os.path.join("graphics", "04B_03.ttf"), 16)
        self.margin = 0
        self.text = text
        self.colour = pygame.color.Color('#cfa100')
        self.x = x
        self.y = y
        
    def draw(self, surface):
        """
        Renders the visual appearance.
        """
        width = surface.get_width()
        height = surface.get_height()
        
        if self.text != "":
            # Render the caption
            caption_surface = self.font.render(self.text, True, self.colour)
            surface.blit(caption_surface, (self.x, self.y))

    def set_font(self, name, size):
        self.fontname = name
        self.fontsize = size
        if self.fontname == "":
            self.font = pygame.font.Font(None, self.fontsize)
        else:
            self.font = pygame.font.Font(self.fontname, self.fontsize)

class ParallaxScroller(object):
    """
    Implements a vertically scrolling area of the screen, wrapping around at the 
    top and bottom edges. For this game this is used for the star-fields in the
    background.
    """
    def __init__(self, image, x, y, speed):
        self.image = image
        self.h = self.image.get_height()
        self.x = x
        self.y = y
        self.speed = speed
        
    def update(self):
        self.y = self.y + self.speed
        if abs(self.y) >= self.h:
            self.y = 0
        
    def render(self, target):
        target.blit(self.image, [int(self.x), int(self.y)])
        target.blit(self.image, [int(self.x), int(self.y) - self.h])

class Animation(object):
    """
    Implements an animated image, for use by sprites, which can retrieve the
    current animation frame from the 'image' variable, calling the 'update()'
    method each game tick to update to the next frame (the Animation class
    will handle the speed, and will only update when required). 
    
    An 'on_cycle' callback can be supplied, which will be called when the
    animation reaches the end of the cycle and has looped back to the start. The
    callback will be passed the Animation image. This can be used, for example,
    to remove an animation which should only be played once.
    """
    sprite_image = None
    frames = None
    on_cycle = None
    rect = None
    
    def __init__(self, image, speed, on_cycle = None):
        """
        Initialises the animation, loading the base image and extracting the
        frames. The images are expected to be in 'film-strip' style, and the
        width of each frame should be the same as the height of the image:
        
            +----+----+----+----+--
            | 01 | 02 | 03 | 04 | ... etc.
            +----+----+----+----+--
    
        Params:
            image : sprite image
            speed : frames per second (max. of 1000)
            on_cycle: optional callback to be invoked at the end of a cycle
        """
        self.sprite_image = image
        
        # All the sprite frames in this game are square and laid out
        # horizontally in the image, so the size of each frame can be read
        # from the height of the image.
        self.frame_height = self.sprite_image.get_height()
        self.frame_width = self.frame_height
        
        # Calculate the number of frames.
        self.frame_count = self.sprite_image.get_width() / self.frame_width
        
        # Extract the frames into a list of sub-surfaces, as this is more
        # efficient than creating an image for each frame.
        self.frames = []
        for frame in range(0, self.frame_count):
            offset = frame * self.frame_width
            frame = self.sprite_image.subsurface(Rect(offset, 0, self.frame_width, self.frame_width))
            self.frames.append(frame)
            
        # Prepare the first frame.
        self.frame = 0
        self.image = self.frames[self.frame]
        self.rect = self.image.get_rect()
        
        # Set the other parameters.
        self.speed = int(1000.0 / speed)
        self.frame_time = 0
        
        # Set up the callback.
        self.on_cycle = on_cycle
        
    def update(self, current_time):
        """
        This should be called every game-tick to allow the sprite to be updated
        """
        if self.frame_time < current_time:
            # Get the current frame image
            self.image = self.frames[self.frame]
            # Advance to the next frame, looping back to frame 0 at the end
            self.frame = self.frame + 1
            if self.frame > self.frame_count - 1:
                self.frame = 0
                if self.on_cycle:
                    self.on_cycle(self)
            # Advance the timer to wait for the next update time                    
            self.frame_time = current_time + self.speed
    
class FrameSprite(pygame.sprite.Sprite):
    """
    Implements an animated sprite which has multiple frames, using the 
    Animation() class.
    """
    spriteImage = None
    frames = None
    animation = None
    on_remove = None
    
    def __init__(self, image, speed):
        """
        Initialises the sprite, setting up an Animation instance to handle the
        actual animation. See the Animation class for the meaning of the
        parameters (these are passed directly on to the Animation class).
        """
        pygame.sprite.Sprite.__init__(self)

        # Set up the animation handler
        self.animation = Animation(image, speed, self.on_cycle)
        self.rect = self.animation.rect
        self.image = self.animation.image
        
        # Set the other parameters
        self.visible = True
        self.play_once = False
        
    def update(self, current_time):
        """
        This is called every game-tick to allow the sprite to be updated.
        """
        if self.visible:
            # Advance the animation and retrieve the current frame image from 
            # it.
            self.animation.update(current_time)
            self.image = self.animation.image

    def draw(self, target):
        """
        Draws the sprite on the target surface, which will usually be the main
        display surface. Does nothing if the sprite is currently not visible.
        """
        if self.visible:
            target.blit(self.image, self.rect)

    def on_cycle(self, animation):
        """
        Callback method, called when the animation reaches the last frame,
        before it loops back to the first frame again.
        """
        if self.play_once:
            self.visible = False

    def remove(self):
        """
        Call this to remove the sprite from the game. It will hide it, and will
        also call any assigned on_remove function, which is generally used to
        inform the owning sprite-group (if any) that the sprite should be
        removed.
        """
        self.visible = False
        if self.on_remove:
            self.on_remove(self)
            
class Asteroid(FrameSprite):
    """
    Handles a single asteroid or powerup.
    """
    spriteImage = None
    frames = None
    being_mined = False
    radius = 28
    value = 1
    
    def __init__(self, value, on_remove):
        asteroids = ["asteroid_01", "asteroid_iron_01", "asteroid_gold_01", "asteroid_emerald_01", "asteroid_powerup_mine_01", "asteroid_powerup_shield_01", "asteroid_powerup_hull_01"]
        self.value = value
        
        FrameSprite.__init__(self, g_store[asteroids[self.value - 1]], 10)

        # The size is currently hard-coded.
        self.rect = Rect(0, 0, 64, 64)
        
        # Position the asteroid somewhere randomly above the top of the screen
        self.rect.top = (0 - self.rect.height) * random.randint(1, 10)
        self.rect.left = random.randint(0, 800)
        
        self.speed = random.randint(1, 3)
        self.drift = random.randint(-2, 2)
        
        self.next_update_time = 0 # update() hasn't been called yet.
        
        self.on_remove = on_remove
        
    def update(self, current_time, bottom):
        FrameSprite.update(self, current_time)
                
        if self.next_update_time < current_time:

            if self.being_mined:
                # Asteroids which are being mined do not move
                pass
            else:
                # If we're at the bottom of the screen, remove us.
                if self.rect.bottom >= bottom - 1:
                    self.remove()
            
                self.rect.left = self.rect.left + self.drift
                    
                # Move our position down by one pixel
                self.rect.top += self.speed
    
            self.next_update_time = current_time + 10

class Asteroids(object):
    
    max_asteroids = 20
    
    def __init__(self):
        self.roids = pygame.sprite.Group()

    def clear(self):
        self.roids.empty()
        
    def update(self, current_time):
        self.roids.update(current_time, 864)
    
    def draw(self, target):
        rectlist = self.roids.draw(target)
        pygame.display.update(rectlist)

    def on_roid_die(self, roid):
        self.roids.remove(roid)
        
class Pulse(FrameSprite):
    """
    Pulse sprites represent weapon-fire (see the WeaponFire class below). For
    this game weapon-fire is always assumed to travel vertically.
    """
    
    def __init__(self, on_die):
        FrameSprite.__init__(self, g_store["weapon_02"], 10)

        # Set the default position, at the front of the ship (the X co-ordinate
        # representing the ship position will be set via the WeaponFire class).
        self.rect = Rect(0, SHIP_Y, 8, 8)

        # The speed of each pulse is randomised slightly for a better visual
        # effect (without this the pulses look like a fixed line, because they
        # always occupy the same vertical positions).
        self.speed = 12 + random.randint(0, 4)
        
        self.next_update_time = 0 # update() hasn't been called yet.
        
        self.on_die = on_die
        
    def update(self, current_time):
        FrameSprite.update(self, current_time)
                
        if self.next_update_time < current_time:

            # Move us up the screen
            self.rect.top -= self.speed
            
            if self.rect.top < -8:
                self.on_die(self)
                
            self.next_update_time = current_time + 1

class WeaponFire(object):
    """
    Base class for handling weapon-fire, using the Pulse class (above) for the
    sprites that represent the visible appearance. The WeaponFire class is
    passed the name of the sprite image to use for the pulses, so this same
    class can be used for different weapons.
    
    REFACTOR: allow this class to use different Pulse classes providing 
              different behaviours.
    """

    # Position is the point from which the weapon pulses will emanate. This
    # must be set externally before the weapon is fired.
    position = 0
    firing = False
    
    def __init__(self):
        # Always start with the weapon inactive
        self.firing = False
        
        # Store the 'pulse' sprites in a sprite group for efficiency
        self.pulses = pygame.sprite.Group()
        
    def update(self, current_time):
        if self.firing:
            # Create another pulse, place it at the current weapon position, and
            # add it to the sprite group.
            pulse = Pulse(self.on_pulse_die)
            pulse.rect.left = self.position
            self.pulses.add(pulse)
        # Update any existing pulses            
        self.pulses.update(current_time)
    
    def draw(self, target):
        # Update the 'pulses' sprite-group (this will redraw all the sprites in
        # the group)
        rectlist = self.pulses.draw(target)
        pygame.display.update(rectlist)

    def on_pulse_die(self, pulse):
        # The pulse has gone off-screen, so remove it
        self.pulses.remove(pulse)

class Mine(FrameSprite):
    """
    Sprite for the asteroid-miner.
    """
    
    is_mining = False
    mine_time = 1000
    asteroid = None
    radius = 12
    clouds = None
    ship = None
    
    def __init__(self, ship, on_remove):
        FrameSprite.__init__(self, g_store["miner_frames_01"], 10)

        # Store the reference to the Ship instance.
        self.ship = ship
        
        # The ship now has one less Mine available
        self.ship.mining_units = self.ship.mining_units - 1
        
        # Set the default position, at the front of the ship (the X co-ordinate
        # representing the ship position will be set via the MineController
        # class).
        self.rect = Rect(0, SHIP_Y, 24, 24)

        self.speed = 1
        
        self.next_update_time = 0 # update() hasn't been called yet.
        
        self.on_remove = on_remove
        
        self.clouds = FrameSprite(g_store["cloud_frames_01"], 10)
        self.clouds.visible = False
        
    def update(self, current_time):
        FrameSprite.update(self, current_time)
                
        if self.next_update_time < current_time:

            if self.is_mining:
                # Update the animated 'mining dust'
                self.clouds.update(current_time)
                # Count down the time we've spent mining
                self.mine_time = self.mine_time - 1
                if self.asteroid:
                    # If it is a normal asteroid, update the player's score
                    # with the value
                    if self.asteroid.value < 5:
                        self.ship.score = self.ship.score + self.asteroid.value
                if self.mine_time < 1:
                    # The mining-time has finished. Remove the mining unit
                    # and the asteroid
                    self.remove()
            else:
                # Move us up the screen
                self.rect.top -= self.speed

                # If we reach the top of the screen without encountering any
                # asteroids, remove the unit
                if self.rect.top < -24:
                    self.remove()
                
            self.next_update_time = current_time + 1

    def draw_clouds(self, target):
        if self.is_mining:
            self.clouds.draw(target)

    def start_mining(self):
        self.is_mining = True
        # Position the 'mining dust' animation at the top of the mining unit
        self.clouds.rect = Rect(self.rect)
        self.clouds.rect.width = 32
        self.clouds.rect.left = self.clouds.rect.left - 4
        self.clouds.rect.top = self.rect.top - 16
        self.clouds.visible = True

    def remove(self, destroyed = False):
        self.ship.mining_units = self.ship.mining_units + 1
        if self.asteroid:
            if not destroyed:
                self.ship.apply_powerup(self.asteroid.value)
            self.asteroid.remove()
        FrameSprite.remove(self)
        
class MineController(object):
    """
    Base class for handling the Mines, using the Mine class (above) for the
    sprites that represent the visible appearance.
    """

    ship = None
    
    def __init__(self, ship):
        # Store the reference to the Ship instance
        self.ship = ship
        
        # Store the 'mine' sprites in a sprite group for efficiency
        self.mines = pygame.sprite.Group()

    def clear(self):
        self.mines.empty()
        
    def update(self, current_time):
        # Update any existing mines            
        self.mines.update(current_time)

    def launch(self, position):
        # Launch a mine
        mine = Mine(self.ship, self.on_mine_remove)
        mine.rect = position
        self.mines.add(mine)
        
    def draw(self, target):
        # Update the 'mines' sprite-group (this will redraw all the sprites in
        # the group)
        rectlist = self.mines.draw(target)
        pygame.display.update(rectlist)
        [mine.draw_clouds(target) for mine in self.mines]

    def on_mine_remove(self, mine):
        # The mine has gone off-screen, so remove it
        self.mines.remove(mine)

class Burst(FrameSprite):
    """
    A Burst is the visual representation of an explosion. It is a simple frame
    sprite which doesn't move.
    """
    
    def __init__(self, on_remove = None):
        FrameSprite.__init__(self, g_store["explosion_frames_01"], 10)
        self.play_once = True
        self.on_remove = on_remove
        self.animation.on_cycle = self.on_cycle

    def on_cycle(self, animation):
        self.remove()

class Explosions(object):
    """
    A class for handling explosions in the game. This works very similarly to
    the WeaponFire class, except that the sprites that it handles to not move.
    """

    # Position is the point from which the weapon pulses will emanate. This
    # must be set externally before the weapon is fired.
    position = 0
    
    def __init__(self):
        # Store the 'burst' sprites in a sprite group for efficiency
        self.bursts = pygame.sprite.Group()
        
    def add(self, position):
        """
        Adds a new explosion at the specified co-ordinates
        """
        burst = Burst(self.on_burst_remove)
        burst.rect.left = position.left
        burst.rect.top = position.top
        self.bursts.add(burst)

    def clear(self):
        self.bursts.empty()
        
    def update(self, current_time):
        # Update any existing pulses            
        self.bursts.update(current_time)
    
    def draw(self, target):
        # Update the 'bursts' sprite-group (this will redraw all the sprites in
        # the group)
        rectlist = self.bursts.draw(target)
        pygame.display.update(rectlist)

    def on_burst_remove(self, burst):
        # The burst has finished, so remove it
        self.bursts.remove(burst)
        
class Ship(FrameSprite):
    """
    Controls and displays the player's ship
    """
    
    max_speed = 2
    acceleration = 0.05
    braking = 0.05
    shield = 0
    hull = 100
    score = 0
    mining_units = 1       # Mining units available for launch
    total_mining_units = 1 # Total mining units, including currently-deployed ones
    
    def __init__(self, x, y, container_rect):
        FrameSprite.__init__(self, g_store["ship_01"], 10)
        # Set the initial position of the ship
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.rect.width = 64
        # The container_rect is the area of the screen that the ship is confined
        # to
        self.container_rect = container_rect.copy()
        # Set the ship's initial parameters
        self.thrust_left = 0
        self.thrust_right = 0
        self.speed = 0.0
        self.powered = False
        
    def update(self, current_time):
        FrameSprite.update(self, current_time)
        if abs(self.speed) < self.max_speed:
            self.speed = self.speed + self.thrust_right
            self.speed = self.speed - self.thrust_left
        x = self.rect.left + self.speed

        if x >= self.container_rect.left and x <= self.container_rect.right:
            self.rect.left = x
        else:
            self.speed = 0
            
        if self.speed > self.braking and self.thrust_right == 0:
            self.speed = self.speed - self.braking
            if self.speed < self.braking:
                self.speed = 0
        elif self.speed < -self.braking and self.thrust_left == 0:
            self.speed = self.speed + self.braking
            if self.speed > -self.braking:
                self.speed = 0
            
    def apply_thrust_left(self, amount = 0):
        if amount == 0:
            amount = self.acceleration
        self.thrust_left = self.thrust_left + amount
        
    def apply_thrust_right(self, amount = 0):
        if amount == 0:
            amount = self.acceleration
        self.thrust_right = self.thrust_right + amount

    def release_thrust_left(self):
        self.thrust_left = 0
        
    def release_thrust_right(self):
        self.thrust_right = 0

    def apply_powerup(self, value):
        if value == 5:
            self.mining_units = self.mining_units + 1
            self.total_mining_units = self.total_mining_units + 1
            s_store["new_mining_unit"].play()
        elif value == 6:
            self.shield = min(self.shield + 25, 100)
            s_store["shield_enhanced"].play()
        elif value == 7:
            self.hull = min(self.hull + 25, 100)
            s_store["hull_integrity_restored"].play()
        
    def stop(self):
        self.thrust_left = 0
        self.thrust_right = 0
    
class Progressbar():
    """
    Draws a Progress Bar on-screen
    """
    
    def __init__(self, rect, color = pygame.color.Color('#ff0000')):
        self.rect = rect
        self.value = 0
        self.color = color
        
    def update(self, value):
        self.value = value
    
    def draw(self, target):
        self.rect.width = abs(int(self.value))
        target.fill(self.color, self.rect)
    
class Hiscore(object):
    """
    Class for reading and maintaining the hi-score table.
    """
    
    def __init__(self):
        """
        Initialises the class
        """
        self.read()
    
    def read(self):
        """
        Reads the hi-score table
        """
        # The scores are stored as a list of two-item lists.
        self.scores = []
        if os.path.exists("hiscores.txt"):
            f = open("hiscores.txt", "r")
            data = f.readlines()
            f.close()
            for line in data:
                # Remove newlines
                line = re.sub("\n", "", line)
                parts = line.split("=")
                if len(parts) == 2:
                    self.add(parts[1], int(parts[0]))
    
    def write(self):
        """
        Writes the hi-score table
        """
        fo = open("hiscores.txt", 'w')
    
        for entry in self.scores:
            line = "%d=%s\n" % (entry[0], entry[1]) 
            fo.write(line)
    
        fo.close()
    
    def position(self, value):
        """
        Returns the position that specified value would appear at in the
        hi-score table. Returns -1 if the value is not high enough to be in
        the table at all.         
        """
        if len(self.scores) == 0:
            return 0
        else:
            result = len(self.scores)
            for i in range(0, len(self.scores)):
                if self.scores[i][0] <= value:
                    result = i
                    break
            if result > 9:
                result = -1
            return result
    
    def add(self, player, score):
        pos = self.position(score)
        if pos > -1:
            self.scores[pos:pos] = [[score, player]]
            if len(self.scores) > 10:
                self.scores.pop()

class Game(object):
    """
    Main game class
    
    To use it, create an instance of Game(), then call the run() method:
    
            from game import Game
            
            newgame = Game()
            newgame.run()
    """

    # Game mode pseudo-constants
    MODE_INTRO = 1  # Opening screen. Pressing SPACE starts the game
    MODE_GAME  = 2  # Main game
    MODE_SCORE = 3  # Player is editing hi-score table
    MODE_OUTRO = 4  # 'Game Over' screen
    
    player_name = ""
    
    def __init__(self):
        logging.basicConfig(filename='jangam.log', format='%(asctime)s %(message)s', level=logging.INFO)
        
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.init()
        
        # Prepare the main display
        self.display = pygame.display.set_mode((800, 800))
        pygame.display.set_caption("Jangam")
        
        self.hiscores = Hiscore()
        
        g_store.load("graphics")
        s_store.load("sounds")

    # --------------------------------------------------------------------------
    
    def startup(self):
        """
        Creates and initialises the various game components.
        """
        self.running = True
        
        # Prepare the animations
        self.scrollers = []
        self.scrollers.append(ParallaxScroller(g_store["starfield_01a"], 0, 0, 0.1))
        self.scrollers.append(ParallaxScroller(g_store["starfield_01b"], 0, 0, 0.2))
        self.scrollers.append(ParallaxScroller(g_store["starfield_01c"], 0, 0, 0.3))
        self.next_update_time = 0
        
        # Prepare the player's ship
        self.ship = Ship(400 - 32, SHIP_Y, pygame.Rect(0, SHIP_Y, 800 - 64, 64))

        self.explosions = Explosions()
        
        self.weapon = WeaponFire()
        self.weapon.firing = False
        
        self.mines = MineController(self.ship)
        
        # Prepare the asteroids
        self.asteroids = Asteroids()
        
        # Prepare the UI screen
        self.overlay = g_store["screen_01"]
        
        # Prepare the status bars
        self.score_label  = Label("%d" % self.ship.score, SPEEDBAR_X, SPEEDBAR_Y)
        self.mine_label   = Label("%d" % self.ship.mining_units, SPEEDBAR_X, SPEEDBAR_Y + 16)
        self.hull_label   = Label("%d %%" % self.ship.hull, SPEEDBAR_X, SPEEDBAR_Y + 32)
        self.shield_label = Label("%d" % self.ship.shield, SPEEDBAR_X, SPEEDBAR_Y + 48)
        
        self.large_score_label = Label("Score: %d" % self.ship.score, 200, 32)
        self.large_score_label.set_font(os.path.join("graphics", "04B_03.ttf"), 48)
        
        self.hiscore_edit = Label("Enter your name: _", 200, 420)
        self.hiscore_edit.set_font(os.path.join("graphics", "04B_03.ttf"), 32)

        self.hiscore_labels = []
        for i in range(0, 10):
            label = Label("", 200, 320 + (i * 32))
            label.set_font(os.path.join("graphics", "04B_03.ttf"), 32)
            self.hiscore_labels.append(label)
            
        self.logo = g_store["logo"]
        
        self.end = g_store["game_over_01"]
        
        pygame.mixer.init(frequency=16000, size=-16, channels=1, buffer=4096)
        
        self.reset()
        
    # --------------------------------------------------------------------------

    def reset(self):
        """
        Resets the game to its starting parameters
        """
        self.ship.collided = False
        self.ship.shield = 0
        self.ship.hull = 100
        self.ship.score = 0
        self.ship.mining_units = 1
        self.ship.total_mining_units = 1
        self.ship.speed = 0
        self.ship.thrust_left = 0
        self.ship.thrust_right = 0
        self.ship.rect.x = 400 - 32
        
        self.explosions.clear()
        self.mines.clear()
        self.asteroids.clear()
        
        self.mode = self.MODE_INTRO
        
    # --------------------------------------------------------------------------

    def on_keydown(self, key, mods = None):
        if self.mode == self.MODE_GAME:
            if key == K_LEFT:
                self.ship.apply_thrust_left()
                
            if key == K_RIGHT:
                self.ship.apply_thrust_right()
                    
            # if key == K_z:
            #    self.weapon.firing = True

            if key == K_UP:
                if self.ship.mining_units > 0:
                    position = Rect(self.ship.rect)
                    self.mines.launch(position)
                    
        elif self.mode == self.MODE_SCORE:
            if key == K_BACKSPACE and self.player_name <> "":
                self.player_name = self.player_name[:-2]
            elif key == K_RETURN:
                self.hiscores.add(self.player_name, self.ship.score)
                self.hiscores.write()
                self.mode = self.MODE_OUTRO
                self.prepare_outro()
            # If the user presses a valid character key
            elif key >= 32 and key <= 126:
                # If the user presses the shift key while pressing another character then capitalise it
                if mods & KMOD_SHIFT:
                    key -= 32
                if len(self.player_name) < 10:
                    self.player_name = self.player_name + chr(key)
                self.hiscore_edit.text = "Enter your name: %s_" % self.player_name
            
    # --------------------------------------------------------------------------

    def on_keyup(self, key):
        if self.mode == self.MODE_GAME:
            if key == K_RIGHT:
                self.ship.release_thrust_right()
                
            if key == K_LEFT:
                self.ship.release_thrust_left()
                
            if key == K_z:
                self.weapon.firing = False        
        
    # --------------------------------------------------------------------------

    def update(self):
        """
        Main routine for updating the game.
        """
        current_time = pygame.time.get_ticks()

        # Always update the scrolling background animations
        if self.next_update_time < current_time:
            for scroller in self.scrollers:
                scroller.update()
            self.next_update_time = current_time + 10

        # Call the mode-specific update routine
        if self.mode == self.MODE_INTRO:
            self.update_intro(current_time)
        elif self.mode == self.MODE_GAME:
            self.update_game(current_time)
        elif self.mode == self.MODE_SCORE:
            self.update_score(current_time)
        elif self.mode == self.MODE_OUTRO:
            self.update_outro(current_time)

    # --------------------------------------------------------------------------

    def update_intro(self, current_time):
        """
        Updates the intro scene
        """
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                self.running = False
            elif (event.type == KEYDOWN) and (event.key == K_SPACE):
                self.mode = self.MODE_GAME
            
    # --------------------------------------------------------------------------

    def update_game(self, current_time):
        """
        Updates the main game scene
        """
        # Update the ship position
        self.ship.update(current_time)
        
        self.score_label.text  = "%d" % self.ship.score
        self.mine_label.text   = "%d" % self.ship.mining_units
        self.hull_label.text   = "%d %%" % self.ship.hull
        self.shield_label.text = "%d" % self.ship.shield
        
        self.large_score_label.text = "Score: %d" % self.ship.score

        # Possibly add a new asteroid
        if random.randint(0, 100) > 50 and len(self.asteroids.roids) < self.asteroids.max_asteroids:
            # Most asteroids have the default value of 1, but there is a 20% chance
            # that it will be a more valuable one.
            if random.randint(1, 100) > 80:
                value = random.randint(2, 4)
            else:
                value = 1
            # There is also a 10% possibility that it will be a power-up, if 
            # appropriate.
            if random.randint(1, 100) > 90:
                powerups = []
                # Only allow 5 mining units 
                if self.ship.total_mining_units < 5:
                    powerups.append(5)
                # Maximum shield strength is 100
                if self.ship.shield < 100:
                    powerups.append(6)
                # If the hull is damaged, include hull-repair powerups
                if self.ship.hull < 100:
                    powerups.append(7)
                if len(powerups):
                    value = random.choice(powerups)
                else:
                    # No power-ups available. Revert to a standard asteroid
                    value = 1
            self.asteroids.roids.add(Asteroid(value, self.asteroids.on_roid_die))
        
        # Update the asteroid positions
        self.asteroids.update(current_time)
        
        # Update any weapon fire. Set the position so that the weapon-fire
        # appears from the middle of the ship
        """
        self.weapon.position = self.ship.rect.left + 32 - 4
        self.weapon.update(current_time)
        """
        
        self.mines.update(current_time)

        # Check for collisions with asteroids
        collision = pygame.sprite.spritecollide(self.ship, self.asteroids.roids, True)
        if collision:
            # Show explosion
            self.ship.collided = True
            self.explosions.add(collision[0].rect)
            # If the ship has shields, reduce them...
            if self.ship.shield > 0:
                self.ship.shield = max(self.ship.shield - 25, 0)
            else:
                # ...otherwise apply the damage directly to the hull
                self.ship.hull = self.ship.hull - 25
                # Announce the new hull status
                if self.ship.hull == 75:
                    s_store["hull_integrity_75"].play()
                elif self.ship.hull == 50:
                    s_store["hull_integrity_50"].play()
                elif self.ship.hull == 25:
                    s_store["hull_integrity_25"].play()
                elif self.ship.hull <= 0:
                    self.ship.hull = 0
                    if self.hiscores.position(self.ship.score) <> -1:
                        self.mode = self.MODE_SCORE
                    else:
                        self.prepare_outro()
                        self.mode = self.MODE_OUTRO
                    s_store["game_over"].play()

        # Check for hitting asteroids or mines with weapon-fire
        """
        for pulse in self.weapon.pulses:
            collision = pygame.sprite.spritecollide(pulse, self.asteroids.roids, True)
            if collision:
                for sprite in collision:
                    # Show explosion
                    self.explosions.add(sprite.rect)
            collision = pygame.sprite.spritecollide(pulse, self.mines.mines, False)
            if collision:
                for sprite in collision:
                    # Show explosion
                    self.explosions.add(sprite.rect)
                    sprite.remove()
        """
        
        # Check for hitting asteroids with a miner
        for mine in self.mines.mines:
            collision = pygame.sprite.spritecollide(mine, self.asteroids.roids, False)
            for roid in collision:
                if mine.is_mining and not roid.being_mined:
                    self.explosions.add(mine.rect)
                    mine.remove(True)
                else:
                    roid.being_mined = True
                    mine.rect.left = roid.rect.left + 20
                    mine.rect.top  = roid.rect.top + roid.rect.height - 8
                    mine.asteroid = roid
                    mine.start_mining()
        
        self.explosions.update(current_time)
    
        # Handle the pygame events
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                self.running = False
            elif (event.type == KEYDOWN):
                self.on_keydown(event.key)
            elif (event.type == KEYUP):
                self.on_keyup(event.key)
            elif event.type == MOUSEBUTTONDOWN:
                # self.mouse_down(pygame.mouse.get_pos())
                pass
            elif event.type == MOUSEBUTTONUP:
                # self.mouse_up(pygame.mouse.get_pos())
                pass
            elif event.type == MOUSEMOTION:
                # self.mouse_moved(pygame.mouse.get_pos())
                pass
            
    # --------------------------------------------------------------------------

    def update_score(self, current_time):
        """
        Updates the high-score edit scene
        """
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                self.running = False
            elif (event.type == KEYDOWN):
                self.on_keydown(event.key, pygame.key.get_mods())
            
    # --------------------------------------------------------------------------

    def prepare_outro(self):
        for i in range(0, len(self.hiscores.scores)):
            self.hiscore_labels[i].text = '{0:.<12}{1:.>10d}'.format(self.hiscores.scores[i][1], self.hiscores.scores[i][0])
            
    # --------------------------------------------------------------------------

    def update_outro(self, current_time):
        """
        Updates the ending scene
        """
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                self.running = False
            elif event.type == KEYUP and event.key == K_SPACE:
                self.reset()
            
    # --------------------------------------------------------------------------
    
    def draw(self):
        """
        Main routine for drawing the display.
        """
        # Draw the background
        for scroller in self.scrollers:
            scroller.render(self.display)

        if self.mode == self.MODE_INTRO:
            # Draw the logo
            self.display.blit(self.logo, [0, 0])
            
        elif self.mode == self.MODE_GAME:
            
            # Draw any active explosions
            self.explosions.draw(self.display)
    
            # Draw the asteroids
            self.asteroids.draw(self.display)
            
            # Draw any active mines
            self.mines.draw(self.display)
    
            # Draw any active weapon fire
            self.weapon.draw(self.display)

            # Draw the ship
            self.ship.draw(self.display)
            
        elif self.mode == self.MODE_OUTRO:
            
            self.display.blit(self.end, [200, 100])
            for label in self.hiscore_labels:
                label.draw(self.display)

        elif self.mode == self.MODE_SCORE:
            
            self.display.blit(self.end, [200, 100])
            self.hiscore_edit.draw(self.display)
            
        # Update the UI
        self.display.blit(self.overlay, [0, 0])
        
        # Update the status
        self.score_label.draw(self.display)
        self.mine_label.draw(self.display)
        self.hull_label.draw(self.display)
        self.shield_label.draw(self.display)

        if self.mode in [self.MODE_GAME, self.MODE_SCORE]:
            self.large_score_label.draw(self.display)
        
        # Update the display
        pygame.display.update()
        
    # --------------------------------------------------------------------------

    def run(self):
        """
        Main game loop
        """
        self.startup()
        while self.running:
            self.update()
            self.draw()
        self.shutdown()
    
    # --------------------------------------------------------------------------

    def shutdown(self):
        """
        Cleans up before the application closes.
        """
        pygame.quit()

if __name__ == "__main__":
    test = Hiscore()

    for i in range(0, len(test.scores)):
        print '{0:.<12}{1:.>10d}'.format(test.scores[i][1], test.scores[i][0])

