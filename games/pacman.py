# -*- coding: utf-8 -*-
"""
Pac-Man for the Mini_Player device (240x240 LCD).

States: title, play, won, lost
Controls: PAD_UP / PAD_DOWN / PAD_LEFT / PAD_RIGHT steer, BTN_A starts /
          plays again, BTN_SELECT returns to the menu.

Eat every dot in the maze while dodging the four ghosts. Power pellets make
the ghosts vulnerable for a short time so you can eat them. Three lives; lose
one whenever a ghost catches you.
"""
import math
import random
import traceback

import pygame
from pygame.font import Font
from PIL import Image

FPS = 20

COLS = 18
ROWS = 18
CELL = 12
HUD_H = 24
MAZE_OX = (240 - COLS * CELL) // 2   # center the maze horizontally
MAZE_OY = HUD_H

STEP = 0.15        # seconds per grid step
LIVES = 3
FRIGHT_TIME = 6.0  # seconds of vulnerability after a power pellet

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
DIRS = [UP, DOWN, LEFT, RIGHT]
OPP = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}

GHOST_COLORS = [(255, 0, 0), (255, 184, 255), (0, 255, 255), (255, 184, 82)]
FRIGHT_COLOR = (40, 40, 200)
BG_COLOR = (0, 0, 0)
WALL_COLOR = (30, 30, 160)
DOT_COLOR = (255, 220, 180)
POWER_COLOR = (255, 200, 120)
PAC_COLOR = (255, 220, 40)


class PacManGame:
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
        self._build_maze()
        self.reset()

    #===== Maze =====
    def _build_maze(self):
        self.walls = [[False] * COLS for _ in range(ROWS)]
        # Border.
        for x in range(COLS):
            self.walls[0][x] = self.walls[ROWS - 1][x] = True
        for y in range(ROWS):
            self.walls[y][0] = self.walls[y][COLS - 1] = True
        # Vertical wall strips with staggered gaps (rows 1 and 16 stay fully open,
        # so every corridor connects via the top or bottom row).
        for i, col in enumerate([3, 6, 9, 12, 15]):
            for y in range(2, ROWS - 2):
                if (y - 2) % 5 == i % 5:
                    continue          # leave a gap
                self.walls[y][col] = True

    def _pixel_center(self, x, y):
        return (MAZE_OX + x * CELL + CELL // 2, MAZE_OY + y * CELL + CELL // 2)

    def _is_wall(self, x, y):
        if x < 0 or y < 0 or x >= COLS or y >= ROWS:
            return True
        return self.walls[y][x]

    def _can_move(self, pos, d):
        nx, ny = pos[0] + d[0], pos[1] + d[1]
        return not self._is_wall(nx, ny)

    #===== Game setup =====
    def reset(self):
        self.state = 'title'
        self.score = 0
        self.lives = LIVES
        # Dots on every corridor cell; power pellets in the four corners.
        self.dots = [[False] * COLS for _ in range(ROWS)]
        self.power = set()
        for y in range(ROWS):
            for x in range(COLS):
                if not self.walls[y][x]:
                    self.dots[y][x] = True
        for cx, cy in ((1, 1), (COLS - 2, 1), (1, ROWS - 2), (COLS - 2, ROWS - 2)):
            self.power.add((cx, cy))
            self.dots[cy][cx] = False
        # Clear dots from the starting areas so nothing overlaps the sprites.
        for sx, sy in ((10, 15), (10, 8), (11, 8), (10, 9), (11, 9)):
            self.dots[sy][sx] = False

        self.pac_pos = [10, 15]
        self.pac_dir = LEFT
        self.pending_dir = None
        self.ghosts = [
            {'pos': [10, 8], 'dir': UP, 'color': GHOST_COLORS[0], 'mode': 'chase'},
            {'pos': [11, 8], 'dir': UP, 'color': GHOST_COLORS[1], 'mode': 'scatter', 'corner': (1, 1)},
            {'pos': [10, 9], 'dir': UP, 'color': GHOST_COLORS[2], 'mode': 'scatter', 'corner': (COLS - 2, 1)},
            {'pos': [11, 9], 'dir': UP, 'color': GHOST_COLORS[3], 'mode': 'scatter', 'corner': (1, ROWS - 2)},
        ]
        self.step_timer = 0.0
        self.fright_timer = 0.0
        self.mouth_t = 0.0
        self.pause_timer = 0.0

    def start(self):
        self.reset()
        self.state = 'play'
        self.pause_timer = 1.0

    def _dot_total(self):
        return sum(sum(row) for row in self.dots)

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

    def _update_play(self, keys, new, dt):
        # Steering intent from the D-pad.
        if 'PAD_UP' in keys:
            self.pending_dir = UP
        elif 'PAD_DOWN' in keys:
            self.pending_dir = DOWN
        elif 'PAD_LEFT' in keys:
            self.pending_dir = LEFT
        elif 'PAD_RIGHT' in keys:
            self.pending_dir = RIGHT

        if self.fright_timer > 0:
            self.fright_timer -= dt
        self.mouth_t += dt

        if self.pause_timer > 0:
            self.pause_timer -= dt
            return

        self.step_timer += dt
        while self.step_timer >= STEP:
            self.step_timer -= STEP
            self._step()

    def _step(self):
        # Apply a queued turn if it is legal.
        if self.pending_dir is not None:
            if self._can_move(self.pac_pos, self.pending_dir):
                self.pac_dir = self.pending_dir
            self.pending_dir = None
        if self._can_move(self.pac_pos, self.pac_dir):
            self.pac_pos[0] += self.pac_dir[0]
            self.pac_pos[1] += self.pac_dir[1]
        self._eat_at()
        for g in self.ghosts:
            self._move_ghost(g)
        self._check_ghost_collision()

    def _eat_at(self):
        x, y = self.pac_pos
        if self.dots[y][x]:
            self.dots[y][x] = False
            self.score += 10
        if (x, y) in self.power:
            self.power.discard((x, y))
            self.score += 50
            self.fright_timer = FRIGHT_TIME
        if self._dot_total() == 0 and not self.power:
            self.state = 'won'

    def _move_ghost(self, g):
        frightened = self.fright_timer > 0
        if frightened:
            choices = [d for d in DIRS
                       if d != OPP[g['dir']] and self._can_move(g['pos'], d)]
            if not choices:
                choices = [d for d in DIRS if self._can_move(g['pos'], d)]
            g['dir'] = random.choice(choices) if choices else g['dir']
        else:
            if g['mode'] == 'chase':
                target = self.pac_pos
            else:
                target = g['corner']
            choices = [d for d in DIRS
                       if d != OPP[g['dir']] and self._can_move(g['pos'], d)]
            if not choices:
                choices = [d for d in DIRS if self._can_move(g['pos'], d)]
            if choices:
                # Pick the direction that gets closest to the target, with some randomness.
                best = min(choices, key=lambda d: self._dist_to(target, g['pos'], d))
                # Occasionally wander so the chase is beatable.
                if random.random() < 0.15:
                    g['dir'] = random.choice(choices)
                else:
                    g['dir'] = best
        g['pos'][0] += g['dir'][0]
        g['pos'][1] += g['dir'][1]

    def _dist_to(self, target, pos, d):
        nx, ny = pos[0] + d[0], pos[1] + d[1]
        tx, ty = target
        return (nx - tx) ** 2 + (ny - ty) ** 2

    def _check_ghost_collision(self):
        frightened = self.fright_timer > 0
        for g in self.ghosts:
            if tuple(g['pos']) == tuple(self.pac_pos):
                if frightened:
                    self.score += 200
                    g['pos'] = [10, 9]
                    g['dir'] = UP
                else:
                    self._hit()
                    return

    def _hit(self):
        self.lives -= 1
        if self.lives <= 0:
            self.state = 'lost'
        else:
            self.pac_pos = [10, 15]
            self.pac_dir = LEFT
            self.pending_dir = None
            self.ghosts = [
                {'pos': [10, 8], 'dir': UP, 'color': GHOST_COLORS[0], 'mode': 'chase'},
                {'pos': [11, 8], 'dir': UP, 'color': GHOST_COLORS[1], 'mode': 'scatter', 'corner': (1, 1)},
                {'pos': [10, 9], 'dir': UP, 'color': GHOST_COLORS[2], 'mode': 'scatter', 'corner': (COLS - 2, 1)},
                {'pos': [11, 9], 'dir': UP, 'color': GHOST_COLORS[3], 'mode': 'scatter', 'corner': (1, ROWS - 2)},
            ]
            self.fright_timer = 0.0
            self.pause_timer = 1.0

    #===== Drawing =====
    def _text(self, font, msg, center, color=(255, 255, 255)):
        surf = font.render(msg, True, color)
        self.screen.blit(surf, surf.get_rect(center=center))

    def _draw_hud(self):
        self._text(self.font, f"Score {self.score}", (56, 12))
        self._text(self.font, f"Lives {self.lives}", (190, 12), (255, 120, 120))

    def _draw_maze(self):
        for y in range(ROWS):
            for x in range(COLS):
                if self.walls[y][x]:
                    pygame.draw.rect(self.screen, WALL_COLOR,
                                     (MAZE_OX + x * CELL, MAZE_OY + y * CELL, CELL, CELL))
                elif self.dots[y][x]:
                    cx, cy = self._pixel_center(x, y)
                    pygame.draw.circle(self.screen, DOT_COLOR, (cx, cy), 2)
        for x, y in self.power:
            cx, cy = self._pixel_center(x, y)
            r = 5 if (int(self.mouth_t * 4) % 2 == 0) else 4
            pygame.draw.circle(self.screen, POWER_COLOR, (cx, cy), r)

    def _draw_pac(self):
        cx, cy = self._pixel_center(self.pac_pos[0], self.pac_pos[1])
        r = CELL // 2 - 1
        pygame.draw.circle(self.screen, PAC_COLOR, (cx, cy), r)
        # Mouth wedge, opening and closing over time.
        mouth_half = 0.25 + 0.35 * (0.5 + 0.5 * math.sin(self.mouth_t * 10))
        ang = {UP: -math.pi / 2, DOWN: math.pi / 2, LEFT: math.pi, RIGHT: 0.0}[self.pac_dir]
        p1 = (cx + r * math.cos(ang - mouth_half), cy + r * math.sin(ang - mouth_half))
        p2 = (cx + r * math.cos(ang + mouth_half), cy + r * math.sin(ang + mouth_half))
        pygame.draw.polygon(self.screen, BG_COLOR, [(cx, cy), p1, p2])

    def _draw_ghosts(self):
        frightened = self.fright_timer > 0
        for g in self.ghosts:
            cx, cy = self._pixel_center(g['pos'][0], g['pos'][1])
            r = CELL // 2 - 1
            color = FRIGHT_COLOR if frightened else g['color']
            pygame.draw.circle(self.screen, color, (cx, cy), r)
            if not frightened:
                pygame.draw.circle(self.screen, (255, 255, 255), (cx - 3, cy - 2), 3)
                pygame.draw.circle(self.screen, (255, 255, 255), (cx + 3, cy - 2), 3)
                pygame.draw.circle(self.screen, (0, 0, 0), (cx - 3, cy - 2), 1)
                pygame.draw.circle(self.screen, (0, 0, 0), (cx + 3, cy - 2), 1)

    def _draw(self):
        self.screen.fill(BG_COLOR)
        self._draw_hud()
        if self.state == 'title':
            self._text(self.big_font, "PAC-MAN", (120, 110), PAC_COLOR)
            self._text(self.font, "Eat the dots, dodge ghosts", (120, 145), (170, 170, 170))
            self._text(self.font, "A = start", (120, 170))
            self._text(self.font, "SELECT = menu", (120, 193), (170, 170, 170))
            return
        self._draw_maze()
        self._draw_ghosts()
        self._draw_pac()
        if self.state in ('won', 'lost'):
            pygame.draw.rect(self.screen, (0, 0, 0), (20, 90, 200, 100))
            msg, color = (("YOU WON!", (255, 255, 0)) if self.state == 'won'
                          else ("GAME OVER", (255, 80, 80)))
            self._text(self.big_font, msg, (120, 115), color)
            self._text(self.font, f"Score {self.score}", (120, 145))
            self._text(self.font, "A = play again", (120, 166))
            self._text(self.font, "SELECT = menu", (120, 184), (170, 170, 170))

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
