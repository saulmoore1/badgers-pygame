import math
import pygame

class Spark:
    def __init__(self, pos, angle, speed):
        self.pos = list(pos)
        self.angle = angle
        self.speed = speed
        # angle + speed = polar coords for the velocity vector
        
    def update(self):
        self.pos[0] += math.cos(self.angle) * self.speed # x
        self.pos[1] += math.sin(self.angle) * self.speed # y
        
        self.speed = max(0, self.speed - 0.1)
        return not self.speed
    
    def render(self, surf, offset=(0, 0)):
        # create a polygon
        render_points = [
            (self.pos[0] + math.cos(self.angle) * self.speed * 3 - offset[0], # *3 for diamond
             self.pos[1] + math.sin(self.angle) * self.speed * 3 - offset[1]),
            (self.pos[0] + math.cos(self.angle + math.pi * 0.5) * self.speed * 0.5 - offset[0], # *0.5 for diamond
             self.pos[1] + math.sin(self.angle + math.pi * 0.5) * self.speed * 0.5 - offset[1]),
            (self.pos[0] + math.cos(self.angle + math.pi) * self.speed * 3 - offset[0], # *3 for diamond
             self.pos[1] + math.sin(self.angle + math.pi) * self.speed * 3 - offset[1]),
            (self.pos[0] + math.cos(self.angle - math.pi * 0.5) * self.speed * 0.5 - offset[0], # *0.5 for diamond
             self.pos[1] + math.sin(self.angle - math.pi * 0.5) * self.speed * 0.5 - offset[1])
            ]
        
        # if no width is specified, pygame will fill in the polygon
        pygame.draw.polygon(surf, (255, 255, 255), render_points) # colour=white
        
