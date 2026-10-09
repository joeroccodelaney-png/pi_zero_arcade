import pygame
import random
import math
from PIL import Image

class SnakeGame:
    """
    SnakeGame class for a simple 2D snake game with a 240x240 screen.
    States: title, play, won, lost, serve
    Fields: mini_player, screen, font, clock, snake, food, score, move_timer
    """
    
    def __init__(self, mini_player):
        self.mini_player = mini_player
        self.screen = pygame.Surface((240, 240))
        pygame.font.init()
        self.font = pygame.font.Font(None, 18)
        self.clock = pygame.time.Clock()
        self.reset()
    
    def reset(self):
        self.snake = [(100, 100), (98, 100), (96, 100)]
        self.direction = (1, 0)
        self.pending_direction = None
        self.food = None
        self.score = 0
        self.move_timer = 0
        self.state = 'title'
    
    def update(self, keys, dt):
        if self.state == 'title':
            if 'BTN_SELECT' in keys:
                self.state = 'play'
                self.reset()
        elif self.state == 'play':
            if 'BTN_SELECT' in keys:
                self.state = 'won' if self.score > 0 else 'lost'
                return False
            if self.mini_player.pressed('BTN_A') and self.move_timer == 0:
                self.pending_direction = (self.direction[0], self.direction[1])
            if self.pending_direction:
                self.direction = self.pending_direction
                self.pending_direction = None
            self.move_timer += dt
            if self.move_timer >= 0.15:
                self.move_timer = 0
                self.snake.insert(0, (self.snake[0][0] + self.direction[0] * 12, self.snake[0][1] + self.direction[1] * 12))
                if self.snake[0] == self.food:
                    self.score += 1
                    self.food = None
                    while not self.food:
                        self.food = (random.randint(0, 19) * 12, random.randint(36, 239))
                else:
                    self.snake.pop()
            self.check_collision()
            return True
        elif self.state == 'won' or self.state == 'lost':
            return False
    
    def render(self):
        self.screen.fill((0, 0, 0))
        if self.state == 'title':
            text = self.font.render("Press A to start", True, (255, 255, 255))
            self.screen.blit(text, (40, 100))
        elif self.state == 'play':
            for x, y in self.snake:
                pygame.draw.rect(self.screen, (255, 255, 255), (x, y, 12, 12))
            if self.food:
                pygame.draw.rect(self.screen, (255, 0, 0), (self.food[0], self.food[1], 12, 12))
            text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
            self.screen.blit(text, (40, 220))
        elif self.state == 'won':
            text = self.font.render("You won!", True, (255, 255, 255))
            self.screen.blit(text, (40, 100))
        elif self.state == 'lost':
            text = self.font.render("You lost!", True, (255, 255, 255))
            self.screen.blit(text, (40, 100))
        pygame.display.flip()
    
    def run(self):
        while True:
            self.clock.tick(30)
            dt = self.clock.get_time() / 1000
            keys = self.mini_player.pressed()
            if not self.update(keys, dt):
                break
            self.render()
