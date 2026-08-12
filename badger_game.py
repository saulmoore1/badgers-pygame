#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BADGERS (PyGame)

@author: sm5911
@date created: 08/08/2026
@date last updated: 09/08/2026

An attempt at using PyGame to make a game about badgers

"""

#%% Imports

import os
import sys
import pygame
from random import randint, choice
import numpy as np
import math

#%% Globals

# game params
WIDTH = 1200 # game screen width, height (in pixels)
HEIGHT = 800
GROUND = int(0.6 * HEIGHT)
MAX_FRAME_RATE = 60
SCALE_IMAGE = 0.05

ENEMY_SPEED = 4
MAX_ENEMIES = 5

PLAYER_SPEED = 4
JUMP_HEIGHT = 20
PLAYER_HEALTH = 5
DAMAGE_DELAY = 0 #15 # n frames after damage before able to take damage again
COLLISION_DELAY = 5 # n frame after collision before recording another collision

TILE_SIZE = 10

DIRPATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
badger_walk_dir = DIRPATH + '/graphics/badger/walk/'
badger_jump_dir = DIRPATH + '/graphics/badger/jump/'
badger_dig_dir = DIRPATH + '/graphics/badger/dig/'
enemy_walk_dir = DIRPATH + '/graphics/badger/walk/'

font_dir = DIRPATH + '/font/'
FONT_COLOUR = (64,64,64) # rgb colour

#%% Functions

class Game():
    def __init__(self, title, width, height):
        super().__init__()
        pygame.display.set_caption(title)
        self.screen = pygame.display.set_mode((width, height))
        self.rect = self.screen.get_rect()
        self.clock = pygame.time.Clock()
        self.active = False
        self.delta = 0
        self.fps = 60
        self.start_time = 0
        self.game_time = 0
        #self.background
        
        self.player = pygame.sprite.GroupSingle()
        self.enemies = pygame.sprite.Group()
        self.ground_grid = Ground() # initialise ground grid
        
    def draw(self):
        # self.surface.fill(self.background)
        pass
    
    def run(self):
        while True:
            # event loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.QUIT
                    sys.exit()

                # if event.type == pygame.MOUSEMOTION:
                #     if player.sprite.rect.collidepoint(event.pos):
                #         print("Hovering over badger")
                #     for enemy in pygame.sprite.Group.sprites(enemies):
                #         if enemy.rect.collidepoint(event.pos):
                #             print("Hovering over enemy")
            
                if not self.active: # start/restart game screen
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        self.active = True #press space to play game 
    
                        # initialise player and enemy sprite groups
                        # create instance of Player class in GroupSingle
                        # NB: enemies can be grouped together but the player needs to be in its own group
                        # so you can check for collisions (cannot check collisions between members of same group)
                        self.player.add(Player())
                        
                        self.start_time = int(pygame.time.get_ticks() / 1000)
                
                elif self.active:
                    if event.type == enemy_timer:
                        # spawn enemies if there are 5 or fewer enemies already spawned
                        if len(self.enemies) < MAX_ENEMIES:
                            # choose from list of types of enemy to spawn
                            self.enemies.add(Enemy(choice(['badger'])))
                        
                        # update timer with new random spawn time
                        pygame.time.set_timer(enemy_timer, randint(5000,10000))
                    
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
                        player_dig()
            
            # game
            if self.active:
                
                # draw sky + ground as rectangles on screen: [left, top, width, height]
                pygame.draw.rect(self.screen, 'skyblue3', [0,0,WIDTH,GROUND]) # sky
                pygame.draw.rect(self.screen, 'darkorange1', [0,GROUND,WIDTH,HEIGHT-GROUND]) # ground
                # TODO: create ground and sky surface from images instead
                
                # draw + update grid
                self.ground_grid.draw_grid()
                
                self.screen.blit(title_text_surf, title_text_rect) # blit = block image transfer
                self.game_time = display_time(self.start_time)
                        
                # draw + update player and enemy sprites
                self.player.draw(self.screen)
                self.player.update()
                self.enemies.draw(self.screen)
                self.enemies.update()
                
                # check collisions
                collision_sprite()
                                    
                # display player health + check if 0 health -> end game
                health_left = self.player.sprite.health
                display_health(health_left)
                if health_left <= 0:
                    self.active = False
                
                # update delay period after taking damage or colliding
                if self.player.sprite.damage_delay_period > 0:
                    self.player.sprite.damage_delay_period -= 1
                for enemy in pygame.sprite.Group.sprites(self.enemies):
                    if enemy.collision_delay_period > 0:
                        enemy.collision_delay_period -= 1
  
            # intro screen if game is not active
            elif not self.active:
                self.screen.fill("springgreen3")
                self.screen.blit(title_text_surf, title_text_rect)
                self.screen.blit(badger_stand_surf, badger_stand_rect)
                
                if self.game_time == 0:
                    # not started game yet
                    self.screen.blit(start_text_surf, start_text_rect)
                    
                else:            
                    # if game has been played
                    total_time_surf = stats_font.render(f'Time (s): {self.game_time}',False,FONT_COLOUR)
                    total_time_rect = total_time_surf.get_rect(bottomleft=(WIDTH-250,80))
                    self.screen.blit(total_time_surf, total_time_rect)
                    self.screen.blit(dead_text_surf, dead_text_rect)
                    self.screen.blit(restart_text_surf, restart_text_rect)
                    
                    # reset player + spawned enemies
                    self.player.empty()
                    self.enemies.empty()

            self.update()
            #self.draw()
            #pygame.display.flip()
            
            # delta time for smooth movement
            # self.delta = self.clock.tick(self.fps) * 0.001

    def update(self):
        pygame.display.update()
        self.clock.tick(self.fps)

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.player_walk_frames = badger_walk_frames
        self.animation_index = 0 # default: first frame
        self.direction = 1 # default: right
        self.player_jump = pygame.transform.rotozoom(
            pygame.image.load(badger_jump_dir+'Badger_jump_1.png').convert_alpha(),
            30, SCALE_IMAGE)
        self.player_dig = pygame.transform.rotozoom(
            pygame.image.load(badger_dig_dir + 'Badger_dig_1.png').convert_alpha(),
            -5, SCALE_IMAGE)
        self.image = self.player_walk_frames[self.animation_index]
        self.rect = self.image.get_rect(midbottom=(int(WIDTH/2),GROUND))
        self.gravity = 0 # default gravity
        self.health = PLAYER_HEALTH
        self.damage_delay_period = DAMAGE_DELAY
    
    def user_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and self.rect.bottom >= GROUND:
            self.gravity = -JUMP_HEIGHT            
        if keys[pygame.K_LEFT]:
            self.direction = -1
            self.rect.right -= PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            self.direction = 1
            self.rect.right += PLAYER_SPEED  
        if keys[pygame.K_UP]:
            if self.rect.bottom >= GROUND:
                self.rect.bottom -= PLAYER_SPEED
        if keys[pygame.K_DOWN]:
            self.rect.bottom += PLAYER_SPEED
            if self.rect.bottom >= HEIGHT:
                self.rect.bottom = HEIGHT
                
        # cycle round screen if player leaves FOV
        if self.rect.right <= 0:
            self.rect.left = WIDTH
        elif self.rect.left >= WIDTH:
            self.rect.right = 0
    
    def apply_gravity(self):
        self.gravity += 1
        if self.rect.bottom <= GROUND:
            if (GROUND - self.rect.bottom) > self.gravity:
                self.rect.bottom += self.gravity
            else:
                self.rect.bottom = GROUND
             
    def animation_state(self):
        
        # play walking animation if on ground
        if self.rect.bottom == GROUND:
            self.animation_index += 1/len(self.player_walk_frames)
            if self.animation_index >= len(self.player_walk_frames):
                self.animation_index = 0
            self.image = self.player_walk_frames[int(self.animation_index)]
            
        # diplay jump surface if above ground
        elif self.rect.bottom < GROUND:
            self.image = self.player_jump
        
        # play digging animation if below ground # TODO
        elif self.rect.bottom > GROUND:
            self.image = self.player_dig
        
        # face direction of movement
        if self.direction == -1:
            self.image = pygame.transform.flip(self.image, True, False)
        
    def update(self):
        self.user_input()
        self.apply_gravity()
        self.animation_state()        
        
class Enemy(pygame.sprite.Sprite):
    def __init__(self, type):
        super().__init__()
        
        if type == 'badger':
            self.walk_frames = badger_walk_frames
        else:
            self.walk_frames = enemy_walk_frames # default: badger
            
        self.animation_index = 0
        self.direction = -1 # default: left
        self.image = self.walk_frames[self.animation_index]
        self.rect = self.image.get_rect(bottomleft=(WIDTH,GROUND))
        self.collision_delay_period = COLLISION_DELAY
        
    def animation_state(self):
        # play walking animation if on ground
        if self.rect.bottom == GROUND:
            self.animation_index += 1/len(self.walk_frames)
            if self.animation_index >= len(self.walk_frames):
                self.animation_index = 0
            self.image = self.walk_frames[int(self.animation_index)]
            
        # face direction of movement
        if self.direction == -1:
            self.image = pygame.transform.flip(self.image, True, False)
            
    def movement(self):
        self.rect.right += ENEMY_SPEED * self.direction
        if self.rect.right <= 0: 
            self.rect.left = WIDTH
        elif self.rect.left >= WIDTH:
            self.rect.right = 0
        
    # def destroy(self):
    #     if: # if collision with player from above (player lands on top of enemy)
    #         self.kill()
    
    def update(self):
        self.animation_state()
        self.movement()
        # self.destroy()
        
def collision_sprite():
    for enemy in pygame.sprite.Group.sprites(game.enemies):
        # pygame.sprite.spritecollide(player.sprite, enemies, False)
        if pygame.sprite.collide_mask(enemy, game.player.sprite):
            if enemy.collision_delay_period <= 0:
                enemy.direction *= -1
                if game.player.sprite.damage_delay_period <= 0:
                    game.player.sprite.health -= 1
                    game.player.sprite.damage_delay_period = DAMAGE_DELAY
            enemy.collision_delay_period = COLLISION_DELAY
            
def player_dig():
    delta = math.ceil(PLAYER_SPEED / 10.0) * 10
    if game.player.sprite.rect.bottom >= GROUND:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_DOWN]: # FIXME: Dig until key released (while KEYDOWN?)
            x_left = math.floor(game.player.sprite.rect.bottomleft[0] / 10.0) * 10
            x_right = math.ceil(game.player.sprite.rect.bottomright[0] / 10.0) * 10
            y_bottom = math.floor((game.player.sprite.rect.bottom - GROUND) / 10.0) * 10
            
            game.ground_grid.grid[x_left // TILE_SIZE : x_right // TILE_SIZE,
                                  y_bottom // TILE_SIZE : (y_bottom + delta) // TILE_SIZE] = 0
        # TODO: Dig left, right, up        
        #player.sprite.direction
    

def display_time(start_time):
    game_time = int(pygame.time.get_ticks() / 1000) - start_time
    time_surf = stats_font.render(f'Time (s): {game_time}',False,(64,64,64))
    time_rect = time_surf.get_rect(bottomleft=(WIDTH-250,80))
    game.screen.blit(time_surf, time_rect)
    return game_time

def display_health(health_left):
    health_surf = stats_font.render(f'Health: {health_left}',False,(64,64,64))
    health_rect = health_surf.get_rect(bottomleft=(WIDTH-250,140))
    game.screen.blit(health_surf, health_rect)
    
class Ground():
    def __init__(self):
        super().__init__()
        self.cols = WIDTH // TILE_SIZE
        self.rows = int(HEIGHT-GROUND) // TILE_SIZE
        self.grid = np.ones((self.cols, self.rows))
        self.colour = 'darkorange4' # TODO: replace with texture?
    
    def update_grid(self, new_grid):
        self.grid = new_grid
        
    def draw_grid(self):
        for i, x in enumerate(range(0, WIDTH, TILE_SIZE)):
            for j, y in enumerate(range(0, int(HEIGHT-GROUND), TILE_SIZE)):
                if self.grid[i,j] == 1:
                    pygame.draw.rect(game.screen, self.colour, 
                                     [x, y+GROUND, TILE_SIZE, TILE_SIZE])

#%% Main game params

pygame.init()

# create display surface
screen = pygame.display.set_mode((WIDTH,HEIGHT))

# name the game
pygame.display.set_caption('Badgers!')
# TODO: Change game icon to a badger

# control frame rate
clock = pygame.time.Clock()

# font params
title_font = pygame.font.Font(font_dir + 'Ulong.ttf', 80)
dead_font = pygame.font.Font(font_dir + 'Ulong.ttf', 80)
stats_font = pygame.font.Font(font_dir + 'Ulong.ttf', 40)

# load badger images
badger_walk_frames = []
file_list = [f for f in os.listdir(badger_walk_dir) if '.png' in f]
file_list.sort()
for file in file_list:
    badger_surf = pygame.image.load(badger_walk_dir + file).convert_alpha()
    #_badger_surf = pygame.transform.scale_by(_badger_surf, (0.05, 0.05))
    badger_surf = pygame.transform.rotozoom(badger_surf, 0, SCALE_IMAGE)
    badger_walk_frames.append(badger_surf)
    
# default enemy frames = badger frames
enemy_walk_frames = badger_walk_frames

#%% Intro screen surfaces to display

badger_stand_surf = pygame.image.load(badger_walk_dir+'badger_1.png').convert_alpha()
badger_stand_surf = pygame.transform.rotozoom(badger_stand_surf, 0, 0.25)
badger_stand_rect = badger_stand_surf.get_rect(center=(int(WIDTH/2),int(HEIGHT/2)))

# title text
title_text_surf = title_font.render("Badger Game", False, FONT_COLOUR)
title_text_rect = title_text_surf.get_rect(center=(int(WIDTH/2), 80))

# dead text
dead_text_surf = dead_font.render("You Died!", False, FONT_COLOUR)
dead_text_rect = dead_text_surf.get_rect(midbottom=(int(WIDTH/2), HEIGHT-100))

# start instructions text
start_text_surf = stats_font.render("(Press space to play)", False, FONT_COLOUR)
start_text_rect = start_text_surf.get_rect(midbottom=(int(WIDTH/2), HEIGHT-50))

# restart instructions text
restart_text_surf = stats_font.render("(Press space to play again)", False, FONT_COLOUR)
restart_text_rect = restart_text_surf.get_rect(midbottom=(int(WIDTH/2), HEIGHT-50))

#%% timers

enemy_timer = pygame.USEREVENT + 1 # add +1 to avoid conflict with default pygame userevent
pygame.time.set_timer(enemy_timer, randint(5000,10000))

enemy_animation_timer = pygame.USEREVENT + 2
pygame.time.set_timer(enemy_animation_timer, 15)

#%% Event loop

# game_active = False # start on intro screen
# start_time = 0
# game_time = 0

# while True:
    
#     # event loop
#     for event in pygame.event.get():
        
#         # check when player closes the game + exit
#         if event.type == pygame.QUIT:
#             pygame.quit()
#             sys.exit() # alternatively: raise SystemExit
                        
#         if not game_active: # if game_active == False, start/restart game
#             if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
#                     game_active = True

#                     # initialise player and enemy sprite groups
#                     # create instance of Player class in GroupSingle
#                     # NB: enemies can be grouped together but the player needs to be in its own group
#                     # so you can check for collisions (cannot check collisions between members of same group)
#                     player = pygame.sprite.GroupSingle()
#                     player.add(Player())
#                     enemies = pygame.sprite.Group()
                    
#                     # initialise ground grid
#                     ground_grid = Ground()
#                     #ground_grid.grid[1:10,1:10] = 0
                    
#                     start_time = int(pygame.time.get_ticks() / 1000)
                    
#         else:
#             # if event.type == pygame.MOUSEMOTION:
#             #     if player.sprite.rect.collidepoint(event.pos):
#             #         print("Hovering over badger")
#             #     for enemy in pygame.sprite.Group.sprites(enemies):
#             #         if enemy.rect.collidepoint(event.pos):
#             #             print("Hovering over enemy")
                
#             if event.type == enemy_timer:
#                 # spawn enemies if there are 5 or fewer enemies already spawned
#                 if len(enemies) < MAX_ENEMIES:
#                     # choose from list of types of enemy to spawn
#                     enemies.add(Enemy(choice(['badger'])))
                
#                 # update timer with new random spawn time
#                 pygame.time.set_timer(enemy_timer, randint(5000,10000))
            
#             if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
#                 player_dig()
    
#     if game_active:
        
#         # draw sky + ground as rectangles on screen: [left, top, width, height]
#         sky = pygame.draw.rect(screen, 'skyblue3', [0,0,WIDTH,GROUND])
#         ground = pygame.draw.rect(screen, 'darkorange1', [0,GROUND,WIDTH,HEIGHT-GROUND])
#         # TODO: create ground and sky surface from images instead
        
#         # draw + update grid
#         ground_grid.draw_grid()
        
#         screen.blit(title_text_surf, title_text_rect) # blit = block image transfer
#         game_time = display_time(start_time)
                
#         # draw + update player and enemy sprites
#         player.draw(screen)
#         player.update()
#         enemies.draw(screen)
#         enemies.update()
        
#         # check collisions
#         collision_sprite()
                            
#         # display player health + check if 0 health -> end game
#         health_left = player.sprite.health
#         display_health(health_left)
#         if health_left <= 0:
#             game_active = False
        
#         # update delay period after taking damage or colliding
#         if player.sprite.damage_delay_period > 0:
#             player.sprite.damage_delay_period -= 1
#         for enemy in pygame.sprite.Group.sprites(enemies):
#             if enemy.collision_delay_period > 0:
#                 enemy.collision_delay_period -= 1
                
#     #%% Intro
                
#     else: # intro screen if game_active == False
#         screen.fill("springgreen3")
#         screen.blit(title_text_surf, title_text_rect)
#         screen.blit(badger_stand_surf, badger_stand_rect)
        
#         if game_time == 0:
#             # not started game yet
#             screen.blit(start_text_surf, start_text_rect)
            
#         else:            
#             # if game has been played
#             total_time_surf = stats_font.render(f'Time (s): {game_time}',False,FONT_COLOUR)
#             total_time_rect = total_time_surf.get_rect(bottomleft=(WIDTH-250,80))
#             screen.blit(total_time_surf, total_time_rect)
#             screen.blit(dead_text_surf, dead_text_rect)
#             screen.blit(restart_text_surf, restart_text_rect)
            
#             # reset player + spawned enemies
#             player.empty()
#             enemies.empty()
            
#             # reset ground grid on new game # TODO

#     # update everything
#     pygame.display.update()
    
#     # Delta time for smooth movement
#     clock.tick(MAX_FRAME_RATE)
     
#%%

if __name__ == "__main__":
    pygame.init()
    game = Game("Badgers!", WIDTH, HEIGHT)
    game.run()

    