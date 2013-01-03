#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import os.path
import logging
import random

import pygame
from pygame.locals import *

# ==============================================================================

class ParallaxScroller():
    """
    Implements a vertically scrolling area of the screen, wrapping around at the 
    top and bottom edges.
    """
    def __init__(self, imagename, x, y, speed):
        self.image = pygame.image.load(imagename).convert_alpha()
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

class Animation():
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
    
    def __init__(self, imagename, frame_width, speed, on_cycle = None):
        """
        Initialises the sprite, loading the base image and extracting the
        frames.
    
        Params:
            imagename : filename of the sprite image
            frame_width : width of each individual frame
            speed : frames per second (max. of 1000)
            on_cycle: optional callback to be invoked at the end of a cycle
        """
        # Load the image, using convert_alpha() to ensure that any transparency
        # is preserved.
        if self.sprite_image == None:
            self.sprite_image = pygame.image.load(imagename).convert_alpha()
        
        # Calculate the number of frames.
        self.frame_count = self.sprite_image.get_width() / frame_width
        print self.frame_count
        
        # Set up the image size details. Assume that we are using the full
        # height of the image.
        self.frame_width = frame_width
        self.frame_height = self.sprite_image.get_height()
        
        # Extract the frames into a list
        self.frames = []
        for frame in range(0, self.frame_count):
            offset = frame * self.frame_width
            frame = self.sprite_image.subsurface(Rect(offset, 0, 64, 64))
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
    
    def __init__(self, imagename, frame_width, speed):
        """
        Initialises the sprite, setting up an Animation instance to handle the
        actual animation. See the Animation class for the meaning of the
        parameters (these are passed directly on to the Animation class).
        """
        pygame.sprite.Sprite.__init__(self)
        
        # Set up the animation handler
        self.animation = Animation(imagename, frame_width, speed, self.on_finish)
        self.rect = self.animation.rect
        
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
    
    def __init__(self, imagename, frame_width, speed):
        FrameSprite.__init__(self, imagename, frame_width, speed)
        
        self.rect = Rect(0, 0, 64, 64)
        self.rect.top = (0 - self.rect.height) * random.randint(1, 10)
        self.rect.left = random.randint(0, 800)
        
        self.speed = random.randint(1, 3)
        self.drift = random.randint(-2, 2)
        
        self.next_update_time = 0 # update() hasn't been called yet.
        
    def update(self, current_time, bottom):
        FrameSprite.update(self, current_time)
                
        if self.next_update_time < current_time:

            # If we're at the bottom of the screen, move us back to the top.
            if self.rect.bottom >= bottom - 1:
                self.rect.top = (0 - self.rect.height) * random.randint(1, 10)
                self.rect.left = random.randint(0, 800)
        
            self.rect.left = self.rect.left + self.drift
                
            # Move our position down by one pixel
            self.rect.top += self.speed

            self.next_update_time = current_time + 10

class Asteroids():
    
    def __init__(self, imagename):
        self.roids = pygame.sprite.Group()
        for i in range(20):
            self.roids.add(Asteroid(imagename, 64, 10))

    def update(self, current_time):
        self.roids.update(current_time, 864)
    
    def draw(self, target):
        rectlist = self.roids.draw(target)
        pygame.display.update(rectlist)
    
class Ship(pygame.sprite.Sprite):
    """
    Controls and displays the player's ship
    """
    
    def __init__(self, imagename, x, y, container_rect):
        self.image = pygame.image.load(imagename).convert_alpha()
        self.x = x
        self.y = y
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.x, self.y)
        self.container_rect = container_rect.copy()
        self.thrust_x = 0
        self.thrust_y = 0
        self.powered = False
        
    def update(self):
        x = self.rect.left + self.thrust_x
        y = self.rect.top + self.thrust_y
        if x >= self.container_rect.left and x <= self.container_rect.right:
            self.rect.left = x
           
        if y >= self.container_rect.top and y <= self.container_rect.bottom:
            self.rect.top = y

        if not self.powered:
            if self.thrust_x > 0:
                self.thrust_x = self.thrust_x - 1
            if self.thrust_x < 0:
                self.thrust_x = self.thrust_x + 1
                
            if self.thrust_y > 0:
                self.thrust_y = self.thrust_y - 1
            if self.thrust_y < 0:
                self.thrust_y = self.thrust_y + 1
            
    def render(self, target):
        target.blit(self.image, self.rect)

    def apply_thrust(self, x, y):
        self.thrust_x = self.thrust_x + x
        self.thrust_y = self.thrust_y + y
        if x <> 0 or y <> 0:
            self.powered = True

    def release_thrust(self, x, y):
        self.powered = False
        
    def stop(self):
        self.thrust_x = 0
        self.thrust_y = 0
    
class Game(object):
    """
    Main game class
    
    To use it, create an instance of Game(), then call the run() method:
    
            from game import Game
            
            newgame = Game()
            newgame.run()
    """
    
    def __init__(self):
        logging.basicConfig(filename='thegame.log', format='%(asctime)s %(message)s', level=logging.INFO)
        logging.info("Start up")
        
        pygame.init()
        
        # Prepare the main display
        self.display = pygame.display.set_mode((800, 800))
        pygame.display.set_caption("TheGame")
        
        # Prepare the animations
        self.backdrop = pygame.image.load(os.path.join("graphics", "stars_00.png")).convert()
        self.scrollers = []
        self.scrollers.append(ParallaxScroller(os.path.join("graphics", "stars_01.png"), 0, 0, 0.1))
        self.next_update_time = 0
        
        # Prepare the player's ship
        self.ship = Ship(os.path.join("graphics", "ship_01.png"), 400 - 32, 800 - 64, pygame.Rect(0, 800 - 64, 800 - 64, 64))
        self.explosion = FrameSprite(os.path.join("graphics", "explosion_01.png"), 64, 10)
        self.explosion.play_once = True
        self.explosion.visible = False
        self.ship.collided = False
        
        # Prepare the asteroids
        self.asteroids = Asteroids(os.path.join("graphics", "asteroid_frames_01.png"))
        
    # --------------------------------------------------------------------------
    
    def startup(self):
        """
        Creates and initialises the various game components.
        """
        self.running = True
        
    # --------------------------------------------------------------------------

    def on_keydown(self, key):
        if key == K_RIGHT:
            self.ship.apply_thrust(1, 0)
                
        if key == K_LEFT:
            self.ship.apply_thrust(-1, 0)
            
        if key == K_UP:
            self.ship.apply_thrust(0, -1)
            
        if key == K_DOWN:
            self.ship.apply_thrust(0, 1)
        
    # --------------------------------------------------------------------------

    def on_keyup(self, key):
        self.ship.release_thrust(0, 0)        
        
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
        self.ship.update()
        
        # Update the asteroid positions
        self.asteroids.update(current_time)
        
        # Check for collisions
        collision = pygame.sprite.spritecollide(self.ship, self.asteroids.roids, True)
        if collision:
            # Show explosion
            self.ship.collided = True
            self.explosion.rect = collision[0].rect
            self.explosion.visible = True

        if self.ship.collided:
            self.explosion.update(current_time)
    
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
        self.display.blit(self.backdrop, [0, 0])
        for scroller in self.scrollers:
            scroller.render(self.display)
        
        # Draw the ship
        self.ship.render(self.display)
        if self.explosion.visible:
            self.explosion.draw(self.display)

        # Draw the asteroids
        self.asteroids.draw(self.display)
        
        # Update the display
        pygame.display.update()
        
    # --------------------------------------------------------------------------

    def on_quit(self, sender):
        self.running = False

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

