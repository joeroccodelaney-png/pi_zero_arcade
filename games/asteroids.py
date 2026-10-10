# -*- coding: utf-8 -*-
"""
Asteroids for the Mini_Player device (240x240 LCD).

States: title, play, gameover
Controls: PAD_LEFT / PAD_RIGHT rotate, BTN_A thrust, BTN_X fire,
          BTN_SELECT returns to the menu.
"""
import math
import random
import traceback

import pygame
from pygame.font import Font
from PIL import Image

FPS = 20


class Asteroids:
    BG_COLOR = (5, 5, 20)

    def __init__(self, mini_player):
        self.mini_player = mini_player
        pygame.font.init()
        self.font = Font(None, 24)
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
        self.ship = {'x': 120.0, 'y': 120.0, 'angle': -90.0, 'vx': 0.0, 'vy': 0.0}
        self.bullets = []
        self.asteroids = []
        self.invuln = 0
        self._spawn_asteroids()

    def start(self):
        self.reset()
        self.state = 'play'

    def _spawn_asteroids(self):
        self.asteroids = []
        for _ in range(4):
            self._spawn_asteroid(random.uniform(20, 220), random.uniform(20, 120), 24)

    def _spawn_asteroid(self, x, y, radius):
        self.asteroids.append({
            'x': x, 'y': y, 'radius': radius,
            'vx': random.uniform(-0.6, 0.6), 'vy': random.uniform(-0.6, 0.6),
        })

    def _update_play(self, keys, new, dt):
        if 'PAD_LEFT' in keys:
            self.ship['angle'] -= 160 * dt
        if 'PAD_RIGHT' in keys:
            self.ship['angle'] += 160 * dt
        if 'BTN_A' in keys:
            rad = math.radians(self.ship['angle'])
            self.ship['vx'] += math.cos(rad) * 90 * dt
            self.ship['vy'] += math.sin(rad) * 90 * dt
        if 'BTN_X' in new:
            rad = math.radians(self.ship['angle'])
            self.bullets.append([self.ship['x'], self.ship['y'],
                                 math.cos(rad) * 180, math.sin(rad) * 180, 60])

        self.ship['x'] = (self.ship['x'] + self.ship['vx'] * dt) % 240
        self.ship['y'] = (self.ship['y'] + self.ship['vy'] * dt) % 240
        self.ship['vx'] *= 0.995
        self.ship['vy'] *= 0.995
        if self.invuln > 0:
            self.invuln -= 1

        for a in self.asteroids:
            a['x'] = (a['x'] + a['vx']) % 240
            a['y'] = (a['y'] + a['vy']) % 240

        for b in self.bullets:
            b[0] = (b[0] + b[2] * dt) % 240
            b[1] = (b[1] + b[3] * dt) % 240
            b[4] -= 1

        for b in list(self.bullets):
            if b[4] <= 0:
                if b in self.bullets:
                    self.bullets.remove(b)
                continue
            for a in list(self.asteroids):
                if math.hypot(b[0] - a['x'], b[1] - a['y']) < a['radius']:
                    if b in self.bullets:
                        self.bullets.remove(b)
                    self.asteroids.remove(a)
                    self.score += 10
                    if a['radius'] > 10:
                        self._spawn_asteroid(a['x'], a['y'], a['radius'] / 2)
                        self._spawn_asteroid(a['x'], a['y'], a['radius'] / 2)
                    break

        if self.invuln == 0:
            for a in self.asteroids:
                if math.hypot(self.ship['x'] - a['x'], self.ship['y'] - a['y']) < a['radius'] + 8:
                    self.lives -= 1
                    if self.lives <= 0:
                        self.state = 'gameover'
                    else:
                        self.ship['x'], self.ship['y'] = 120.0, 120.0
                        self.ship['vx'] = self.ship['vy'] = 0.0
                        self.invuln = FPS * 2
                    break

    def _draw_ship(self):
        if self.invuln > 0 and self.invuln % 6 < 3:
            return
        rad = math.radians(self.ship['angle'])
        points = [
            (self.ship['x'] + math.cos(rad) * 12, self.ship['y'] + math.sin(rad) * 12),
            (self.ship['x'] + math.cos(rad + 2.5) * 8, self.ship['y'] + math.sin(rad + 2.5) * 8),
            (self.ship['x'] + math.cos(rad - 2.5) * 8, self.ship['y'] + math.sin(rad - 2.5) * 8),
        ]
        pygame.draw.polygon(self.screen, (120, 220, 120), points)

    def _draw_play(self):
        for a in self.asteroids:
            pygame.draw.circle(self.screen, (200, 200, 200),
                               (int(a['x']), int(a['y'])), int(a['radius']), 1)
        for b in self.bullets:
            pygame.draw.circle(self.screen, (255, 120, 120), (int(b[0]), int(b[1])), 2)
        self._draw_ship()
        self._text(self.font, f"Score {self.score}", (120, 16))
        self._text(self.font, f"Lives {self.lives}", (200, 16), (255, 120, 120))

    def _text(self, font, msg, center, color=(255, 255, 255)):
        surf = font.render(msg, True, color)
        self.screen.blit(surf, surf.get_rect(center=center))

    def _draw(self):
        self.screen.fill(self.BG_COLOR)
        if self.state == 'title':
            self._text(self.big_font, "ASTEROIDS", (120, 90), (120, 220, 120))
            self._text(self.font, "A = thrust  X = fire", (120, 130), (170, 170, 170))
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
