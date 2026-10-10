# -*- coding: utf-8 -*-
"""
Breakout for the Mini_Player device (240x240 LCD).

States: title, play, won, lost
Controls: PAD_LEFT / PAD_RIGHT move the paddle, BTN_A starts / launches the
          ball / plays again, BTN_SELECT returns to the menu.

Aim: bounce the ball off the paddle to clear every brick at the top.
Three lives. Lose a life when the ball drops past the paddle; clear the
whole wall to win.
"""
import random
import traceback

import pygame
from pygame.font import Font
from PIL import Image

FPS = 20

BRICK_ROWS = 5
BRICK_COLS = 8
BRICK_MARGIN = 6
BRICK_GAP = 4
BRICK_HEIGHT = 12
WALL_TOP = 34            # leave room for the score line


class BreakoutGame:
    PAD_WIDTH = 40
    PAD_HEIGHT = 8
    PAD_SPEED = 130       # pixels per second
    PAD_Y = 224           # top of the paddle
    BALL_RADIUS = 4
    BALL_MAX_DX = 6.0
    LIVES = 3
    BG_COLOR = (10, 10, 40)

    def __init__(self, mini_player):
        self.mini_player = mini_player
        pygame.font.init()
        self.font = Font(None, 22)
        self.big_font = Font(None, 40)
        self.screen = pygame.Surface((mini_player.WIDTH, mini_player.HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.released = False       # ignore buttons still held from the menu
        self.prev_keys = set()
        self.reset()

    #===== Brick wall =====
    def _make_bricks(self):
        usable = self.mini_player.WIDTH - 2 * BRICK_MARGIN
        self.brick_w = (usable - (BRICK_COLS - 1) * BRICK_GAP) // BRICK_COLS
        bricks = []
        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                x = BRICK_MARGIN + col * (self.brick_w + BRICK_GAP)
                y = WALL_TOP + row * (BRICK_HEIGHT + BRICK_GAP)
                bricks.append([x, y, self.brick_w, BRICK_HEIGHT, True])
        return bricks

    #===== Game setup =====
    def reset(self):
        self.state = 'title'        # title, play, won, lost
        self.score = 0
        self.lives = self.LIVES
        self.bricks = self._make_bricks()
        self.paddle_x = (self.mini_player.WIDTH - self.PAD_WIDTH) // 2
        self._prepare_serve()

    def start(self):
        self.reset()
        self.state = 'play'

    def _prepare_serve(self):
        self.serve = True
        self.ball_dx = 0
        self.ball_dy = 0
        self._attach_ball()

    def _attach_ball(self):
        self.ball_x = self.paddle_x + self.PAD_WIDTH / 2.0
        self.ball_y = self.PAD_Y - self.BALL_RADIUS - 1

    def _launch(self):
        self.ball_dx = random.choice((-1, 1)) * random.uniform(3.0, 4.5)
        self.ball_dy = -random.uniform(4.0, 5.5)
        self.serve = False

    #===== Per-frame update. Returns False to leave the game =====
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
        elif self.state in ('won', 'lost'):
            if 'BTN_A' in new:
                self.start()
        return True

    def _update_play(self, keys, new, dt):
        #===== Paddle =====
        speed = self.PAD_SPEED * dt
        if 'PAD_LEFT' in keys:
            self.paddle_x -= speed
        if 'PAD_RIGHT' in keys:
            self.paddle_x += speed
        self.paddle_x = max(0, min(self.mini_player.WIDTH - self.PAD_WIDTH,
                                   self.paddle_x))

        if self.serve:
            self._attach_ball()
            if 'BTN_A' in new:
                self._launch()
            return

        self._move_ball()

    def _move_ball(self):
        r = self.BALL_RADIUS
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy

        #===== Walls =====
        if self.ball_x - r < 0:
            self.ball_x = r
            self.ball_dx = abs(self.ball_dx)
        elif self.ball_x + r > self.mini_player.WIDTH:
            self.ball_x = self.mini_player.WIDTH - r
            self.ball_dx = -abs(self.ball_dx)
        if self.ball_y - r < 0:
            self.ball_y = r
            self.ball_dy = abs(self.ball_dy)

        #===== Paddle =====
        ball = pygame.Rect(int(self.ball_x - r), int(self.ball_y - r), 2 * r, 2 * r)
        paddle = pygame.Rect(int(self.paddle_x), self.PAD_Y,
                             self.PAD_WIDTH, self.PAD_HEIGHT)
        if self.ball_dy > 0 and paddle.colliderect(ball):
            self.ball_y = self.PAD_Y - r
            self._bounce_off_paddle()

        #===== Bricks =====
        for brick in self.bricks:
            if brick[4] and pygame.Rect(brick[0], brick[1], brick[2], brick[3]).colliderect(ball):
                brick[4] = False
                self.score += 1
                self.ball_dy = abs(self.ball_dy)      # always bounce upward off a brick
                if not any(b[4] for b in self.bricks):
                    self.state = 'won'
                    return
                break

        #===== Missed below the paddle =====
        if self.ball_y - r > self.mini_player.HEIGHT:
            self.lives -= 1
            if self.lives <= 0:
                self.state = 'lost'
            else:
                self._prepare_serve()

    def _bounce_off_paddle(self):
        offset = (self.ball_x - (self.paddle_x + self.PAD_WIDTH / 2.0)) / (self.PAD_WIDTH / 2.0)
        offset = max(-1.0, min(1.0, offset))
        self.ball_dx = max(-self.BALL_MAX_DX, min(self.BALL_MAX_DX, offset * 5.5))
        self.ball_dy = -max(3.5, abs(self.ball_dy))
        if abs(self.ball_dx) < 1.0:
            self.ball_dx = 1.0 if offset >= 0 else -1.0

    #===== Drawing =====
    def _text(self, font, msg, center, color=(255, 255, 255)):
        surf = font.render(msg, True, color)
        self.screen.blit(surf, surf.get_rect(center=center))

    def _draw_play(self):
        self._text(self.font, f"Score {self.score}", (120, 16))
        self._text(self.font, f"Lives {self.lives}", (200, 16), (255, 120, 120))
        for brick in self.bricks:
            if brick[4]:
                pygame.draw.rect(self.screen, (220, 90, 40), brick[:4])
        pygame.draw.rect(self.screen, (255, 255, 255),
                         (int(self.paddle_x), self.PAD_Y, self.PAD_WIDTH, self.PAD_HEIGHT))
        pygame.draw.circle(self.screen, (255, 255, 255),
                           (int(self.ball_x), int(self.ball_y)), self.BALL_RADIUS)

    def _draw(self):
        self.screen.fill(self.BG_COLOR)
        if self.state == 'title':
            self._text(self.big_font, "BREAKOUT", (120, 90), (250, 150, 50))
            self._text(self.font, "Clear all the bricks", (120, 125), (170, 170, 170))
            self._text(self.font, "A = start", (120, 150))
            self._text(self.font, "SELECT = menu", (120, 173), (170, 170, 170))
            return
        self._draw_play()
        if self.state in ('won', 'lost'):
            pygame.draw.rect(self.screen, (0, 0, 0), (20, 80, 200, 100))
            msg, color = (("YOU WON!", (255, 255, 0)) if self.state == 'won'
                          else ("GAME OVER", (255, 80, 80)))
            self._text(self.big_font, msg, (120, 105), color)
            self._text(self.font, f"Score {self.score}", (120, 135))
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
