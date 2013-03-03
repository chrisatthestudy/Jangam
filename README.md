Jangam Retro
================================================================================
January game for OneGameAMonth #1GAM

Overview
--------------------------------------------------------------------------------
Starting with something simple...

This is a kind of 'space-invaders' style game, with the player handling a ship
which moves horizontally at the bottom of the screen, and asteroids coming down
randomly (?) from the top of the screen. The player has to avoid getting hit,
and to build up a score by mining the asteroids.

Controls:

* Right and Left arrow-keys to move
* Up arrow to launch mining-unit
* Escape key for exit

Details
--------------------------------------------------------------------------------
The ship is fixed at the bottom of the screen, and can only move left or right.

Asteroids descend from the top of the screen, moving in random directions.

If the ship is hit by an asteroid it will be damaged. If it is damaged too much
it will be destroyed, and the game ends.

The ship can launch mining units. When these collide with an asteroid they
attach themselves to it and stop it moving. They then 'mine' the asteroid, and
the player's score increases. The mining lasts for a certain length of time
(constantly adding to the score), then both the asteroid and the mining unit
are destroyed.

If an attached mining unit is struck by another asteroid, both it and the 
asteroid which it is mining are destroyed.

Most asteroids are plain rock, and only of little value.

Some asteroids contain precious metals (these are indicated visually on the
asteroid), and are of much higher value.

Dependencies
--------------------------------------------------------------------------------
* Python 2.7
* Pygame 1.9.1
