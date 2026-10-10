# -*- coding: utf-8 -*-
"""
Flappy for the Mini_Player device (240x240 LCD).

States: title, play, lost
Controls: BTN_A (or PAD_UP) flaps the bird, BTN_SELECT returns to the menu,
          BTN_A on title starts, BTN_A on game-over restarts.

The player character is the bee sprite (images/bee_smile50x51.png), scaled to
fit the play area and rendered with per-pixel alpha.
"""
import os
import random
import traceback

import pygame
from pygame.font import Font
from PIL import Image

FPS = 20

BIRD_X = 60
GRAVITY = 500.0
FLAP_VELOCITY = -160.0
PIPE_WIDTH = 40
PIPE_GAP = 90
PIPE_SPEED = 60.0

# Scaled size of the bee sprite (source image is 50x51).
BIRD_W = 26
BIRD_H = 27
BIRD_HW = BIRD_W / 2.0
BIRD_HH = BIRD_H / 2.0


class FlappyGame:
    BG_COLOR = (20, 60, 90)

    def __init__(self, mini_player):
        self.mini_player = mini_player
        pygame.font.init()
        self.font = Font(None, 26)
        self.big_font = Font(None, 40)
        self.screen = pygame.Surface((mini_player.WIDTH, mini_player.HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.released = False
        self.prev_keys = set()
        self.bird_img = self._load_bird()
        self.reset()

    def _load_bird(self):
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, "..", "images", "bee_smile50x51.png")
        im = Image.open(path).convert("RGBA").resize((BIRD_W, BIRD_H), Image.LANCZOS)
        return pygame.image.frombuffer(im.tobytes(), im.size, "RGBA")

    def reset(self):
        self.state = 'title'
        self.bird_y = float(self.mini_player.HEIGHT // 2)
        self.velocity = 0.0
        self.score = 0
        self.pipes = []
        self.pipe_timer = 0.0

    def start(self):
        self.reset()
        self.state = 'play'

    def _spawn_pipe(self):
        gap_y = random.randint(70, self.mini_player.HEIGHT - 70)
        self.pipes.append([float(self.mini_player.WIDTH), gap_y, False])

    def _update_play(self, keys, new, dt):
        if 'BTN_A' in new or 'PAD_UP' in new:
            self.velocity = FLAP_VELOCITY

        self.velocity += GRAVITY * dt
        self.bird_y += self.velocity * dt

        self.pipe_timer += dt
        if self.pipe_timer >= 2.6:
            self.pipe_timer = 0.0
            self._spawn_pipe()
        for pipe in self.pipes:
            pipe[0] -= PIPE_SPEED * dt

        for pipe in self.pipes:
            if not pipe[2] and pipe[0] + PIPE_WIDTH < BIRD_X - BIRD_HW:
                pipe[2] = True
                self.score += 1
        self.pipes = [p for p in self.pipes if p[0] + PIPE_WIDTH > -10]

        if self.bird_y - BIRD_HH < 0:
            self.bird_y = float(BIRD_HH)
            self.velocity = 0.0
        if self.bird_y + BIRD_HH > self.mini_player.HEIGHT:
            self.state = 'lost'
            return
        for px, gap_y, _ in self.pipes:
            if px < BIRD_X + BIRD_HW and px + PIPE_WIDTH > BIRD_X - BIRD_HW:
                if (self.bird_y - BIRD_HH < gap_y - PIPE_GAP / 2 or
                        self.bird_y + BIRD_HH > gap_y + PIPE_GAP / 2):
                    self.state = 'lost'
                    return

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
            if 'BTN_A' in new or 'PAD_UP' in new:
                self.start()
        elif self.state == 'play':
            self._update_play(keys, new, dt)
        elif self.state == 'lost':
            if 'BTN_A' in new:
                self.start()
        return True

    def _text(self, font, msg, center, color=(255, 255, 255)):
        surf = font.render(msg, True, color)
        self.screen.blit(surf, surf.get_rect(center=center))

    def _draw_play(self):
        for px, gap_y, _ in self.pipes:
            pygame.draw.rect(self.screen, (0, 180, 80),
                             (int(px), 0, PIPE_WIDTH, int(gap_y - PIPE_GAP / 2)))
            pygame.draw.rect(self.screen, (0, 180, 80),
                             (int(px), int(gap_y + PIPE_GAP / 2), PIPE_WIDTH,
                              self.mini_player.HEIGHT - int(gap_y + PIPE_GAP / 2)))
        rect = self.bird_img.get_rect(center=(BIRD_X, int(self.bird_y)))
        self.screen.blit(self.bird_img, rect)
        self._text(self.font, str(self.score), (120, 20))

    def _draw(self):
        self.screen.fill(self.BG_COLOR)
        if self.state == 'title':
            self._text(self.big_font, "FLAPPY", (120, 90), (255, 220, 40))
            self._text(self.font, "A = flap / start", (120, 130))
            self._text(self.font, "SELECT = menu", (120, 155), (170, 170, 170))
            return
        self._draw_play()
        if self.state == 'lost':
            pygame.draw.rect(self.screen, (0, 0, 0), (20, 80, 200, 100))
            self._text(self.big_font, "GAME OVER", (120, 105), (255, 80, 80))
            self._text(self.font, f"Score {self.score}", (120, 135))
            self._text(self.font, "A = play again", (120, 156))
            self._text(self.font, "SELECT = menu", (120, 174), (170, 170, 170))

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
