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

DIRPATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

#%% Functions

class Game():
    def __init__(self, title, width, height):
        super().__init__()
        pygame.display.set_caption(title)
        # TODO: Change game icon to a badger
        self.width = width # game screen width, height (in pixels)
        self.height = height
        self.ground = int(0.6 * self.height)
        self.screen = pygame.display.set_mode((self.width, self.height))
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
        self.max_enemies = 5
        
        # initialise ground grid
        self.ground_grid = Ground(self) 

        # intro screen
        self.title_font = pygame.font.Font(DIRPATH + '/font/Ulong.ttf', 80)
        self.stats_font = pygame.font.Font(DIRPATH + '/font/Ulong.ttf', 40)
        
        self.intro_img = load_frames(DIRPATH + '/graphics/badger/walk/', 
                                     scale_by=0.25)[0]
        self.intro_img_rect = self.intro_img.get_rect(center=(int(width/2),int(height/2)))
        
    def draw(self):
        # self.surface.fill(self.background)
        pass
    
    def run(self):
        
        # intro screen surfaces to display
        title_text_surf = self.title_font.render("Badger Game", False, (64,64,64))
        title_text_rect = title_text_surf.get_rect(center=(int(self.width/2), 80))
        dead_text_surf = self.title_font.render("You Died!", False, (64,64,64))
        dead_text_rect = dead_text_surf.get_rect(midbottom=(int(self.width/2), self.height-100))
        start_text_surf = self.stats_font.render("(Press space to play)", False, (64,64,64))
        start_text_rect = start_text_surf.get_rect(midbottom=(int(self.width/2), self.height-50))
        restart_text_surf = self.stats_font.render("(Press space to play again)", False, (64,64,64))
        restart_text_rect = restart_text_surf.get_rect(midbottom=(int(self.width/2), self.height-50))

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
                        # spawn enemies if there are n or fewer enemies already spawned
                        if len(self.enemies) < self.max_enemies:
                            # choose from list of types of enemy to spawn
                            self.enemies.add(Enemy(choice(['badger'])))
                        
                        # update timer with new random spawn time
                        pygame.time.set_timer(enemy_timer, randint(5000,10000))
                    
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
                        player_dig()
            
            # game
            if self.active:
                
                # draw sky + ground as rectangles on screen: [left, top, width, height]
                pygame.draw.rect(self.screen, 'skyblue3', 
                                 [0, 0, self.width, self.ground]) # sky
                pygame.draw.rect(self.screen, 'darkorange1', 
                                 [0, self.ground, self.width, self.height - self.ground]) # ground
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
                # if self.player.sprite.damage_delay_period > 0:
                #     self.player.sprite.damage_delay_period -= 1
                for enemy in pygame.sprite.Group.sprites(self.enemies):
                    if enemy.collision_delay_period > 0:
                        enemy.collision_delay_period -= 1
  
            # intro screen if game is not active
            elif not self.active:
                self.screen.fill("springgreen3")
                self.screen.blit(title_text_surf, title_text_rect)
                self.screen.blit(self.intro_img, self.intro_img_rect)
                
                if self.game_time == 0:
                    # not started game yet
                    self.screen.blit(start_text_surf, start_text_rect)
                    
                else:            
                    # if game has been played
                    total_time_surf = self.stats_font.render(f'Time (s): {self.game_time}',False,(64,64,64))
                    total_time_rect = total_time_surf.get_rect(bottomleft=(self.width-250,80))
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
    def __init__(self, player_type='badger'):
        super().__init__()
        self.scale_img_by = 0.05
        self.player_walk_frames = load_frames(DIRPATH + '/graphics/' + 
                                              player_type + '/walk/', 
                                              scale_by=self.scale_img_by)
        self.animation_index = 0 # default: first frame
        self.direction = 1 # default: right
        self.player_jump = load_frames(DIRPATH + '/graphics/' + 
                                       player_type + '/jump/',
                                       rotation=30, scale_by=self.scale_img_by)[0] # TODO: update to animation?
        self.player_dig = load_frames(DIRPATH + '/graphics/' + 
                                      player_type + '/dig/',
                                      rotation=-5, scale_by=self.scale_img_by)[0] # TODO: update to animation?
        self.image = self.player_walk_frames[self.animation_index]
        self.rect = self.image.get_rect(midbottom=(int(game.width/2),game.ground))
        self.jump_height = 20
        self.gravity = 0 # default gravity
        self.speed = 4
        self.health = 5
        #self.damage_delay_period = 0 # n frames after damage before able to take damage again
    
    def user_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and self.rect.bottom >= game.ground:
            self.gravity = -self.jump_height            
        if keys[pygame.K_LEFT]:
            self.direction = -1
            self.rect.right -= self.speed
        if keys[pygame.K_RIGHT]:
            self.direction = 1
            self.rect.right += self.speed
        if keys[pygame.K_UP]:
            if self.rect.bottom >= game.ground:
                self.rect.bottom -= self.speed
        if keys[pygame.K_DOWN]:
            self.rect.bottom += self.speed
            if self.rect.bottom >= game.height:
                self.rect.bottom = game.height
                
        # cycle round screen if player leaves FOV
        if self.rect.right <= 0:
            self.rect.left = game.width
        elif self.rect.left >= game.width:
            self.rect.right = 0
    
    def apply_gravity(self):
        self.gravity += 1
        if self.rect.bottom <= game.ground:
            if (game.ground - self.rect.bottom) > self.gravity:
                self.rect.bottom += self.gravity
            else:
                self.rect.bottom = game.ground
             
    def animation_state(self):
        
        # play walking animation if on ground
        if self.rect.bottom == game.ground:
            self.animation_index += 1/len(self.player_walk_frames)
            if self.animation_index >= len(self.player_walk_frames):
                self.animation_index = 0
            self.image = self.player_walk_frames[int(self.animation_index)]
            
        # diplay jump surface if above ground
        elif self.rect.bottom < game.ground:
            self.image = self.player_jump
        
        # play digging animation if below ground # TODO
        elif self.rect.bottom > game.ground:
            self.image = self.player_dig
        
        # face direction of movement
        if self.direction == -1:
            self.image = pygame.transform.flip(self.image, True, False)
        
    def update(self):
        self.user_input()
        self.apply_gravity()
        self.animation_state()        
        
class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_type='badger'):
        super().__init__()
        
        self.scale_img_by = 0.05
        #if enemy_type == '':
        self.walk_frames = load_frames(DIRPATH + '/graphics/' + 
                                       enemy_type + '/walk/', 
                                       scale_by=self.scale_img_by)
        self.animation_index = 0
        self.direction = -1 # default: left
        self.image = self.walk_frames[self.animation_index]
        self.rect = self.image.get_rect(bottomleft=(game.width, game.ground))
        self.speed = 4
        self.collision_delay_period = 5 # n frames after collision before recording another collision
        
    def animation_state(self):
        # play walking animation if on ground
        if self.rect.bottom == game.ground:
            self.animation_index += 1/len(self.walk_frames)
            if self.animation_index >= len(self.walk_frames):
                self.animation_index = 0
            self.image = self.walk_frames[int(self.animation_index)]
            
        # face direction of movement
        if self.direction == -1:
            self.image = pygame.transform.flip(self.image, True, False)
            
    def movement(self):
        self.rect.right += self.speed * self.direction
        if self.rect.right <= 0: 
            self.rect.left = game.width
        elif self.rect.left >= game.width:
            self.rect.right = 0
        
    # def destroy(self):
    #     if: # if collision with player from above (player lands on top of enemy)
    #         self.kill()
    
    def update(self):
        self.animation_state()
        self.movement()
        # self.destroy()
        
class Ground():
    def __init__(self, game):
        super().__init__()
        self.tile_size = 10
        self.cols = game.width // self.tile_size
        self.rows = int(game.height - game.ground) // self.tile_size
        self.grid = np.ones((self.cols, self.rows))
        self.colour = 'darkorange4' # TODO: replace with texture?
    
    def update_grid(self, new_grid):
        self.grid = new_grid
        
    def draw_grid(self):
        for i, x in enumerate(range(0, game.width, self.tile_size)):
            for j, y in enumerate(range(0, int(game.height - game.ground), self.tile_size)):
                if self.grid[i,j] == 1:
                    pygame.draw.rect(game.screen, self.colour, 
                                     [x, y + game.ground, self.tile_size, self.tile_size])

def load_frames(dirpath, rotation=0, scale_by=0.05, img_type='.png'):
    frames = []
    file_list = [f for f in os.listdir(dirpath) if img_type in f]
    file_list.sort()
    for file in file_list:
        surf = pygame.image.load(dirpath + file).convert_alpha()
        surf = pygame.transform.rotozoom(surf, rotation, scale_by)
        frames.append(surf)
        
    return frames
        
def collision_sprite():
    for enemy in pygame.sprite.Group.sprites(game.enemies):
        # pygame.sprite.spritecollide(player.sprite, enemies, False)
        if pygame.sprite.collide_mask(enemy, game.player.sprite):
            if enemy.collision_delay_period <= 0:
                enemy.direction *= -1
                # if game.player.sprite.damage_delay_period <= 0:
                #     game.player.sprite.health -= 1
                #     game.player.sprite.damage_delay_period = DAMAGE_DELAY
            enemy.collision_delay_period = enemy.collision_delay_period # n frames after collision before recording another collision
            
def player_dig(): # TODO: put in player class
    delta = math.ceil(game.player.sprite.speed / 10.0) * 10
    if game.player.sprite.rect.bottom >= game.ground:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_DOWN]: # FIXME: Dig until key released (while KEYDOWN?)
            x_left = math.floor(game.player.sprite.rect.bottomleft[0] / 10.0) * 10
            x_right = math.ceil(game.player.sprite.rect.bottomright[0] / 10.0) * 10
            y_bottom = math.floor((game.player.sprite.rect.bottom - game.ground) / 10.0) * 10
            
            ts = game.ground_grid.tile_size
            game.ground_grid.grid[x_left // ts : x_right // ts,
                                  y_bottom // ts : (y_bottom + delta) // ts] = 0
        # TODO: Dig left, right, up        
        #player.sprite.direction   

def display_time(start_time):
    game_time = int(pygame.time.get_ticks() / 1000) - start_time
    time_surf = game.stats_font.render(f'Time (s): {game_time}',False,(64,64,64))
    time_rect = time_surf.get_rect(bottomleft=(game.width-250, 80))
    game.screen.blit(time_surf, time_rect)
    return game_time

def display_health(health_left):
    health_surf = game.stats_font.render(f'Health: {health_left}',False,(64,64,64))
    health_rect = health_surf.get_rect(bottomleft=(game.width-250,140))
    game.screen.blit(health_surf, health_rect)
    
#%% Main

if __name__ == "__main__":
    pygame.init()
    game = Game(title="Badgers!", width=1200, height=800)
    
    # timers  
    enemy_timer = pygame.USEREVENT + 1 # add +1 to avoid conflict with default pygame userevent
    pygame.time.set_timer(enemy_timer, randint(5000,10000))
    enemy_animation_timer = pygame.USEREVENT + 2
    pygame.time.set_timer(enemy_animation_timer, 15)    

    game.run()
