# -*- coding: utf-8 -*-
"""
Whack-a-Mole for the Mini_Player device (240x240 LCD).

States: title, play, won
Controls: PAD_LEFT / PAD_RIGHT / PAD_UP / PAD_DOWN move the hammer cursor,
          BTN_X whacks, BTN_A starts / plays again, BTN_SELECT returns to menu.

A single mole pops up from a random hole for a short time. Whack it to score.
The game lasts 30 seconds; when time runs out the final score is shown.
"""
import random
import traceback

import pygame
from pygame.font import Font
from PIL import Image

FPS = 20
COLS = 3
ROWS = 3
CELL = 64
ORIGIN_X = 56
ORIGIN_Y = 56
HOLE_R = 22
GAME_TIME = 30.0
MOLE_UP_TIME = 0.9      # seconds a mole stays up
MOLE_HIDE_TIME = 0.5    # seconds between moles


class WhackAMole:
    BG_COLOR = (16, 16, 40)

    def __init__(self, mini_player):
        self.mini_player = mini_player
        pygame.font.init()
        self.font = Font(None, 22)
        self.big_font = Font(None, 40)
        self.screen = pygame.Surface((mini_player.WIDTH, mini_player.HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.released = False      # ignore buttons still held from the menu
        self.prev_keys = set()     # edge detection, kept OUTSIDE the loop
        self.reset()

    def _hole_center(self, idx):
        col = idx % COLS
        row = idx // COLS
        return (ORIGIN_X + col * CELL, ORIGIN_Y + row * CELL)

    def reset(self):
        self.state = 'title'
        self.score = 0
        self.cursor = 4            # center hole
        self.mole = None           # hole index where a mole is up, or None
        self.mole_timer = 0.0
        self.game_time = GAME_TIME

    def start(self):
        self.reset()
        self.state = 'play'
        self.mole = random.randrange(COLS * ROWS)
        self.mole_timer = MOLE_UP_TIME

    def _update_play(self, keys, new, dt):
        # Grid cursor movement (one step per fresh press)
        col = self.cursor % COLS
        row = self.cursor // COLS
        if 'PAD_LEFT' in new and col > 0:
            col -= 1
        if 'PAD_RIGHT' in new and col < COLS - 1:
            col += 1
        if 'PAD_UP' in new and row > 0:
            row -= 1
        if 'PAD_DOWN' in new and row < ROWS - 1:
            row += 1
        self.cursor = row * COLS + col

        # Whack
        if 'BTN_X' in new:
            if self.mole is not None and self.mole == self.cursor:
                self.score += 1
                self.mole = None
                self.mole_timer = MOLE_HIDE_TIME

        # Mole lifecycle
        self.mole_timer -= dt
        if self.mole is not None:
            if self.mole_timer <= 0:
                self.mole = None
                self.mole_timer = MOLE_HIDE_TIME
        else:
            if self.mole_timer <= 0:
                self.mole = random.randrange(COLS * ROWS)
                self.mole_timer = MOLE_UP_TIME

        # Game clock
        self.game_time -= dt
        if self.game_time <= 0:
            self.game_time = 0
            self.state = 'won'

    def _text(self, font, msg, center, color=(255, 255, 255)):
        surf = font.render(msg, True, color)
        self.screen.blit(surf, surf.get_rect(center=center))

    def _draw(self):
        self.screen.fill(self.BG_COLOR)
        if self.state == 'title':
            self._text(self.big_font, "WHACK-A-MOLE", (120, 90), (255, 220, 90))
            self._text(self.font, "Move: D-pad", (120, 150))
            self._text(self.font, "Whack: X", (120, 172), (255, 200, 120))
            self._text(self.font, "A = start", (120, 196))
            self._text(self.font, "SELECT = menu", (120, 216), (170, 170, 170))
            return

        # HUD
        self._text(self.font, "Score " + str(self.score), (58, 18))
        t = int(self.game_time + 0.999)
        self._text(self.font, "Time " + str(t), (182, 18), (120, 220, 255))

        # Holes, cursor highlight, mole
        for i in range(COLS * ROWS):
            x, y = self._hole_center(i)
            pygame.draw.ellipse(self.screen, (70, 45, 20),
                                (x - HOLE_R, y - HOLE_R // 2, HOLE_R * 2, HOLE_R))
            if i == self.cursor:
                pygame.draw.circle(self.screen, (255, 220, 90), (x, y), HOLE_R + 6, 2)
        if self.mole is not None:
            x, y = self._hole_center(self.mole)
            pygame.draw.circle(self.screen, (150, 90, 40), (x, y - 8), 16)

        # Footer hint
        self._text(self.font, "X = whack", (120, 226), (170, 170, 170))

        if self.state == 'won':
            pygame.draw.rect(self.screen, (0, 0, 0), (20, 84, 200, 96))
            self._text(self.big_font, "TIME'S UP!", (120, 112), (255, 220, 90))
            self._text(self.font, "Score " + str(self.score), (120, 142))
            self._text(self.font, "A = play again", (120, 162))
            self._text(self.font, "SELECT = menu", (120, 178), (170, 170, 170))

    def _show(self):
        img = Image.frombytes("RGB", (240, 240),
                              pygame.image.tostring(self.screen, "RGB"))
        self.mini_player.device.display(img)

    def update(self, keys, dt):
        keys = set(keys)
        new = keys - self.prev_keys
        self.prev_keys = keys

        # Ignore buttons held from the menu.
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
        elif self.state == 'won':
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

