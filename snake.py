# -*- coding: utf-8 -*-
"""
Snake for the Mini_Player device (240x240 LCD).

States: title, play, won, lost
Controls: D-pad steers, A starts / plays again, SELECT returns to the menu.
The playfield is a 20 x 17 grid of 12px cells under a 36px score bar.
"""
import random
import pygame
from PIL import Image


class SnakeGame:
    CELL = 12
    COLS = 20
    TOP = 36                       # pixels reserved at the top for the score bar
    ROWS = (240 - TOP) // CELL     # 17 rows -> playfield ends exactly at y=240
    MOVE_DELAY = 0.15              # seconds between snake steps
    WIN_SCORE = 15
    BG_COLOR = (10, 10, 40)
    SNAKE_COLOR = (80, 220, 120)
    HEAD_COLOR = (170, 255, 190)
    FOOD_COLOR = (230, 60, 60)
    DIRS = {"PAD_UP": (0, -1), "PAD_DOWN": (0, 1),
            "PAD_LEFT": (-1, 0), "PAD_RIGHT": (1, 0)}

    #===== Initialize the game =====#
    def __init__(self, mini_player):
        self.mini_player = mini_player
        pygame.init()
        self.screen = pygame.Surface((mini_player.WIDTH, mini_player.HEIGHT))
        self.font = pygame.font.Font(None, 26)
        self.big_font = pygame.font.Font(None, 40)
        self.clock = pygame.time.Clock()
        self.running = True
        self.released = False       # ignore input until the launch button is let go
        self.prev_keys = set()
        self.reset()

    #===== Reset to the title screen =====#
    def reset(self):
        mid_y = self.TOP + (self.ROWS // 2) * self.CELL
        self.snake = [(120, mid_y), (108, mid_y), (96, mid_y)]   # head first, on the grid
        self.direction = (1, 0)
        self.pending_direction = None
        self.score = 0
        self.move_timer = 0.0
        self.food = self._spawn_food()
        self.state = 'title'

    #===== Start a round =====#
    def start(self):
        self.reset()
        self.state = 'play'

    #===== Pick a random free grid cell for the food =====#
    def _spawn_food(self):
        free = [(c * self.CELL, self.TOP + r * self.CELL)
                for c in range(self.COLS) for r in range(self.ROWS)
                if (c * self.CELL, self.TOP + r * self.CELL) not in self.snake]
        return random.choice(free) if free else None

    #===== Turn the snake (no 180 degree reversals) =====#
    def _steer(self, keys):
        for name, d in self.DIRS.items():
            if name in keys and (d[0] + self.direction[0], d[1] + self.direction[1]) != (0, 0):
                self.pending_direction = d

    #===== Move the snake one cell =====#
    def _step(self):
        if self.pending_direction:
            self.direction = self.pending_direction
            self.pending_direction = None
        nx = self.snake[0][0] + self.direction[0] * self.CELL
        ny = self.snake[0][1] + self.direction[1] * self.CELL
        hit_wall = nx < 0 or nx >= 240 or ny < self.TOP or ny >= 240
        if hit_wall or (nx, ny) in self.snake[:-1]:
            self.state = 'lost'
            return
        self.snake.insert(0, (nx, ny))
        if (nx, ny) == self.food:
            self.score += 1
            if self.score >= self.WIN_SCORE:
                self.state = 'won'
                return
            self.food = self._spawn_food()
        else:
            self.snake.pop()

    #===== Update game state. Returns False to leave the game =====#
    def update(self, keys, dt):
        keys = set(keys)
        new = keys - self.prev_keys          # buttons pressed this frame
        self.prev_keys = keys
        if not self.released:                # a button held from the menu must not act
            if not keys:
                self.released = True
            return True
        if 'BTN_SELECT' in new:
            return False
        if self.state == 'play':
            self._steer(keys)
            self.move_timer += dt
            if self.move_timer >= self.MOVE_DELAY:
                self.move_timer -= self.MOVE_DELAY
                self._step()
        elif 'BTN_A' in new:                 # title / won / lost
            self.start()
        return True

    #===== Draw text centered on a point =====#
    def _text(self, font, msg, center, color=(255, 255, 255)):
        surf = font.render(msg, True, color)
        self.screen.blit(surf, surf.get_rect(center=center))

    #===== Draw the board =====#
    def _draw_board(self):
        c = self.CELL
        self._text(self.font, f"Score {self.score}/{self.WIN_SCORE}", (120, 17))
        pygame.draw.line(self.screen, (90, 90, 140), (0, self.TOP - 2), (240, self.TOP - 2))
        if self.food:
            pygame.draw.rect(self.screen, self.FOOD_COLOR, (self.food[0] + 1, self.food[1] + 1, c - 2, c - 2))
        for i, (x, y) in enumerate(self.snake):
            color = self.HEAD_COLOR if i == 0 else self.SNAKE_COLOR
            pygame.draw.rect(self.screen, color, (x + 1, y + 1, c - 2, c - 2))

    #===== Draw the current frame =====#
    def _draw(self):
        self.screen.fill(self.BG_COLOR)
        if self.state == 'title':
            self._text(self.big_font, "SNAKE", (120, 90), (80, 220, 120))
            self._text(self.font, "A = start", (120, 135))
            self._text(self.font, "SELECT = menu", (120, 160), (170, 170, 170))
            return
        self._draw_board()
        if self.state in ('won', 'lost'):
            pygame.draw.rect(self.screen, (0, 0, 0), (20, 80, 200, 100))
            msg, color = ("YOU WON!", (255, 255, 0)) if self.state == 'won' else ("GAME OVER", (255, 80, 80))
            self._text(self.big_font, msg, (120, 108), color)
            self._text(self.font, "A = play again", (120, 142))
            self._text(self.font, "SELECT = menu", (120, 164), (170, 170, 170))

    #===== Push the frame to the LCD =====#
    def _show(self):
        img = Image.frombytes("RGB", (240, 240), pygame.image.tostring(self.screen, "RGB"))
        self.mini_player.device.display(img)

    #===== Run the game =====#
    def run(self):
        try:
            while self.running:
                dt = min(self.clock.tick(20) / 1000.0, 0.1)
                keys = self.mini_player.pressed()
                if not self.update(keys, dt):
                    self.running = False
                    return False
                self._draw()
                self._show()
        finally:
            pygame.quit()
        return False

