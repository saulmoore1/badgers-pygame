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
import random
import math

from scripts.utils import load_image, load_images, Animation
from scripts.entities import Player, Enemy
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particles import Particle
from scripts.sparks import Spark

#%% Globals

#DIRPATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

RENDER_SCALE = 2.0
IMG_SCALE = 0.05
DISPLAY_SIZE = (1280, 720)

LEVEL = 0

#%% Functions

class Game():
    def __init__(self):
        super().__init__()
        
        pygame.display.set_caption('Badgers!')
        pygame.display.set_icon(load_images('entities/badger/walk')[0])

        self.screen = pygame.display.set_mode(DISPLAY_SIZE) # game screen width, height (in pixels)
        # display surface (outline applied)
        self.display = pygame.Surface((self.screen.get_width() // RENDER_SCALE,
                                       self.screen.get_height() // RENDER_SCALE),
                                      pygame.SRCALPHA)
        # second display surface (no outline applied)
        self.display_2 = pygame.Surface((self.screen.get_width() // RENDER_SCALE,
                                         self.screen.get_height() // RENDER_SCALE))
        
        self.clock = pygame.time.Clock()
        self.fps = 60                
        self.movement = [False, False, False, False]
        
        # self.rect = self.screen.get_rect()
        self.active = False
        self.game_time = 0

        # self.delta = 0
        # self.start_time = 0
        self.ground = int(0.6 * self.display.get_height())

        self.assets = {
            'grass': load_images('tiles/grass', scale=IMG_SCALE),
            'mud': load_images('tiles/mud', scale=IMG_SCALE),
            'foliage': load_images('tiles/foliage', scale=IMG_SCALE),
            'background': load_image('background/0.png'),
            'startscreen': load_image('entities/badger/idle/Badger_5.png', scale=0.2),
            'clouds': load_images('clouds', scale=0.1),
            'enemy/idle': Animation(load_images('entities/enemy/idle', scale=IMG_SCALE), img_dur=15),
            'enemy/walk': Animation(load_images('entities/enemy/walk', scale=IMG_SCALE), img_dur=4),
            'player/idle': Animation(load_images('entities/badger/idle', scale=IMG_SCALE), img_dur=15),
            'player/walk': Animation(load_images('entities/badger/walk', scale=IMG_SCALE), img_dur=4),
            'player/jump': Animation(load_images('entities/badger/jump', scale=IMG_SCALE), img_dur=5),
            'player/wall_slide': Animation(load_images('entities/badger/wall_slide', scale=IMG_SCALE), img_dur=5),
            'player/dig': Animation(load_images('entities/badger/dig', scale=IMG_SCALE), img_dur=5),
            'particles/leaf': Animation(load_images('particles/leaf', rotate=-45, scale=0.01), img_dur=50, loop=False),
            'particles/woosh': Animation(load_images('particles/woosh', scale=0.01), img_dur=6, loop=False),
            'gun': load_image('weapons/gun.png', scale=0.01),
            'bullet': load_image('weapons/bullet.png', scale=0.007)
            }
        
        # scale background to the dimensions of the display
        w, h = self.assets['background'].get_size()
        sw, sh = self.display.get_size()
        self.assets['background'] = pygame.transform.scale(self.assets['background'], 
                                                           (int(sh/h * w), sh)) # keep ratio
        
        # sounds effects
        self.sfx = {
            'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
            'walk': pygame.mixer.Sound('data/sfx/walk.wav'),
            'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
            'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
            'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
            'ambience': pygame.mixer.Sound('data/sfx/ambience.wav'),
            #'death': pygame.mixer.Sound('data/sfx/death.wav')
            }
        
        self.sfx['jump'].set_volume(0.3)
        self.sfx['walk'].set_volume(0.3)
        self.sfx['dash'].set_volume(0.5)
        self.sfx['hit'].set_volume(0.5)
        self.sfx['shoot'].set_volume(0.3)
        self.sfx['ambience'].set_volume(0.5)
        #self.sfx['death'].set_volume(0.9)

        self.clouds = Clouds(self.assets['clouds'], count=8)
        
        #self.player = pygame.sprite.GroupSingle()
        self.player = Player(self, # game
                             pos = (int(self.display.get_width() // RENDER_SCALE), 
                                    int(self.ground // RENDER_SCALE)), 
                             size = self.assets['player/walk'].max_dims())
        
        self.tilemap = Tilemap(self, tile_size=self.assets['grass'][0].get_width())
        
        self.level = LEVEL
        self.load_level(self.level)
        
        self.screenshake = 0
                
        # self.max_enemies = 5

        self.large_font = pygame.font.Font('data/font/Ulong.ttf', 60)
        self.small_font = pygame.font.Font('data/font/Ulong.ttf', 40)
                                
    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')
        
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
                self.player.air_time = 0 # to avoid trigger multiple times
                #print(spawner['pos'], 'player spawned')
                self.player.pos = spawner['pos']
            # enemy spawner
            else:
                #print(spawner['pos'], 'enemy spawned')
                self.enemies.append(Enemy(self, # game
                                          pos = spawner['pos'],
                                          size = self.assets['enemy/walk'].max_dims()))
        self.projectiles = []
        self.particles = []
        self.sparks = []
        
        self.scroll = [0, 0]
        self.dead = 0
        self.transistion = -30 # 
    
    def run(self):
        # pygame.mixer.music.load('data/music.wav')
        # pygame.mixer.music.set_volume(0.5)
        # pygame.mixer.music.play(-1) # -1 = loop forever
                
        self.sfx['ambience'].play(-1)

        while True:
            if self.active:
                self.display.fill((0, 0, 0, 0)) # (r,g,b,alpha) - transparent display to blit surfaces to
                
                # background (set to base colour then overlay image - in center of screen)
                self.display_2.fill((14, 219, 248))
                w, h = self.assets['background'].get_size()
                sw, sh = self.display.get_size()
                self.display_2.blit(self.assets['background'], ((int(sw - sh/h * w) / 2), 0))
                
                self.screenshake = max(0, self.screenshake - 1) # screenshake timer
                
                # if all of the enemies are dead, transistion level
                if not len(self.enemies):
                    self.transistion += 1
                    if self.transistion > 30:
                        # load next level if exists (check n levels in data/maps dir)
                        self.level = min(self.level + 1, len(os.listdir('data/maps/')) - 1)
                        self.load_level(self.level) # load level during full blackscreen
                if self.transistion < 0:
                    self.transistion += 1
                
                # increment damage counter if player hit during frame
                if self.dead:
                    self.dead += 1
                    if self.dead >= 10:
                        # if dead do not transisiton to next level (do not exceed 30)
                        self.transistion = min(30, self.transistion + 1)
                    if self.dead > 40:
                        self.load_level(self.level)
                
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
                self.clouds.render(self.display_2, offset=render_scroll)
                
                self.tilemap.render(self.display, offset=render_scroll)
                
                for enemy in self.enemies.copy():
                    kill = enemy.update(self.tilemap, (0, 0)) # default no movement
                    enemy.render(self.display, offset=render_scroll)
                    if kill:
                        self.enemies.remove(enemy)
                    
                if not self.dead:
                    self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                    # self.player.update(self.tilemap, (self.movement[1] - self.movement[0],
                    #                                   self.movement[3] - self.movement[2]))
                    self.player.render(self.display, offset=render_scroll)
                    #print(self.tilemap.physics_rects_around(self.player.pos))
                    
                # TODO: Save option in game to save game state (tilemap, player pos, enemy pos+spawn, etc)
                
                # [[x, y], direction, timer]
                for projectile in self.projectiles.copy():
                    projectile[0][0] += projectile[1] # x pos
                    projectile[2] += 1 # timer
                    img = self.assets['bullet']
                    self.display.blit(img, 
                                      (projectile[0][0] - img.get_width() / 2 - render_scroll[0], 
                                       projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
                    # make projectile disappear when it hits a wall
                    if self.tilemap.solid_check(projectile[0]):
                        self.projectiles.remove(projectile)
                        # sparks when projectile hits wall 
                        for i in range(4):
                            self.sparks.append(Spark(projectile[0], # last projectile position
                                                     # sparks left only if projectile is going right, and vice versa
                                                     random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0),
                                                     2 + random.random())) # random speed
                    # projectile timeout after 6 seconds
                    elif projectile[2] > 360:
                        self.projectiles.remove(projectile)
                    # check if bullet hits the player (if not dashing)
                    # player is invincible while dashing
                    elif abs(self.player.dashing) < 50:
                        if self.player.rect().collidepoint(projectile[0]):
                            # TODO: Look into using masks for pixel-perfect collisions
                            self.projectiles.remove(projectile)
                            # damage player when hit
                            self.dead += 1
                            self.sfx['hit'].play() # default = play only once
                            # shake screen when player is hit
                            self.screenshake = max(16, self.screenshake)
                            # sparks + particles when projectile hits the player
                            for i in range(30):
                                angle = random.random() * math.pi * 2 # random direction in a full circle
                                speed = random.random() * 5
                                self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
                                self.particles.append(Particle(self, 
                                                               'woosh', 
                                                               self.player.rect().center,
                                                               velocity=[math.cos(angle + math.pi) * speed * 0.5,
                                                                         math.sin(angle + math.pi) * speed * 0.5],
                                                               frame=random.randint(0, 7)))
                            
                for spark in self.sparks.copy():
                    kill = spark.update()
                    spark.render(self.display, offset=render_scroll)
                    if kill:
                        self.sparks.remove(spark)
                            
                for particle in self.particles.copy():
                    kill = particle.update()
                    particle.render(self.display_2, offset=render_scroll)
                    if particle.type == 'leaf':
                        particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                    if kill:
                        self.particles.remove(particle)
                        
                # create sillhouette
                display_mask = pygame.mask.from_surface(self.display)
                display_sillhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180),
                                                              unsetcolor=(0, 0, 0, 0))
                # render sillouette 4 times, offset in each direction to create outline
                outline_thickness = 1
                for offset in [(-outline_thickness, 0), (outline_thickness, 0), 
                               (0, -outline_thickness), (0, outline_thickness)]:
                    self.display_2.blit(display_sillhouette, offset)

                if self.transistion:
                    transistion_surf = pygame.Surface(self.display.get_size())
                    # radius of circle shrinks then expands to screen size
                    pygame.draw.circle(transistion_surf, 
                                       (255, 255, 255), # colour white, but will be set to transparent
                                       (self.display.get_width() // 2,
                                        self.display.get_height() // 2), 
                                       (30 - abs(self.transistion)) * self.display.get_width() // 30) # radius
                    transistion_surf.set_colorkey((255, 255, 255)) # set white to transparent
                    self.display.blit(transistion_surf, (0, 0))
                
                # render display back on top of sillhouette
                self.display_2.blit(self.display, (0, 0))
                
                # random shake in x, y from 0 pixels up to screenshake value
                screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2,
                                      random.random() * self.screenshake - self.screenshake / 2)
                
                self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), 
                                 screenshake_offset)
            
            elif not self.active:
                self.screen.fill("springgreen3")
                
                intro_img = self.assets['startscreen']
                intro_img_rect = intro_img.get_rect()
                intro_img_rect.center = (self.screen.get_width() // 2, 
                                         self.screen.get_height() // 2)
                self.screen.blit(intro_img, intro_img_rect)
                
                title_large_text_surf = self.large_font.render("Badger Game", False, (64,64,64))
                title_large_text_rect = title_large_text_surf.get_rect(center=(intro_img_rect.centerx,
                                                                               intro_img_rect.bottom + 40))
                self.screen.blit(title_large_text_surf, title_large_text_rect)
                
                title_small_text_surf = self.small_font.render("(Click to play)", False, (64,64,64))
                title_small_text_rect = title_small_text_surf.get_rect(center=(title_large_text_rect.centerx,
                                                                               title_large_text_rect.bottom + 40))
                self.screen.blit(title_small_text_surf, title_small_text_rect)

                
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.QUIT
                    sys.exit()
                    
                # click on badger icon to play the game
                if not self.active:
                    if event.type == pygame.MOUSEBUTTONUP:
                        if intro_img_rect.collidepoint(event.pos):
                            self.active = True

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.sfx['walk'].play()
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT:
                        self.sfx['walk'].play()
                        self.movement[1] = True
                    if event.key == pygame.K_UP:
                        self.movement[2] = True
                    if event.key == pygame.K_DOWN:
                        self.movement[3] = True
                    if event.key == pygame.K_SPACE:
                        if self.player.jump():
                            #if self.player.air_time == 0: # TODO: fix double jump sound
                            self.sfx['jump'].play() # default = play only once
                    if event.key == pygame.K_x:
                        self.player.dash()
                    if event.key == pygame.K_d:
                        self.player.digging = True
                
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.sfx['walk'].stop()
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT:
                        self.sfx['walk'].stop()
                        self.movement[1] = False
                    if event.key == pygame.K_UP:
                        self.movement[2] = False
                    if event.key == pygame.K_DOWN:
                        self.movement[3] = False                    
                    if event.key == pygame.K_d:
                        self.player.digging = False
            
            pygame.display.update()
            self.clock.tick(self.fps)

#     # intro screen surfaces to display

#     dead_text_surf = self.title_font.render("You Died!", False, (64,64,64))
#     dead_text_rect = dead_text_surf.get_rect(midbottom=(int(self.width/2), self.height-100))
#     start_text_surf = self.stats_font.render("(Press space to play)", False, (64,64,64))
#     start_text_rect = start_text_surf.get_rect(midbottom=(int(self.width/2), self.height-50))
#     restart_text_surf = self.stats_font.render("(Press space to play again)", False, (64,64,64))
#     restart_text_rect = restart_text_surf.get_rect(midbottom=(int(self.width/2), self.height-50))

#     while True:
#         # event loop
#         for event in pygame.event.get():
#             # if event.type == pygame.MOUSEMOTION:
#             #     if player.sprite.rect.collidepoint(event.pos):
#             #         print("Hovering over badger")
#             #     for enemy in pygame.sprite.Group.sprites(enemies):
#             #         if enemy.rect.collidepoint(event.pos):
#             #             print("Hovering over enemy")
        
#             if not self.active: # start/restart game screen
#                 if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
#                     self.active = True #press space to play game 

#                     # initialise player and enemies

#                     self.start_time = int(pygame.time.get_ticks() / 1000)
            
#             elif self.active:
#                 if event.type == enemy_timer:
#                     # spawn enemies if there are n or fewer enemies already spawned
#                     if len(self.enemies) < self.max_enemies:
#                         # choose from list of types of enemy to spawn
#                         self.enemies.add(Enemy(choice(['badger'])))
                    
#                     # update timer with new random spawn time
#                     pygame.time.set_timer(enemy_timer, randint(5000,10000))
                
#         # game
#         if self.active:
#             self.screen.blit(title_text_surf, title_text_rect) # blit = block image transfer
#             self.game_time = display_time(self.start_time)

#             # # light up if player eneters this area
#             # if self.player.sprite.rect.colliderect(self.collision_area):
#             #     pygame.draw.rect(self.screen, (0,100,255), self.collision_area)
                    
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

#         # delta time for smooth movement
#         # self.delta = self.clock.tick(self.fps) * 0.001

# def update(self):
#     pygame.display.update()
#     self.clock.tick(self.fps)
    
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
