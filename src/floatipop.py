#
# Copyright (C) 2008 - Mark Dillavou
# Copyright (C) 2008 - UAB Game Developers Club (www.uab.edu/gamedev/)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

import os
import time
import math
import random
import copy

import pygame
from pygame.locals import *

from .Singleton import Singleton

WIDTH = 1024
HEIGHT = 768

# game modes
MENU = 1
GAME = 2
HIGHSCORES = 3
# current mode
MODE = MENU

DATA_DIR = 'data'

def load_image(name, colorkey=None, convert=True):
    fullname = os.path.join(DATA_DIR, name)
    try:
        image = pygame.image.load(fullname)
    except (pygame.error, message):
        print('Cannot load image:', fullname)
        raise SystemExit(message)
    if convert:
        image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()

def main():
    pygame.init()
    pygame.mixer.init()
    pygame.font.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Float-i-Pop')
    pygame.mouse.set_visible(False)

    # load high scores
    HighScore().load()

    # create some music
    pygame.mixer.music.load(os.path.join(DATA_DIR, 'battleofsteel.xm'))
    pygame.mixer.music.play(-1)

    modes = {MENU: do_menu_loop,
             GAME: do_game_loop,
             HIGHSCORES: do_highscore_loop,}

    done = False
    while not done:
        done = not modes[MODE](screen)

    pygame.quit()

    HighScore().save()

def do_menu_loop(screen):
    global MODE
    background, background_rect = load_image('menu.png')
    
    clock = pygame.time.Clock()
    pressed_time = time.time()
    while 1:
        clock.tick(60)
        current_time = time.time()

        if pygame.event.peek(pygame.QUIT):
            return False # quit

        pressed_list = pygame.key.get_pressed()
        if current_time - pressed_time > .5:
            if pressed_list[pygame.K_ESCAPE]:
                return False
            elif pressed_list[pygame.K_SPACE] or pressed_list[pygame.K_RETURN]:
                break

        screen.blit(background, (0, 0))

        pygame.display.flip()

    MODE = GAME
    return True

def do_game_loop(screen):
    global MODE

    # reset the scroll speed
    scroll_speed = 10.0

    # create a background
    background, background_rect = load_image('background.png')

    water, water_rect = load_image('water.png')

    # create the basic world
    world_rects = []
    left_rect = pygame.Rect(-5, 0, 5, HEIGHT)
    right_rect = pygame.Rect(WIDTH, 0, 5, HEIGHT)
    ceiling_rect = pygame.Rect(0, -5, WIDTH, 5)
    world_rects = [left_rect, right_rect, ceiling_rect]

    # offscreen rect to delete old objects
    delete_rect = pygame.Rect(1500, 0, 5, HEIGHT)

    screen.blit(background, (0, 0))
    pygame.display.flip()

    # create the scrolling sprites
    foreground_scrolling_sprites = pygame.sprite.Group()
    background_scrolling_sprites = pygame.sprite.Group()
    for i in range(0, WIDTH + 88, 88):
        foreground_scrolling_sprites.add(Water(i + 44, HEIGHT - (31 / 2) + 10, scroll_speed, math.pi / 2.5, 5.0 + (random.random())))
    for i in range(0, WIDTH + 88, 88):
        foreground_scrolling_sprites.add(Water(i, HEIGHT - (31 / 2) + 5, scroll_speed, 5.0 + (3.0 * random.random())))
    # clouds
    for i in range(0, 7):
        background_scrolling_sprites.add(Cloud(random.randint(-WIDTH, WIDTH * 2), random.randint(75, 350), scroll_speed))

    # objects
    object_sprites = pygame.sprite.Group()

    # movable world
    movable_sprites = pygame.sprite.Group()
    #movable_sprites.add(Platform(800, HEIGHT - 415, scroll_speed))

    # create a player
    player = Player(scroll_speed)
    player_sprites = pygame.sprite.RenderPlain((player))

    # create hud
    font = pygame.font.Font(None, 36)

    pygame.key.set_repeat(500, 30)
    clock = pygame.time.Clock()
    start_time = time.time()
    last_time = time.time()

    while 1:
        clock.tick(60)
        current_time = time.time()

        # "peek" at the event queue to see if there are any QUIT messages
        if pygame.event.peek(pygame.QUIT):
            return False
        
        pygame.event.pump()  # Let pygame handle all other messages.
        # ...Look at keypresses
        pressed_list = pygame.key.get_pressed()
        if pressed_list[pygame.K_ESCAPE]:
            break
        
        # start increasing the scroll speed
        if current_time - start_time > 25 and scroll_speed > 5: # 25 seconds
            scroll_speed -= (current_time - last_time) * .1
            # update all the objects
            player.scroll_speed = scroll_speed
            for object in foreground_scrolling_sprites:
                object.scroll_speed = scroll_speed
            for object in background_scrolling_sprites:
                object.scroll_speed = scroll_speed
            for object in object_sprites:
                object.scroll_speed = scroll_speed

        # handle input
        player.handle_keys(pressed_list)

        # create new objects
        add_random_objects(object_sprites, current_time - start_time, scroll_speed)

        # update everyone
        player_sprites.update()
        foreground_scrolling_sprites.update()
        background_scrolling_sprites.update()
        object_sprites.update()
        movable_sprites.update()

        # check for collision
        player.check_collision(world_rects, movable_sprites, object_sprites)
        # game over?
        if player.balloons <= 0:
            c_t = time.time()
            l_t = time.time()
            while player.do_death(c_t - l_t):
                l_t = c_t
                c_t = time.time()

                if pygame.event.peek(pygame.QUIT):
                    return False
        
                pygame.event.pump()  # Let pygame handle all other messages.
                pressed_list = pygame.key.get_pressed()
                if pressed_list[pygame.K_ESCAPE]:
                    break

                screen.blit(background, (0, 0))
                # draw the scrolling background
                background_scrolling_sprites.draw(screen)
                # object
                object_sprites.draw(screen)
                movable_sprites.draw(screen)
                # draw the player
                player_sprites.draw(screen)
                # draw the scrolling foreground
                foreground_scrolling_sprites.draw(screen)

                text = font.render("Score: %d" % player.score, 1, (220, 220, 220))
                textpos = text.get_rect(centerx = background.get_width()/2)
                textpos.topleft = (10, 5)
                # draw the hud
                screen.blit(text, textpos)

                # flip the display
                pygame.display.flip()

            print('Game Over')
            print('score is', int(player.score))
            HighScore().addScore(int(player.score))

            break

        # check if scrolling sprites should be deleted
        check_collision(delete_rect, object_sprites)
        check_collision(delete_rect, movable_sprites)

        text = font.render("Score: %d" % player.score, 1, (220, 220, 220))
        textpos = text.get_rect(centerx = background.get_width()/2)
        textpos.topleft = (10, 5)

        # draw the background
        screen.blit(background, (0, 0))

        # draw the scrolling background
        background_scrolling_sprites.draw(screen)
        # object
        object_sprites.draw(screen)
        movable_sprites.draw(screen)
        # draw the player
        player_sprites.draw(screen)
        # draw the scrolling foreground
        foreground_scrolling_sprites.draw(screen)

        # draw the hud
        screen.blit(text, textpos)

        # flip the display
        pygame.display.flip()

        last_time = current_time

    MODE = HIGHSCORES
    return True

def do_highscore_loop(screen):
    global MODE
    highscores, highscores_rect = load_image('highscores.png')
    
    font = pygame.font.Font(None, 48)

    clock = pygame.time.Clock()
    pressed_time = time.time()
    while 1:
        clock.tick(60)
        current_time = time.time()

        if pygame.event.peek(pygame.QUIT):
            return False

        pressed_list = pygame.key.get_pressed()
        if current_time - pressed_time > .5:
            if pressed_list[pygame.K_ESCAPE] or pressed_list[pygame.K_SPACE] or pressed_list[pygame.K_RETURN]:
                break

        screen.blit(highscores, (0, 0))

        # draw the high scores
        start_pos = (130, 210)
        skip_space = (400, 45)
        found_current = False
        for i, score in enumerate(HighScore().scores):
            col = i / 10
            row = i % 10

            color = (255, 255, 255)
            if score == HighScore().currentScore and not found_current:
                found_current = True
                color = (150, 150, 150)

            text = font.render("%d) %d" % (i + 1, score), 1, color)
            textpos = text.get_rect()
            textpos.topleft = (start_pos[0] + col * skip_space[0], start_pos[1] + row * skip_space[1])
            screen.blit(text, textpos)

        pygame.display.flip()

    MODE = MENU
    return True


def check_collision(rect, sprite_group, dokill = True):
    delete_list = []
    for i in sprite_group:
        if rect.colliderect(i):
            delete_list.append(i)

    sprite_group.remove(delete_list)

def add_random_objects(object_group, total_time, scroll_speed):
    desired_objects = random.randint(5, 5 + int(total_time * .15))
    while len(object_group) < desired_objects:
        # create a random object
        objs = [Star] * 45 + [Balloon] * 1 + [Whale] * 4
        t = random.choice(objs)
        object_group.add(t.make(scroll_speed))

class GameObject(pygame.sprite.Sprite):
    def do_collision(self, group, object):
        return False

class ScrollingSprite(GameObject):
    image = None
    def __init__(self, scroll_speed):
        GameObject.__init__(self)
        self.image = None
        self.rect = None
        self.scroll_speed = scroll_speed

        self.last_time = None

    def update(self):
        if self.last_time is None:
            self.last_time = time.time()
            return

        current_time = time.time()
        t = current_time - self.last_time
        self.last_time = current_time

        self.rect.move_ip(WIDTH / self.scroll_speed * t, 0)

class Platform(ScrollingSprite):
    def __init__(self, position_x, position_y, scroll_speed):
        ScrollingSprite.__init__(self, scroll_speed)
        if Platform.image is None:
            Platform.image, r = load_image('platform.png', -1, False)

        self.image = Platform.image
        self.rect = self.image.get_rect()
        self.rect.centerx = position_x
        self.rect.centery = position_y
        

class Cloud(ScrollingSprite):
    def __init__(self, position_x, position_y, scroll_speed):
        ScrollingSprite.__init__(self, scroll_speed)

        if Cloud.image is None:
            Cloud.image, r = load_image('clouds.png', -1)

        self.image = Cloud.image
        self.rect = self.image.get_rect()
        self.rect.centerx = position_x
        self.rect.centery = position_y

    def update(self):
        ScrollingSprite.update(self)

        if self.rect.centerx > WIDTH + (self.rect.width / 2):
            self.rect.centerx = -(random.randint(self.rect.width / 2 + 10, self.rect.width / 2 + 250))

class Balloon(ScrollingSprite):
    def __init__(self, position_x, position_y, scroll_speed):
        ScrollingSprite.__init__(self, scroll_speed)

        if Balloon.image is None:
            Balloon.image, r = load_image('balloon1.png', -1)

        self.image = Balloon.image
        self.rect = self.image.get_rect()
        self.rect.centerx = position_x
        self.rect.centery = position_y

        self.initial_x = position_x
        self.offset_x = 0

        self.vert_speed = 160

    def update(self):
        if self.last_time is None:
            self.last_time = time.time()
            return
        
        current_time = time.time()
        t = current_time - self.last_time
        self.last_time = current_time

        sin_x = math.sin(current_time * 7.0) * 10.0
        self.offset_x += WIDTH / self.scroll_speed * t

        self.rect.move_ip(0, -self.vert_speed * t)
        self.rect.centerx = self.initial_x + sin_x + self.offset_x


    def do_collision(self, group, object):
        r = object.do_add_balloon()
        if r:
            group.remove(self)
        return r

    @staticmethod
    def make(scroll_speed):
        x = random.randint(-10, -5)
        y = random.randint(15, 150)
        return Balloon(x, HEIGHT - y, scroll_speed)

class Water(ScrollingSprite):
    def __init__(self, position_x, position_y, scroll_speed, wave_offset = 0, wave_speed = 5.0):
        ScrollingSprite.__init__(self, scroll_speed)

        if Water.image is None:
            Water.image, r = load_image('water.png', -1)

        self.image = Water.image
        self.rect = self.image.get_rect()
        self.rect.centerx = position_x
        self.rect.centery = position_y
        self.start_y = position_y
        self.wave_offset = wave_offset
        self.wave_speed = wave_speed
        
        self.start_time = time.time()

    def update(self):
        ScrollingSprite.update(self)

        # up and down
        current_time = time.time()
        self.rect.centery = self.start_y + (math.sin((current_time - self.start_time) * self.wave_speed + self.wave_offset) * 5.0)

        # make us repeat
        if self.rect.centerx > WIDTH + (self.rect.width / 2):
           self.rect.centerx -= (WIDTH + self.rect.width)

class Whale(ScrollingSprite):
    def __init__(self, position_x, position_y, scroll_speed):
        ScrollingSprite.__init__(self, scroll_speed)
        
        if Whale.image is None:
            Whale.image, r = load_image('whale.png', -1, False)

        self.image = Whale.image
        self.rect = self.image.get_rect()
        self.rect.centerx = position_x
        self.rect.centery = position_y

        self.start_x = position_x
        self.start_y = position_y
        self.swim_speed = 1.2

        self.start_time = time.time()

    def update(self):
        if self.last_time is None:
            self.last_time = time.time()
            return

        # swim, i mean fly whale, fly!!
        current_time = time.time()
        t = current_time - self.last_time

        self.rect.centerx = WIDTH / self.scroll_speed * self.swim_speed * t
        self.rect.centery = self.start_y + (math.sin((current_time - self.start_time) * 4.0) * 25.0)

    def do_collision(self, group, object):
        return object.do_hit(self)

    @staticmethod
    def make(scroll_speed):
        pos = (random.randint(-200, -150), random.randint(45, HEIGHT - 45))

        return Whale(pos[0], pos[1], scroll_speed)

class Star(ScrollingSprite):
    def __init__(self, rect, vert_speed, scroll_speed, vert_displacement, initial_direction = None):
        ScrollingSprite.__init__(self, scroll_speed)

        if Star.image is None:
            Star.image, r = load_image('star.png', -1, False)

        self.image = Star.image
        self.rect = rect

        self.start_pos_y = self.rect.centery
        self.vert_speed = vert_speed
        self.vert_displacement = vert_displacement

        if initial_direction is None:
            num = random.randint(0, 1)
            if num == 0:
                self.direction = -1
            else:
                self.direction = 1
        else:
            self.direction = initial_direction

        self.last_time = None

    def update(self):
        if self.last_time is None:
            self.last_time = time.time()
            return

        current_time = time.time()
        t = current_time - self.last_time
        self.last_time = current_time

        self.rect.move_ip(WIDTH / self.scroll_speed * t, self.vert_speed * t * self.direction)
        if self.direction == 1 and self.rect.centery - self.start_pos_y > self.vert_displacement:
            self.direction = -self.direction
        elif self.direction == -1 and self.rect.centery - self.start_pos_y <= 0:
            self.direction = -self.direction

    def do_collision(self, group, object):
        return object.do_hit(self)

    @staticmethod
    def make(scroll_speed):
        pos = (random.randint(-50, -5), random.randint(15, HEIGHT - 45))
        vert_speed = random.randint(25, 100)
        displacement = random.randint(0, HEIGHT - pos[1] - 45)

        return Star(Rect(pos[0], pos[1], 32, 32), vert_speed, scroll_speed, displacement)

class Player(pygame.sprite.Sprite):
    MAX_FORCE_X = 150.0
    MAX_FORCE_Y = 150.0
    FORCE_APPLIED = 40.0
    FLAP_TIME = .09 # in seconds
    GRAVITY = -98.0 * 1.5
    RUN_FORCE = 100.0
    INVINCIBLE_TIME = 2.0
    ANIMATION_STEP = 0.1
    NUM_ANIMATIONS = 5
    def __init__(self, scroll_speed):
        pygame.sprite.Sprite.__init__(self)
        self.scroll_speed = scroll_speed
        self.images = {}
        for i in range(4):
            l = []
            for j in range(Player.NUM_ANIMATIONS):
                img = load_image('shrimp-%d-%d.png' % (i, j), -1, False)
                l.append((img[0], pygame.transform.flip(img[0], 1, 0)))
            self.images[i] = l
        # flipped images
        self.blank_image = load_image('blank.png', -1)
        self.current_image = None
        self.image_num = None

        self.animation_start_time = 0
        self.animation_num = 0
        self.image_num = 0
        self.flipped = 1

        self.force_x = 0.0
        self.force_y = 0.0

        self.start_pos_x = 50.0
        self.start_pos_y = 100.0

        self.current_pos_x = 50.0
        self.current_pos_y = 100.0

        self.offset_x = 0.0

        # direction the user is pressing keys
        self.x_dir = 0
        self.x_dir_prev = -1
        self.y_dir = 0

        self.on_ground = True

        # keey track of some time
        self.last_flap = time.time()
        self.last_time = None
        self.total_time = 0

        self.invincible = time.time()
        self.balloons = 3
        self.score = 0.0

        self.reset()

    def reset(self):
        self.balloons = 3
        self.score = 0.0
        self.space_up = True

        self.reset_position()

        # start off with 3 balloons
        self.image_num = None
        self.set_image(3)


    def handle_keys(self, key_list):
        self.x_dir = 0
        if key_list[pygame.K_LEFT]:
            if self.x_dir_prev == 1:
                self.set_image(self.image_num)
            self.x_dir = -1
        if key_list[pygame.K_RIGHT]:
            if self.x_dir_prev == -1:
                self.set_image(self.image_num, True)
            self.x_dir = 1
        if key_list[pygame.K_SPACE] and self.space_up:
            if time.time() - self.last_flap > Player.FLAP_TIME: # we are ok to flag
                self.space_up = False
                # store our new starting position
                self.start_pos_x = self.current_pos_x
                self.start_pos_y = self.current_pos_y

                # apply some force
                if self.x_dir == 0: # is the user pressing left or right?
                    if time.time() - self.last_flap < Player.FLAP_TIME * 5.0:
                        self.force_y += Player.FORCE_APPLIED  / 3.0 * 1.2
                    else:
                        self.force_y = Player.FORCE_APPLIED / 3.0 * 2.0
                else:
                    # y gets 2/3 or force, x gets 1/3
                    if time.time() - self.last_flap < Player.FLAP_TIME * 5.0:
                        self.force_y += Player.FORCE_APPLIED / 3.0 * 1.0
                    else:
                        self.force_y = Player.FORCE_APPLIED / 3.0 * 2.0
                    self.force_x += self.x_dir * Player.FORCE_APPLIED / 3.0 * 2.0

                # reset everything
                self.last_flap = time.time()
                if time.time() - self.animation_start_time >= Player.ANIMATION_STEP * (Player.NUM_ANIMATIONS - 2): # only reset if we aren't in an animation (last step = first)
                    self.animation_start_time = time.time()
                    self.animation_num = 0
                self.total_time = 0
        if not key_list[pygame.K_SPACE]: # space key is up
            self.space_up = True


        if self.force_y > Player.MAX_FORCE_Y:
            self.force_y = Player.MAX_FORCE_Y
        if self.force_x > Player.MAX_FORCE_X:
            self.force_x = Player.MAX_FORCE_X
        if self.force_x < -Player.MAX_FORCE_X:
            self.force_x = -Player.MAX_FORCE_X

        if self.x_dir != 0:
            self.x_dir_prev = self.x_dir

    def update(self):
        if self.last_time is None:
            self.last_time = time.time()
            return

        current_time = time.time()

        self.score += (current_time - self.last_time) * 10.0
        
        self.total_time += current_time - self.last_time

        if self.on_ground and self.force_y == 0:
            dx = self.force_x * self.total_time
            if self.x_dir == 0: # not moving apply "friction"
                self.force_x *= .9
                if (self.force_x < .01 and self.force_x > 0) or (self.force_x > -.01 and self.force_x < 0): # fake friction
                    self.force_x = 0
            self.current_pos_x = self.start_pos_x + dx

        else: # in air, do physics
            # find our change in x and y over time
            dx = self.force_x * self.total_time
            dy = self.force_y * self.total_time + .5 * Player.GRAVITY * (self.total_time ** 2)

            # add to our current position
            self.current_pos_x = self.start_pos_x + dx
            self.current_pos_y = self.start_pos_y + dy


        self.offset_x += float(WIDTH) / float(self.scroll_speed) * (current_time - self.last_time)

        self.rect.center = (self.current_pos_x, HEIGHT - self.current_pos_y) # - HEIGHT to inverse
        self.collision_rect.center = self.rect.center

        # update the image for animation
        self.do_animation()

        if current_time - self.invincible < Player.INVINCIBLE_TIME:
            if math.sin((current_time - self.invincible) * 100.0) > 0:
                self.image = self.current_image
            else:
                self.image = self.blank_image[0]
        else:
            self.image = self.current_image

        if self.current_pos_y < 25: # dead
            print('You Died')
            self.balloons = 0

        self.last_time = current_time

        self.on_ground = False

    def do_animation(self):
        current_time = time.time()
        if current_time - self.animation_start_time < Player.ANIMATION_STEP * Player.NUM_ANIMATIONS:
            if current_time - self.animation_start_time > Player.ANIMATION_STEP * (self.animation_num + 1):
                self.animation_num += 1
                if self.animation_num >= Player.NUM_ANIMATIONS:
                    self.animation_num = 0
                self.image = self.images[self.image_num][self.animation_num][self.flipped]
                self.current_image = self.image
        else:
            self.animation_num = 0

    def do_death(self, time):
        self.set_image(0, self.flipped)
        self.current_pos_y -= 350.0 * time
        self.rect.center = (self.current_pos_x, HEIGHT - self.current_pos_y)
        self.collision_rect.center = self.rect.center
        if self.current_pos_y < 0 - self.rect.height:
            return False
        return True

    def set_image(self, num_balloons, flipped = False):
        if flipped:
            self.image = self.images[num_balloons][self.animation_num][0]
        else:
            self.image = self.images[num_balloons][self.animation_num][1]

        self.image_num = num_balloons
        if flipped:
            self.flipped = 0
        else:
            self.flipped = 1

        self.rect = self.image.get_rect()
        self.current_image = self.image
        self.collision_rect = self.rect.inflate(-10, -10) # make the collision rect smaller
        self.image_num = num_balloons
        self.rect.center = (self.current_pos_x, HEIGHT - self.current_pos_y)
        self.collision_rect.center = self.rect.center

    def reset_position(self):
        self.offset_x = 0.0

        self.start_pos_x = 850.0
        self.start_pos_y = 500.0
        
        self.current_pos_x = 850.0
        self.current_pos_y = 500.0

        self.force_x = 0.0
        self.force_y = 0.0

        # direction the user is pressing keys
        self.x_dir_prev = -1
        self.x_dir = 0
        self.y_dir = 0

        self.on_ground = True

        # keey track of some time
        self.last_flap = time.time()
        #self.last_time = None
        self.total_time = 0

    def check_collision(self, static_world, movable_world, objects):
        # check collision
        for r in static_world:
            if self.collision_rect.colliderect(r):
                self.do_bounce(r, True)
                break

        for r in movable_world:
            if self.collision_rect.colliderect(r):
                self.do_bounce(r.rect, True)
                break

        for r in objects:
            if self.collision_rect.colliderect(r):
                if r.do_collision(objects, self):
                    break
            
    def do_hit(self, by_object):
        if time.time() - self.invincible < Player.INVINCIBLE_TIME: # still invincible
            return False

        # we are hit, update everything
        self.invincible = time.time()
        
        self.balloons -= 1
        self.x_dir_prev = -1
        self.set_image(self.balloons)
        self.do_bounce(by_object.rect, False)
        return True

    def do_add_balloon(self):
        if self.balloons < 3:
            self.balloons += 1
            self.x_dir_prev = -1
            self.set_image(self.balloons)
            return True
        return False

    def do_bounce(self, r, has_ground):
        # find the side we hit it at
        y_mult = 1.
        x_mult = 1.
        if r.centerx - self.collision_rect.centerx == 0: 
            if r.centery > self.collision_rect.centery:
                angle = -math.pi / 2.0
            else:
                angle = math.pi / 2.0
        else:
            angle = math.atan2((r.centery - self.collision_rect.centery), (r.centerx - self.collision_rect.centerx))

        rect_angle = math.atan((r.height / 2.0) / (r.width / 2.0))

        if (angle > rect_angle and angle < math.pi - rect_angle): # top
            if has_ground:
                # top, setup onground
                self.total_time = 0

                self.start_pos_x = self.current_pos_x
                self.start_pos_y = self.current_pos_y

                self.force_y = 0.0
                self.force_x += (Player.RUN_FORCE / 5.0) * self.x_dir
                if self.force_x > Player.RUN_FORCE:
                    self.force_x = Player.RUN_FORCE
                if self.force_x < -Player.RUN_FORCE:
                    self.force_x = -Player.RUN_FORCE

                self.on_ground = True
                return
            else:
                y_mutl = -.7
                if self.collision_rect.bottom > r.top:
                    self.current_pos_y += r.top - self.collision_rect.bottom
        elif (angle < -rect_angle and angle > -math.pi + rect_angle): # bottom
            y_mult = -.7
            if self.collision_rect.top < r.bottom:
                self.current_pos_y -= r.bottom - self.collision_rect.top
        elif angle < rect_angle and angle > -rect_angle: # left
            x_mult = -.7
            if self.collision_rect.right > r.left:
                self.current_pos_x -= self.collision_rect.right - r.left
        else: # right
            x_mult = -.7
            if self.collision_rect.left  < r.right:
                self.current_pos_x += r.right - self.collision_rect.left


        self.total_time = 0
        self.start_pos_x = self.current_pos_x
        self.start_pos_y = self.current_pos_y
        self.force_y *= y_mult
        self.force_x *= x_mult


class HighScore(Singleton):
    def __init__(self):
        if not self._isFirstInit():
            return

        self._prefix = os.path.expanduser('~')
        if os.name == 'nt': # windows
            self._prefix = os.environ.get('APPDATA', '.')

        self._prefix = os.path.join(self._prefix, '.floatipop')

        self.currentScore = None
        self.scores = []

    def load(self):
        try:
            f = open(os.path.join(self._prefix, 'highscores.txt'), 'r')
            self.scores = [int(x) for x in f.readlines()]
            self.scores.sort(reverse = True)
            print('current scores are', self.scores)
        except IOError:
            pass
    def save(self):
        if len(self.scores) == 0:
            return

        try: # create a directory
            os.makedirs(self._prefix)
        except OSError:
            pass

        print('save current scores are', self.scores)
        f = open(os.path.join(self._prefix, 'highscores.txt'), 'w')
        for i in self.scores:
            f.write('%d\n' % i)
        f.close()

    def addScore(self, score):
        try:
            s = int(score)

            if len(self.scores) < 20:
                self.scores.append(s)
            else:
                if s > self.scores[-1]:
                    self.scores[-1] = s

            print('add current scores are', self.scores)
            self.currentScore = s
            self.scores.sort(reverse = True)

        except ValueError:
            pass
        
if __name__ == '__main__':
    main()
