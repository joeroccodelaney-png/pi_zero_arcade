# -*- coding: utf-8 -*-
"""
Blocks (falling-block puzzle) for the Mini_Player device (240x240 LCD).

States: title, play, gameover
Controls: PAD_LEFT / PAD_RIGHT move, PAD_DOWN soft drop, BTN_A rotate,
          BTN_SELECT returns to the menu.
"""
import random
import traceback

import pygame
from pygame.font import Font
from PIL import Image

FPS = 20
COLS = 10
ROWS = 18
CELL = 12
BOARD_X = 8
BOARD_Y = 22

PIECES = [
    [(0, 0), (1, 0), (0, 1), (1, 1)],
    [(0, 0), (1, 0), (2, 0), (3, 0)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 1), (1, 1), (2, 1), (2, 0)],
    [(0, 0), (0, 1), (1, 1), (1, 2)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],
    [(0, 2), (1, 2), (1, 1), (1, 0)],
]

DROP_INTERVAL = 0.6


class Blocks:
    BG_COLOR = (10, 10, 30)

    def __init__(self, mini_player):
        self.mini_player = mini_player
        pygame.font.init()
        self.font = Font(None, 22)
        self.big_font = Font(None, 40)
        self.screen = pygame.Surface((mini_player.WIDTH, mini_player.HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.released = False
        self.prev_keys = set()
        self.reset()

    def reset(self):
        self.state = 'title'
        self.grid = [[0] * COLS for _ in range(ROWS)]
        self.score = 0
        self.piece = None
        self.piece_x = 0
        self.piece_y = 0
        self.drop_timer = 0.0
        self._new_piece()

    def start(self):
        self.reset()
        self.state = 'play'

    def _new_piece(self):
        self.piece = random.choice(PIECES)
        self.piece_x = COLS // 2 - 1
        self.piece_y = 0
        self.drop_timer = 0.0
        if self._collides(self.piece_x, self.piece_y, self.piece):
            self.state = 'gameover'

    def _collides(self, px, py, piece):
        for dx, dy in piece:
            x, y = px + dx, py + dy
            if x < 0 or x >= COLS or y >= ROWS:
                return True
            if y >= 0 and self.grid[y][x]:
                return True
        return False

    def _lock(self):
        for dx, dy in self.piece:
            x, y = self.piece_x + dx, self.piece_y + dy
            if 0 <= y < ROWS and 0 <= x < COLS:
                self.grid[y][x] = 1
        cleared = 0
        new_grid = []
        for row in self.grid:
            if all(row):
                cleared += 1
            else:
                new_grid.append(row)
        while len(new_grid) < ROWS:
            new_grid.insert(0, [0] * COLS)
        self.grid = new_grid
        self.score += cleared * 10
        self._new_piece()

    def _rotate(self):
        rotated = [(-dy, dx) for dx, dy in self.piece]
        if not self._collides(self.piece_x, self.piece_y, rotated):
            self.piece = rotated

    def _update_play(self, keys, new, dt):
        if 'PAD_LEFT' in new and not self._collides(self.piece_x - 1, self.piece_y, self.piece):
            self.piece_x -= 1
        if 'PAD_RIGHT' in new and not self._collides(self.piece_x + 1, self.piece_y, self.piece):
            self.piece_x += 1
        if 'PAD_DOWN' in new and not self._collides(self.piece_x, self.piece_y + 1, self.piece):
            self.piece_y += 1
            self.score += 1
        if 'BTN_A' in new:
            self._rotate()

        self.drop_timer += dt
        if self.drop_timer >= DROP_INTERVAL:
            self.drop_timer -= DROP_INTERVAL
            if not self._collides(self.piece_x, self.piece_y + 1, self.piece):
                self.piece_y += 1
            else:
                self._lock()

    def _draw_cell(self, x, y, color):
        pygame.draw.rect(self.screen, color,
                         (BOARD_X + x * CELL, BOARD_Y + y * CELL, CELL - 1, CELL - 1))

    def _draw_play(self):
        pygame.draw.rect(self.screen, (40, 40, 70),
                         (BOARD_X - 2, BOARD_Y - 2, COLS * CELL + 4, ROWS * CELL + 4), 2)
        for y in range(ROWS):
            for x in range(COLS):
                if self.grid[y][x]:
                    self._draw_cell(x, y, (90, 90, 180))
        for dx, dy in self.piece:
            self._draw_cell(self.piece_x + dx, self.piece_y + dy, (220, 180, 60))
        self._text(self.font, f"Score {self.score}", (120, 12))

    def _text(self, font, msg, center, color=(255, 255, 255)):
        surf = font.render(msg, True, color)
        self.screen.blit(surf, surf.get_rect(center=center))

    def _draw(self):
        self.screen.fill(self.BG_COLOR)
        if self.state == 'title':
            self._text(self.big_font, "BLOCKS", (120, 90), (220, 180, 60))
            self._text(self.font, "A = rotate", (120, 130), (170, 170, 170))
            self._text(self.font, "A = start", (120, 155))
            self._text(self.font, "SELECT = menu", (120, 178), (170, 170, 170))
            return
        self._draw_play()
        if self.state == 'gameover':
            pygame.draw.rect(self.screen, (0, 0, 0), (20, 80, 200, 100))
            self._text(self.big_font, "GAME OVER", (120, 105), (255, 80, 80))
            self._text(self.font, f"Score {self.score}", (120, 135))
            self._text(self.font, "A = play again", (120, 156))
            self._text(self.font, "SELECT = menu", (120, 174), (170, 170, 170))

    def _show(self):
        img = Image.frombytes("RGB", (240, 240),
                              pygame.image.tostring(self.screen, "RGB"))
        self.mini_player.device.display(img)

    def update(self, keys, dt):
        keys = set(keys)
        new = keys - self.prev_keys
        self.prev_keys = keys
        if not self.released:
            if not keys:
                self.released = True
            return True
        if 'BTN_SELECT' in new:
            return False
        if self.state == 'title':
            if 'BTN_A' in new:
                self.start()
        elif self.state == 'play':
            self._update_play(keys, new, dt)
        elif self.state == 'gameover':
            if 'BTN_A' in new:
                self.start()
        return True

    def run(self):
        try:
            self.running = True
            while self.running:
                dt = min(self.clock.tick(FPS) / 1000.0, 0.1)
                keys = self.mini_player.pressed()
                if not self.update(keys, dt):
                    self.running = False
                self._draw()
                self._show()
        except Exception:
            print("Error playing game:")
            traceback.print_exc()
        finally:
            pygame.quit()
        return False
