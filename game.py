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

# import os
import sys
import pygame
import random
import numpy as np
import math

from scripts.utils import load_images, Animation
from scripts.entities import Player, Enemy
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particles import Particle

#%% Globals

#DIRPATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

RENDER_SCALE = 2.0

#%% Functions

class Game():
    def __init__(self):
        super().__init__()
        
        pygame.display.set_caption('Badgers!')
        pygame.display.set_icon(load_images('entities/badger/walk')[0])

        self.screen = pygame.display.set_mode((1200, 800)) # game screen width, height (in pixels)
        self.display = pygame.Surface((self.screen.get_width() // RENDER_SCALE,
                                       self.screen.get_height() // RENDER_SCALE))
        self.clock = pygame.time.Clock()
        
        self.ground = int(0.6 * self.display.get_height())
        
        self.movement = [False, False]
        
        # self.rect = self.screen.get_rect()
        # self.active = False
        # self.delta = 0
        self.fps = 60
        # self.start_time = 0
        # self.game_time = 0
        # #self.background
        self.assets = {
            'grass': load_images('tiles/grass', scale=0.05),
            'mud': load_images('tiles/mud', scale=0.05),
            'foliage': load_images('tiles/foliage', scale=0.05),
            #'background': load_image('background.png'),
            'clouds': load_images('clouds', scale=0.05),
            'enemy/idle': Animation(load_images('entities/enemy/idle', scale=0.05), img_dur=15),
            'enemy/walk': Animation(load_images('entities/enemy/walk', scale=0.05), img_dur=4),
            'player/idle': Animation(load_images('entities/badger/idle', scale=0.05), img_dur=15),
            'player/walk': Animation(load_images('entities/badger/walk', scale=0.05), img_dur=4),
            'player/jump': Animation(load_images('entities/badger/jump', scale=0.05), img_dur=5),
            'player/wall_slide': Animation(load_images('entities/badger/wall_slide', scale=0.05), img_dur=5),
            'player/dig': Animation(load_images('entities/badger/dig', scale=0.05), img_dur=5),
            'particles/leaf': Animation(load_images('particles/leaf', rotate=-45, scale=0.01), img_dur=50, loop=False),
            'particles/woosh': Animation(load_images('particles/woosh', scale=0.01), img_dur=6, loop=False),
            }
                
        self.clouds = Clouds(self.assets['clouds'], count=16)
        
        #self.player = pygame.sprite.GroupSingle()
        self.player = Player(self, # game
                             pos = (int(self.display.get_width() // RENDER_SCALE), 
                                    int(self.ground // RENDER_SCALE)), 
                             size = (8, 15)) # in pixels
        
        self.tilemap = Tilemap(self, tile_size=16)
        self.tilemap.load('map.json')
        
        # hard code a hitbox around foliage for leaf spawning
        self.leaf_spawners = []
        for tree in self.tilemap.extract([('foliage', 0)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], #x-axis
                                                  4 + tree['pos'][1], #y-axis
                                                  23, #width
                                                  13)) #height
        
        # player + enemy spawning from positions set in editor
        self.enemies = []
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)], keep=False):
            # player spawner
            if spawner['variant'] == 0:
                #print(spawner['pos'], 'player spawned')
                self.player.pos = spawner['pos']
            # enemy spawner
            else:
                #print(spawner['pos'], 'enemy spawned')
                self.enemies.append(Enemy(self, # game
                                          pos = spawner['pos'],
                                          size = (8, 15))) # in pixels
        
        #print(self.leaf_spawners)
        self.particles = []
        
        self.scroll = [0, 0]
        
        # self.enemies = pygame.sprite.Group()
        # self.max_enemies = 5
        
        # initialise ground grid
        self.ground_grid = Ground(self) 

        # # intro screen
        # self.title_font = pygame.font.Font(DIRPATH + '/font/Ulong.ttf', 80)
        # self.stats_font = pygame.font.Font(DIRPATH + '/font/Ulong.ttf', 40)
        
        # self.intro_img = load_frames(DIRPATH + '/graphics/badger/walk/', 
        #                              scale_by=0.25)[0]
        # self.intro_img_rect = self.intro_img.get_rect(center=(int(width/2),int(height/2)))
        
        #self.collision_area = pygame.Rect(50, self.ground-50, 100, 50)
                
    def run(self):
        while True:
            self.display.fill((14, 219, 248))
            #self.display.blit(self.assets['background'], (0, 0))
            
            # pan camera centered on player
            self.scroll[0] += (self.player.rect().centerx - 
                               self.display.get_width() / 2 - 
                               self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - 
                               self.display.get_height() / 2 - 
                               self.scroll[1]) / 30
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            for rect in self.leaf_spawners:
                # check if random number is less than pixel area of our rectangle
                # spawn-rate proportional to the amount of pixels that the hitbox covers
                # eg. bigger trees spawn more leaves
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width,
                           rect.y + random.random() * rect.height)
                    self.particles.append(Particle(self, 
                                                   'leaf', 
                                                   pos, 
                                                   velocity=[-0.1, 0.3], 
                                                   frame=random.randint(0, 20)))
            
            self.clouds.update()
            self.clouds.render(self.display, offset=render_scroll)
            
            self.tilemap.render(self.display, offset=render_scroll)
            
            for enemy in self.enemies.copy():
                enemy.update(self.tilemap, (0, 0)) # default no movement
                enemy.render(self.display, offset=render_scroll)
            
            self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
            self.player.render(self.display, offset=render_scroll)
            
            #print(self.tilemap.physics_rects_around(self.player.pos))
            
            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.QUIT
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = True
                    if event.key == pygame.K_UP:
                        self.player.jump()
                    if event.key == pygame.K_x:
                        self.player.dash()
                
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = False
            # movement adds up both inputs if two keys pressed
            # self.img_pos[1] += self.movement[1] - self.movement[0] * self.movement_speed 
                       
    # def update(self):
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(self.fps)
            
    # def run(self):
        
    #     # intro screen surfaces to display
    #     title_text_surf = self.title_font.render("Badger Game", False, (64,64,64))
    #     title_text_rect = title_text_surf.get_rect(center=(int(self.width/2), 80))
    #     dead_text_surf = self.title_font.render("You Died!", False, (64,64,64))
    #     dead_text_rect = dead_text_surf.get_rect(midbottom=(int(self.width/2), self.height-100))
    #     start_text_surf = self.stats_font.render("(Press space to play)", False, (64,64,64))
    #     start_text_rect = start_text_surf.get_rect(midbottom=(int(self.width/2), self.height-50))
    #     restart_text_surf = self.stats_font.render("(Press space to play again)", False, (64,64,64))
    #     restart_text_rect = restart_text_surf.get_rect(midbottom=(int(self.width/2), self.height-50))

    #     while True:
    #         # event loop
    #         for event in pygame.event.get():
    #             if event.type == pygame.QUIT:
    #                 pygame.QUIT
    #                 sys.exit()

    #             # if event.type == pygame.MOUSEMOTION:
    #             #     if player.sprite.rect.collidepoint(event.pos):
    #             #         print("Hovering over badger")
    #             #     for enemy in pygame.sprite.Group.sprites(enemies):
    #             #         if enemy.rect.collidepoint(event.pos):
    #             #             print("Hovering over enemy")
            
    #             if not self.active: # start/restart game screen
    #                 if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
    #                     self.active = True #press space to play game 
    
    #                     # initialise player and enemy sprite groups
    #                     # create instance of Player class in GroupSingle
    #                     # NB: enemies can be grouped together but the player needs to be in its own group
    #                     # so you can check for collisions (cannot check collisions between members of same group)
    #                     self.player.add(Player(game=self, player_type='badger',
    #                                            pos=[], size=[]))
                        
    #                     self.start_time = int(pygame.time.get_ticks() / 1000)
                
    #             elif self.active:
    #                 if event.type == enemy_timer:
    #                     # spawn enemies if there are n or fewer enemies already spawned
    #                     if len(self.enemies) < self.max_enemies:
    #                         # choose from list of types of enemy to spawn
    #                         self.enemies.add(Enemy(choice(['badger'])))
                        
    #                     # update timer with new random spawn time
    #                     pygame.time.set_timer(enemy_timer, randint(5000,10000))
                    
    #                 if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
    #                     player_dig()
            
    #         # game
    #         if self.active:
                
    #             # draw sky + ground as rectangles on screen: [left, top, width, height]
    #             pygame.draw.rect(self.screen, (14, 219, 248), 
    #                              [0, 0, self.width, self.ground]) # sky
    #             pygame.draw.rect(self.screen, 'darkorange1', 
    #                              [0, self.ground, self.width, self.height - self.ground]) # ground
    #             # TODO: create ground and sky surface from images instead
                
    #             # draw + update grid
    #             self.ground_grid.draw_grid()
                
    #             self.screen.blit(title_text_surf, title_text_rect) # blit = block image transfer
    #             self.game_time = display_time(self.start_time)

    #             # check collisions
    #             collision_sprite()
    #             # update delay period after taking damage or colliding
    #             # if self.player.sprite.damage_delay_period > 0:
    #             #     self.player.sprite.damage_delay_period -= 1
    #             for enemy in pygame.sprite.Group.sprites(self.enemies):
    #                 if enemy.collision_delay_period > 0:
    #                     enemy.collision_delay_period -= 1
                
    #             # # light up if player eneters this area
    #             # if self.player.sprite.rect.colliderect(self.collision_area):
    #             #     pygame.draw.rect(self.screen, (0,100,255), self.collision_area)
                        
    #             # draw + update player and enemy sprites
    #             self.player.draw(self.screen)
    #             self.player.update()
    #             self.enemies.draw(self.screen)
    #             self.enemies.update()
                                                    
    #             # display player health + check if 0 health -> end game
    #             health_left = self.player.sprite.health
    #             display_health(health_left)
    #             if health_left <= 0:
    #                 self.active = False
                  
    #         # intro screen if game is not active
    #         elif not self.active:
    #             self.screen.fill("springgreen3")
    #             self.screen.blit(title_text_surf, title_text_rect)
    #             self.screen.blit(self.intro_img, self.intro_img_rect)
                
    #             if self.game_time == 0:
    #                 # not started game yet
    #                 self.screen.blit(start_text_surf, start_text_rect)
                    
    #             else:            
    #                 # if game has been played
    #                 total_time_surf = self.stats_font.render(f'Time (s): {self.game_time}',False,(64,64,64))
    #                 total_time_rect = total_time_surf.get_rect(bottomleft=(self.width-250,80))
    #                 self.screen.blit(total_time_surf, total_time_rect)
    #                 self.screen.blit(dead_text_surf, dead_text_rect)
    #                 self.screen.blit(restart_text_surf, restart_text_rect)
                    
    #                 # reset player + spawned enemies
    #                 self.player.empty()
    #                 self.enemies.empty()

    #         self.update()
    #         #self.draw()
    #         #pygame.display.flip()
            
    #         # delta time for smooth movement
    #         # self.delta = self.clock.tick(self.fps) * 0.001

    # def update(self):
    #     pygame.display.update()
    #     self.clock.tick(self.fps)

# class Player(pygame.sprite.Sprite):
#     def __init__(self, game, player_type, pos, size):
#         super().__init__()
#         self.game = game
#         self.type = player_type
#         self.pos = list(pos)
#         self.size = size
#         self.velocity = [0, 0]
        
#         self.scale_img_by = 0.05
#         self.player_walk_frames = load_frames(DIRPATH + '/graphics/' + 
#                                               self.type + '/walk/', 
#                                               scale_by=self.scale_img_by)
#         self.animation_index = 0 # default: first frame
#         self.direction = 1 # default: right
#         self.player_jump = load_frames(DIRPATH + '/graphics/' + 
#                                        self.type + '/jump/',
#                                        rotation=30, scale_by=self.scale_img_by)[0] # TODO: update to animation?
#         self.player_dig = load_frames(DIRPATH + '/graphics/' + 
#                                       self.type + '/dig/',
#                                       rotation=-5, scale_by=self.scale_img_by)[0] # TODO: update to animation?
#         self.image = self.player_walk_frames[self.animation_index]
#         self.rect = self.image.get_rect(midbottom=(int(game.width/2),game.ground))
#         self.jump_height = 20
#         self.gravity = 0 # default gravity
#         self.movement_speed = 5
#         self.health = 5
#         #self.damage_delay_period = 0 # n frames after damage before able to take damage again
#         # self.movement = [False, False]
        
#     def user_input(self):
        
#         # for event in pygame.event.get():
#         #     if event.type == pygame.KEYDOWN:
#         #         if event.key == pygame.K_UP:
#         #             self.movement[0] = True
#         #         if event.key == pygame.K_DOWN:
#         #             self.movement[1] = True
#         # movement adds up both inputs if two keys pressed
#         # self.img_pos[1] += self.movement[1] - self.movement[0] * self.movement_speed 
        
        
#         keys = pygame.key.get_pressed()
#         if keys[pygame.K_SPACE] and self.rect.bottom >= game.ground:
#             self.gravity = -self.jump_height            
#         if keys[pygame.K_LEFT]:
#             self.direction = -1
#             self.rect.right -= self.movement_speed
#         if keys[pygame.K_RIGHT]:
#             self.direction = 1
#             self.rect.right += self.movement_speed
#         if keys[pygame.K_UP]:
#             if self.rect.bottom >= game.ground:
#                 self.rect.bottom -= self.movement_speed
#         if keys[pygame.K_DOWN]:
#             self.rect.bottom += self.movement_speed
#             if self.rect.bottom >= game.height:
#                 self.rect.bottom = game.height
                
#         # cycle round screen if player leaves FOV
#         if self.rect.right <= 0:
#             self.rect.left = game.width
#         elif self.rect.left >= game.width:
#             self.rect.right = 0
    
#     def apply_gravity(self):
#         self.gravity += 1
#         if self.rect.bottom <= game.ground:
#             if (game.ground - self.rect.bottom) > self.gravity:
#                 self.rect.bottom += self.gravity
#             else:
#                 self.rect.bottom = game.ground
             
#     def animation_state(self):
        
#         # play walking animation if on ground
#         if self.rect.bottom == game.ground:
#             self.animation_index += 1/len(self.player_walk_frames)
#             if self.animation_index >= len(self.player_walk_frames):
#                 self.animation_index = 0
#             self.image = self.player_walk_frames[int(self.animation_index)]
            
#         # diplay jump surface if above ground
#         elif self.rect.bottom < game.ground:
#             self.image = self.player_jump
        
#         # play digging animation if below ground # TODO
#         elif self.rect.bottom > game.ground:
#             self.image = self.player_dig
        
#         # face direction of movement
#         if self.direction == -1:
#             self.image = pygame.transform.flip(self.image, True, False)
        
#     def update(self, movement=(0, 0)):
#         # frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        
#         # self.pos[0] += frame_movement[0]
#         # self.pos[1] += frame_movement[1]
        
#         self.user_input()
#         self.apply_gravity()
#         self.animation_state()        
        
#     def render(self, surf):
#         surf.blit(self.game.assets['player'], self.pos)
        
        
# class Enemy(pygame.sprite.Sprite):
#     def __init__(self, enemy_type='badger'):
#         super().__init__()
        
#         self.scale_img_by = 0.05
#         #if enemy_type == '':
#         self.walk_frames = load_frames(DIRPATH + '/graphics/' + 
#                                        enemy_type + '/walk/', 
#                                        scale_by=self.scale_img_by)
#         self.animation_index = 0
#         self.direction = -1 # default: left
#         self.image = self.walk_frames[self.animation_index]
#         # self.image.set_colorkey((0,0,0)) # replace black background in sprite img
#         self.rect = self.image.get_rect(bottomleft=(game.width, game.ground))
#         self.movement_speed = 4
#         self.collision_delay_period = 5 # n frames after collision before recording another collision
        
#     def animation_state(self):
#         # play walking animation if on ground
#         if self.rect.bottom == game.ground:
#             self.animation_index += 1/len(self.walk_frames)
#             if self.animation_index >= len(self.walk_frames):
#                 self.animation_index = 0
#             self.image = self.walk_frames[int(self.animation_index)]
            
#         # face direction of movement
#         if self.direction == -1:
#             self.image = pygame.transform.flip(self.image, True, False)
            
#     def movement(self):
#         self.rect.right += self.movement_speed * self.direction
#         if self.rect.right <= 0: 
#             self.rect.left = game.width
#         elif self.rect.left >= game.width:
#             self.rect.right = 0
        
#     # def destroy(self):
#     #     if: # if collision with player from above (player lands on top of enemy)
#     #         self.kill()
    
#     def update(self):
#         self.animation_state()
#         self.movement()
#         # self.destroy()
        
class Ground():
    def __init__(self, game):
        super().__init__()
        self.tile_size = 10
        self.cols = game.display.get_width() // self.tile_size
        self.rows = int(game.display.get_height() - game.ground) // self.tile_size
        self.grid = np.ones((self.cols, self.rows))
        self.colour = 'darkorange4' # TODO: replace with texture?
    
    def update_grid(self, new_grid):
        self.grid = new_grid
        
    def draw_grid(self):
        for i, x in enumerate(range(0, game.display.get_width(), self.tile_size)):
            for j, y in enumerate(range(0, int(game.display.get_height() - game.ground), self.tile_size)):
                if self.grid[i,j] == 1:
                    pygame.draw.rect(game.display, self.colour, 
                                     [x, y + game.ground, self.tile_size, self.tile_size])
        
# def collision_sprite():
#     for enemy in pygame.sprite.Group.sprites(game.enemies):
#         # pygame.sprite.spritecollide(player.sprite, enemies, False)
#         if pygame.sprite.collide_mask(enemy, game.player.sprite):
#             if enemy.collision_delay_period <= 0:
#                 enemy.direction *= -1
#                 # if game.player.sprite.damage_delay_period <= 0:
#                 #     game.player.sprite.damage_delay_period = 5 # damage delay
#                 game.player.sprite.health -= 1
#             enemy.collision_delay_period = 5 # n frames after collision before recording another collision
            
# def player_dig(): # TODO: put in player class
#     delta = math.ceil(game.player.sprite.speed / 10.0) * 10
#     if game.player.sprite.rect.bottom >= game.ground:
#         keys = pygame.key.get_pressed()
#         if keys[pygame.K_DOWN]: # FIXME: Dig until key released (while KEYDOWN?)
#             x_left = math.floor(game.player.sprite.rect.bottomleft[0] / 10.0) * 10
#             x_right = math.ceil(game.player.sprite.rect.bottomright[0] / 10.0) * 10
#             y_bottom = math.floor((game.player.sprite.rect.bottom - game.ground) / 10.0) * 10
            
#             ts = game.ground_grid.tile_size
#             game.ground_grid.grid[x_left // ts : x_right // ts,
#                                   y_bottom // ts : (y_bottom + delta) // ts] = 0
#         # TODO: Dig left, right, up        
#         #player.sprite.direction   

# def display_time(start_time):
#     game_time = int(pygame.time.get_ticks() / 1000) - start_time
#     time_surf = game.stats_font.render(f'Time (s): {game_time}',False,(64,64,64))
#     time_rect = time_surf.get_rect(bottomleft=(game.width-250, 80))
#     game.screen.blit(time_surf, time_rect)
#     return game_time

# def display_health(health_left):
#     health_surf = game.stats_font.render(f'Health: {health_left}',False,(64,64,64))
#     health_rect = health_surf.get_rect(bottomleft=(game.width-250,140))
#     game.screen.blit(health_surf, health_rect)
    
#%% Main

if __name__ == "__main__":
    pygame.init()
    game = Game()
    
    # timers  
    # enemy_timer = pygame.USEREVENT + 1 # add +1 to avoid conflict with default pygame userevent
    # pygame.time.set_timer(enemy_timer, randint(5000,10000))
    # enemy_animation_timer = pygame.USEREVENT + 2
    # pygame.time.set_timer(enemy_animation_timer, 15)    

    game.run()
