# -*- coding: utf-8 -*-
"""
Space Invader for the Mini_Player device (240x240 LCD).

States: title, play, gameover
Controls: PAD_LEFT / PAD_RIGHT move, BTN_X fire, BTN_SELECT returns to menu.
"""
import random
import traceback

import pygame
from pygame.font import Font
from PIL import Image

FPS = 20
INVADER_COLS = 6
INVADER_ROWS = 4


class Invaders:
    BG_COLOR = (5, 5, 15)

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
        self.score = 0
        self.lives = 3
        self.player_x = 100
        self.shots = []
        self.bombs = []
        self.invaders = [[(40 + j * 28, 30 + i * 22, True) for j in range(INVADER_COLS)]
                         for i in range(INVADER_ROWS)]
        self.dir = 1
        self.move_timer = 0.0
        self.shoot_cooldown = 0
        self.bomb_timer = 0

    def start(self):
        self.reset()
        self.state = 'play'

    def _lose_life(self):
        self.lives -= 1
        if self.lives <= 0:
            self.state = 'gameover'

    def _update_play(self, keys, new, dt):
        if 'PAD_LEFT' in keys:
            self.player_x = max(0, self.player_x - 3)
        if 'PAD_RIGHT' in keys:
            self.player_x = min(200, self.player_x + 3)
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if 'BTN_X' in new and self.shoot_cooldown == 0:
            self.shots.append([self.player_x + 18, 210])
            self.shoot_cooldown = 8

        for s in list(self.shots):
            s[1] -= 6
            if s[1] < 0:
                self.shots.remove(s)

        self.move_timer += dt
        if self.move_timer >= 0.5:
            self.move_timer = 0.0
            edge = False
            for row in self.invaders:
                for inv in row:
                    if inv[2]:
                        if (self.dir > 0 and inv[0] + 20 >= 240) or (self.dir < 0 and inv[0] <= 0):
                            edge = True
            for row in self.invaders:
                for inv in row:
                    inv[0] += self.dir * 8
                    if edge:
                        inv[1] += 8
            if edge:
                self.dir *= -1

        for s in list(self.shots):
            for row in self.invaders:
                hit = False
                for inv in row:
                    if inv[2] and inv[0] <= s[0] <= inv[0] + 20 and inv[1] <= s[1] <= inv[1] + 12:
                        inv[2] = False
                        self.score += 10
                        hit = True
                        break
                if hit:
                    self.shots.remove(s)
                    break

        self.bomb_timer += 1
        if self.bomb_timer >= 40:
            self.bomb_timer = 0
            alive = [inv for row in self.invaders for inv in row if inv[2]]
            if alive:
                shooter = random.choice(alive)
                self.bombs.append([shooter[0] + 10, shooter[1] + 6])

        for b in list(self.bombs):
            b[1] += 4
            if b[1] > 240:
                self.bombs.remove(b)
            elif self.player_x <= b[0] <= self.player_x + 40 and 210 <= b[1] <= 226:
                self.bombs.remove(b)
                self._lose_life()

        if not any(inv[2] for row in self.invaders for inv in row):
            self.score += 50
            self.invaders = [[(40 + j * 28, 30 + i * 22, True) for j in range(INVADER_COLS)]
                             for i in range(INVADER_ROWS)]

        for row in self.invaders:
            for inv in row:
                if inv[2] and inv[1] >= 190:
                    self.state = 'gameover'

    def _draw_play(self):
        for row in self.invaders:
            for inv in row:
                if inv[2]:
                    pygame.draw.rect(self.screen, (255, 90, 90), (inv[0], inv[1], 20, 12))
        pygame.draw.rect(self.screen, (90, 200, 255), (self.player_x, 210, 40, 16))
        for s in self.shots:
            pygame.draw.rect(self.screen, (255, 255, 255), (s[0], s[1], 4, 8))
        for b in self.bombs:
            pygame.draw.rect(self.screen, (255, 200, 60), (b[0], b[1], 4, 8))
        self._text(self.font, f"Score {self.score}", (120, 12))
        self._text(self.font, f"Lives {self.lives}", (200, 12), (255, 120, 120))

    def _text(self, font, msg, center, color=(255, 255, 255)):
        surf = font.render(msg, True, color)
        self.screen.blit(surf, surf.get_rect(center=center))

    def _draw(self):
        self.screen.fill(self.BG_COLOR)
        if self.state == 'title':
            self._text(self.big_font, "INVADERS", (120, 90), (90, 200, 255))
            self._text(self.font, "X = fire", (120, 130), (170, 170, 170))
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
