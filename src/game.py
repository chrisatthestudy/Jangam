#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import os.path
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
SPEEDBAR_X = 400
SPEEDBAR_Y = 800 - 32

from time import clock

class GraphicStore(object):
    """
    Loads and stores all the graphics used in the game. The graphics are stored
    in a dictionary keyed on the name (without extension) of the graphic.
    """
    
    def __init__(self, path):
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
    
    def __init__(self, image, frame_width, speed, on_cycle = None):
        """
        Initialises the sprite, loading the base image and extracting the
        frames.
    
        Params:
            image : sprite image
            frame_width : width of each individual frame
            speed : frames per second (max. of 1000)
            on_cycle: optional callback to be invoked at the end of a cycle
        """
        self.sprite_image = image
        
        # Calculate the number of frames.
        self.frame_count = self.sprite_image.get_width() / frame_width
        
        # Set up the image size details. Assume that we are using the full
        # height of the image.
        self.frame_width = frame_width
        self.frame_height = self.sprite_image.get_height()
        
        # Extract the frames into a list of sub-surfaces, as this is more
        # efficient than creating an image for each frame.
        self.frames = []
        for frame in range(0, self.frame_count):
            offset = frame * self.frame_width
            frame = self.sprite_image.subsurface(Rect(offset, 0, frame_width, frame_width))
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
    Implements an animated sprite which has multiple frames. It is expected to
    be given an image which has all the frames laid out horizontally in 
    'filmstrip' style, from which it extracts the frames and then cycles through 
    them.
    """
    spriteImage = None
    frames = None
    animation = None
    
    def __init__(self, image, frame_width, speed):
        """
        Initialises the sprite, setting up an Animation instance to handle the
        actual animation. See the Animation class for the meaning of the
        parameters (these are passed directly on to the Animation class).
        """
        pygame.sprite.Sprite.__init__(self)
        
        # Set up the animation handler
        self.animation = Animation(image, frame_width, speed, self.on_finish)
        self.rect = self.animation.rect
        self.image = self.animation.image
        
        # Set the other parameters
        self.visible = True
        self.play_once = False
        
    def update(self, current_time):
        """
        This is called every game-tick to allow the sprite to be updated
        """
        if self.visible:
            self.animation.update(current_time)
            self.image = self.animation.image

    def draw(self, target):
        """
        Draws the sprite on the target surface. Does nothing if the sprite is
        currently not visible.
        """
        if self.visible:
            target.blit(self.image, self.rect)

    def on_finish(self, animation):
        if self.play_once:
            self.visible = False
        
class Asteroid(FrameSprite):
    
    spriteImage = None
    frames = None
    being_mined = False
    radius = 48
    
    def __init__(self, image, frame_width, speed, on_die):
        FrameSprite.__init__(self, image, frame_width, speed)
        
        self.rect = Rect(0, 0, 64, 64)
        self.rect.top = (0 - self.rect.height) * random.randint(1, 10)
        self.rect.left = random.randint(0, 800)
        
        self.speed = random.randint(1, 3)
        self.drift = random.randint(-2, 2)
        
        self.next_update_time = 0 # update() hasn't been called yet.
        
        self.on_die = on_die
        
    def update(self, current_time, bottom):
        FrameSprite.update(self, current_time)
                
        if self.next_update_time < current_time:

            if self.being_mined:
                pass
            else:
                # If we're at the bottom of the screen, move us back to the top.
                if self.rect.bottom >= bottom - 1:
                    self.rect.top = (0 - self.rect.height) * random.randint(1, 10)
                    self.rect.left = random.randint(0, 800)
            
                self.rect.left = self.rect.left + self.drift
                    
                # Move our position down by one pixel
                self.rect.top += self.speed
    
            self.next_update_time = current_time + 10

class Asteroids(object):
    
    def __init__(self, image):
        self.roids = pygame.sprite.Group()
        for i in range(50):
            self.roids.add(Asteroid(image, 64, 10, self.on_roid_die))

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
    
    def __init__(self, image, on_die):
        FrameSprite.__init__(self, image, 8, 10)

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
    
    def __init__(self, image):
        # Always start with the weapon inactive
        self.firing = False
        
        # Store the 'pulse' sprites in a sprite group for efficiency
        self.pulses = pygame.sprite.Group()
        
        # Use the same image for all the 'pulse' sprites
        self.sprite_image = image
            
    def update(self, current_time):
        if self.firing:
            # Create another pulse, place it at the current weapon position, and
            # add it to the sprite group.
            pulse = Pulse(self.sprite_image, self.on_pulse_die)
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
    radius = 48
    
    def __init__(self, image, on_die):
        FrameSprite.__init__(self, image, 64, 10)

        # Set the default position, at the front of the ship (the X co-ordinate
        # representing the ship position will be set via the MineController
        # class).
        self.rect = Rect(0, SHIP_Y, 64, 64)

        self.speed = 1
        
        self.next_update_time = 0 # update() hasn't been called yet.
        
        self.on_die = on_die
        
    def update(self, current_time):
        FrameSprite.update(self, current_time)
                
        if self.next_update_time < current_time:

            if self.is_mining:
                self.mine_time = self.mine_time - 1
                if self.mine_time < 1:
                    self.on_die(self)
                    self.asteroid.on_die(self.asteroid)
            else:
                # Move us up the screen
                self.rect.top -= self.speed
                
                if self.rect.top < -64:
                    self.on_die(self)
                
            self.next_update_time = current_time + 1

class MineController(object):
    """
    Base class for handling the Mines, using the Mine class (above) for the
    sprites that represent the visible appearance.
    """

    def __init__(self, image):
        # Store the 'mine' sprites in a sprite group for efficiency
        self.mines = pygame.sprite.Group()
        
        # Use the same image for all the 'mine' sprites
        self.sprite_image = image
            
    def update(self, current_time):
        # Update any existing mines            
        self.mines.update(current_time)

    def launch(self, position):
        # Launch a mine
        mine = Mine(self.sprite_image, self.on_mine_die)
        mine.rect = position
        self.mines.add(mine)
        
    def draw(self, target):
        # Update the 'mines' sprite-group (this will redraw all the sprites in
        # the group)
        rectlist = self.mines.draw(target)
        pygame.display.update(rectlist)

    def on_mine_die(self, mine):
        # The mine has gone off-screen, so remove it
        self.mines.remove(mine)

class Burst(FrameSprite):
    """
    A Burst is the visual representation of an explosion. It is a simple frame
    sprite which doesn't move.
    """
    
    def __init__(self, image, frame_width, speed, on_die = None):
        FrameSprite.__init__(self, image, frame_width, speed)
        self.play_once = True
        self.on_die = on_die
        self.animation.on_cycle = self.on_finish

    def on_finish(self, animation):
        self.visible = False
        if self.on_die:
            self.on_die(self)

class Explosions(object):
    """
    A class for handling explosions in the game. This works very similarly to
    the WeaponFire class, except that the sprites that it handles to not move.
    """

    # Position is the point from which the weapon pulses will emanate. This
    # must be set externally before the weapon is fired.
    position = 0
    
    def __init__(self, image):
        # Store the 'burst' sprites in a sprite group for efficiency
        self.bursts = pygame.sprite.Group()
        
        # Use the same image for all the 'burst' sprites
        self.sprite_image = image

    def add(self, position):
        """
        Adds a new explosion at the specified co-ordinates
        """
        burst = Burst(self.sprite_image, 64, 10, self.on_burst_die)
        burst.rect.left = position.left
        burst.rect.top = position.top
        self.bursts.add(burst)
        
    def update(self, current_time):
        # Update any existing pulses            
        self.bursts.update(current_time)
    
    def draw(self, target):
        # Update the 'bursts' sprite-group (this will redraw all the sprites in
        # the group)
        rectlist = self.bursts.draw(target)
        pygame.display.update(rectlist)

    def on_burst_die(self, burst):
        # The burst has finished, so remove it
        self.bursts.remove(burst)
        
class Ship(FrameSprite):
    """
    Controls and displays the player's ship
    """
    
    max_speed = 10
    acceleration = 0.05
    braking = 0.05
    
    def __init__(self, image, x, y, container_rect):
        FrameSprite.__init__(self, image, 64, 10)
        self.image = image
        self.x = x
        self.y = y
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.x, self.y)
        self.container_rect = container_rect.copy()
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
        
    def stop(self):
        self.thrust_left = 0
        self.thrust_right = 0
    
class Speedbar():
    """
    Draws a speedbar on-screen
    """
    
    def __init__(self, rect, color = pygame.color.Color('#ff0000')):
        self.rect = rect
        self.speed = 0
        self.color = color
        
    def update(self, speed):
        self.speed = speed * 10
    
    def draw(self, target):
        self.rect.width = abs(int(self.speed))
        target.fill(self.color, self.rect)
    
class Game(object):
    """
    Main game class
    
    To use it, create an instance of Game(), then call the run() method:
    
            from game import Game
            
            newgame = Game()
            newgame.run()
    """
    
    def __init__(self):
        logging.basicConfig(filename='jangam.log', format='%(asctime)s %(message)s', level=logging.INFO)
        logging.info("Start up")
        
        pygame.init()
        
        # Prepare the main display
        self.display = pygame.display.set_mode((800, 800))
        pygame.display.set_caption("Jangam")
        
        graphics = GraphicStore("graphics")
        
        # Prepare the animations
        self.scrollers = []
        self.scrollers.append(ParallaxScroller(graphics["starfield_01a"], 0, 0, 0.1))
        self.scrollers.append(ParallaxScroller(graphics["starfield_01b"], 0, 0, 0.2))
        self.scrollers.append(ParallaxScroller(graphics["starfield_01c"], 0, 0, 0.3))
        self.next_update_time = 0
        
        # Prepare the player's ship
        self.ship = Ship(graphics["ship_01"], 400 - 32, SHIP_Y, pygame.Rect(0, SHIP_Y, 800 - 64, 64))
        self.ship.collided = False

        self.explosions = Explosions(graphics["explosion_frames_01"])
        
        self.weapon = WeaponFire(graphics["weapon_01"])
        self.weapon.firing = False
        
        self.mines = MineController(graphics["miner_frames_01"])
        
        # Prepare the asteroids
        self.asteroids = Asteroids(graphics["asteroid_01"])
        
        # Prepare the UI screen
        self.overlay = graphics["screen_01"]
        
        # Prepare the status bars
        self.speedbar = Speedbar(Rect(SPEEDBAR_X, SPEEDBAR_Y, 400, 8))
        
    # --------------------------------------------------------------------------
    
    def startup(self):
        """
        Creates and initialises the various game components.
        """
        self.running = True
        
    # --------------------------------------------------------------------------

    def on_keydown(self, key):
        if key == K_LEFT:
            self.ship.apply_thrust_left()
            
        if key == K_RIGHT:
            self.ship.apply_thrust_right()
                
        if key == K_z:
            self.weapon.firing = True

        if key == K_x:
            position = Rect(self.ship.rect)
            self.mines.launch(position)
            
    # --------------------------------------------------------------------------

    def on_keyup(self, key):
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

        # Update the scrolling background animations
        if self.next_update_time < current_time:
            for scroller in self.scrollers:
                scroller.update()
            self.next_update_time = current_time + 10

        # Update the ship position
        self.ship.update(current_time)
        
        self.speedbar.update(self.ship.speed)
        
        # Update the asteroid positions
        self.asteroids.update(current_time)
        
        # Update any weapon fire. Set the position so that the weapon-fire
        # appears from the middle of the ship
        self.weapon.position = self.ship.rect.left + 32 - 4
        self.weapon.update(current_time)
        
        self.mines.update(current_time)
        
        # Check for collisions with asteroids
        collision = pygame.sprite.spritecollide(self.ship, self.asteroids.roids, True)
        if collision:
            # Show explosion
            self.ship.collided = True
            self.explosions.add(collision[0].rect)

        # Check for hitting asteroids with weapon-fire
        for pulse in self.weapon.pulses:
            collision = pygame.sprite.spritecollide(pulse, self.asteroids.roids, True)
            if collision:
                for sprite in collision:
                    # Show explosion
                    self.explosions.add(sprite.rect)

        # Check for hitting asteroids with a miner
        for mine in self.mines.mines:
            if not mine.is_mining:
                for roid in self.asteroids.roids:
                    if abs(mine.rect.left - roid.rect.left) < 40 and abs(mine.rect.top - roid.rect.top) < 40:
                        roid.being_mined = True
                        mine.is_mining = True
                        mine.rect.left = roid.rect.left
                        mine.rect.top  = roid.rect.top + roid.rect.height - 8
                        mine.asteroid = roid
        
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
    
    def draw(self):
        """
        Main routine for drawing the display.
        """
        # Draw the animations
        for scroller in self.scrollers:
            scroller.render(self.display)
        
        # Draw any active mines
        self.mines.draw(self.display)

        # Draw the ship
        self.ship.draw(self.display)

        # Draw any active explosions
        self.explosions.draw(self.display)

        # Draw the asteroids
        self.asteroids.draw(self.display)
        
        # Draw any active weapon fire
        self.weapon.draw(self.display)
        
        # Update the UI
        self.display.blit(self.overlay, [0, 0])
        
        # Update the status bars
        self.speedbar.draw(self.display)
        
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

