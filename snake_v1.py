'''
Response Number 2 from qwen2.5-coder:3b

'''

import pygame
import random
import math
from PIL import Image

class SnakeGame:
    """
    SnakeGame class for a simple 2D snake game with a 240x240 screen.
    States: title, play, won, lost, serve
    Fields: mini_player, screen, font, clock, snake, food, score, move_timer, prev_keys
    """

    def __init__(self, mini_player):
        self.mini_player = mini_player
        self.screen = pygame.Surface((240, 240))
        pygame.font.init()
        self.font = pygame.font.Font(None, 18)
        self.clock = pygame.time.Clock()
        self.reset()
        self.prev_keys = {'BTN_A'}

    def reset(self):
        self.snake = [(10, 8), (9, 8), (8, 8)]
        self.direction = (1, 0)
        self.pending_direction = None
        self.food = None
        self.score = 0
        self.move_timer = 0
        self.state = 'title'

    def check_collision(self):
        head = self.snake[0]
        if head[0] < 0 or head[0] >= 240 or head[1] < 36 or head[1] >= 240:
            self.state = 'lost'
            return True
        for i in range(1, len(self.snake)):
            if head == self.snake[i]:
                self.state = 'lost'
                return True
        return False

    def update(self, keys, dt):
        if self.state == 'title':
            if 'BTN_SELECT' in keys:
                self.state = 'play'
                self.reset()
        elif self.state == 'play':
            if 'BTN_SELECT' in keys:
                self.state = 'won' if self.score > 0 else 'lost'
                return False
            if self.mini_player.pressed('BTN_A') and self.move_timer == 0 and 'BTN_A' not in self.prev_keys:
                self.pending_direction = (self.direction[0], self.direction[1])
            self.prev_keys = keys
            if self.pending_direction:
                self.direction = self.pending_direction
                self.pending_direction = None
            self.move_timer += dt
            if self.move_timer >= 0.15:
                self.move_timer = 0
                self.snake.insert(0, (self.snake[0][0] + self.direction[0] * 12, self.snake[0][1] +
self.direction[1] * 12))
                if self.snake[0] == self.food:
                    self.score += 1
                    self.food = None
                    while not self.food:
                        self.food = (random.randint(0, 19) * 12, random.randint(36, 239))
                else:
                    self.snake.pop()
            if self.check_collision():
                return False
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
