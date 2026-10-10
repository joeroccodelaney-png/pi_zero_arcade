# -*- coding: utf-8 -*-
"""
Frogger for the Mini_Player device (240x240 LCD).

States: title, play, won, lost
Controls: PAD_UP / PAD_DOWN / PAD_LEFT / PAD_RIGHT hop one cell at a time,
          BTN_A starts / plays again, BTN_SELECT returns to the menu.

The player character is the crab sprite (images/crab80x62.png). Hop from the
bottom row to the top goal row while dodging the traffic. There are three
levels; each crossing advances a level and speeds up the cars a little. Clear
all three levels to win; three lives, lost on any collision.
"""
import os
import random
import traceback

import pygame
from pygame.font import Font
from PIL import Image

FPS = 20

COLS = 10
CELL_W = 24
LANE_H = 24
TOP = 36                 # score bar height
ROWS = 8                 # lane 0 (top) = goal, lane 7 (bottom) = start

MAX_LEVEL = 3
LIVES = 3

# Scaled size of the crab sprite (source image is 80x62).
CRAB_W = 24
CRAB_H = 19


class FroggerGame:
    BG_COLOR = (5, 25, 15)

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
        self.crab_img = self._load_crab()
        self.reset()

    def _load_crab(self):
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, "..", "images", "crab80x62.png")
        im = Image.open(path).convert("RGBA").resize((CRAB_W, CRAB_H), Image.LANCZOS)
        return pygame.image.frombuffer(im.tobytes(), im.size, "RGBA")

    #===== Lane geometry =====
    def _cell_rect(self, col, row):
        return pygame.Rect(col * CELL_W, TOP + row * LANE_H, CELL_W, LANE_H)

    def _crab_center(self):
        rect = self._cell_rect(self.col, self.row)
        return (rect.centerx, rect.centery)

    #===== Game setup =====
    def reset(self):
        self.state = 'title'
        self.level = 1
        self.lives = LIVES
        self.col = COLS // 2
        self.row = ROWS - 1            # bottom row
        self.cars = self._make_cars()

    def start(self):
        self.reset()
        self.state = 'play'

    def _make_cars(self):
        # Six traffic lanes (rows 1..6), each with its own direction and speed.
        lanes = [
            (1, 30, 1),    # (row, speed px/s, direction)
            (2, -35, -1),
            (3, 40, 1),
            (4, -30, -1),
            (5, 45, 1),
            (6, -40, -1),
        ]
        cars = []
        for row, speed, direction in lanes:
            for i in range(2):
                x = random.uniform(0, 240)
                cars.append({
                    'row': row,
                    'x': x,
                    'speed': speed,
                    'dir': direction,
                    'w': 34,
                    'h': LANE_H - 6,
                    'color': (200, 80, 80) if direction > 0 else (90, 150, 220),
                })
        return cars

    def _speed_multiplier(self):
        # Level 1 = base speed, each level ~25% faster.
        return 1 + 0.25 * (self.level - 1)

    #===== Per-frame update. Returns False to leave the game =====
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
        elif self.state in ('won', 'lost'):
            if 'BTN_A' in new:
                self.start()
        return True

    def _hop(self, dcol, drow):
        self.col = max(0, min(COLS - 1, self.col + dcol))
        self.row = max(0, min(ROWS - 1, self.row + drow))

    def _update_play(self, keys, new, dt):
        # Discrete hops on fresh presses only.
        if 'PAD_UP' in new:
            self._hop(0, -1)
        if 'PAD_DOWN' in new:
            self._hop(0, 1)
        if 'PAD_LEFT' in new:
            self._hop(-1, 0)
        if 'PAD_RIGHT' in new:
            self._hop(1, 0)

        # Move cars.
        mult = self._speed_multiplier()
        for car in self.cars:
            car['x'] += car['speed'] * mult * dt
            # Wrap around the playfield.
            span = 240 + car['w']
            car['x'] %= span
            car['x'] -= car['w']

        # Reached the goal row?
        if self.row == 0:
            if self.level >= MAX_LEVEL:
                self.state = 'won'
                return
            self.level += 1
            self.row = ROWS - 1
            self.col = COLS // 2
            return

        # Collision with a car in the same lane.
        crab = self._cell_rect(self.col, self.row)
        crab.inflate_ip(-6, -6)
        for car in self.cars:
            if car['row'] != self.row:
                continue
            car_rect = pygame.Rect(int(car['x']), TOP + car['row'] * LANE_H + 3,
                                   car['w'], car['h'])
            if crab.colliderect(car_rect):
                self._hit()
                return

    def _hit(self):
        self.lives -= 1
        if self.lives <= 0:
            self.state = 'lost'
        else:
            self.row = ROWS - 1
            self.col = COLS // 2

    #===== Drawing =====
    def _text(self, font, msg, center, color=(255, 255, 255)):
        surf = font.render(msg, True, color)
        self.screen.blit(surf, surf.get_rect(center=center))

    def _draw_play(self):
        # Score bar.
        self._text(self.font, f"Level {self.level}/{MAX_LEVEL}", (72, 12))
        self._text(self.font, f"Lives {self.lives}", (190, 12), (255, 120, 120))

        # Goal lane (top) and start lane (bottom).
        pygame.draw.rect(self.screen, (0, 80, 0), (0, TOP, 240, LANE_H))
        pygame.draw.rect(self.screen, (0, 60, 0), (0, TOP + (ROWS - 1) * LANE_H, 240, LANE_H))

        # Cars.
        for car in self.cars:
            pygame.draw.rect(self.screen, car['color'],
                             (int(car['x']), TOP + car['row'] * LANE_H + 3, car['w'], car['h']))

        # Crab.
        cx, cy = self._crab_center()
        rect = self.crab_img.get_rect(center=(cx, cy))
        self.screen.blit(self.crab_img, rect)

    def _draw(self):
        self.screen.fill(self.BG_COLOR)
        if self.state == 'title':
            self._text(self.big_font, "FROGGER", (120, 90), (120, 220, 120))
            self._text(self.font, "3 levels, hop to top", (120, 128), (170, 170, 170))
            self._text(self.font, "A = start", (120, 152))
            self._text(self.font, "SELECT = menu", (120, 175), (170, 170, 170))
            return
        self._draw_play()
        if self.state in ('won', 'lost'):
            pygame.draw.rect(self.screen, (0, 0, 0), (20, 80, 200, 100))
            msg, color = (("YOU WON!", (255, 255, 0)) if self.state == 'won'
                          else ("GAME OVER", (255, 80, 80)))
            self._text(self.big_font, msg, (120, 105), color)
            self._text(self.font, f"Level {self.level}/{MAX_LEVEL}", (120, 135))
            self._text(self.font, "A = play again", (120, 156))
            self._text(self.font, "SELECT = menu", (120, 174), (170, 170, 170))

    #===== Push the frame to the LCD =====
    def _show(self):
        img = Image.frombytes("RGB", (240, 240),
                              pygame.image.tostring(self.screen, "RGB"))
        self.mini_player.device.display(img)

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
