'''
Pong for the MiniPlayer, using pygame (renders to a Surface, pushed to the LCD with PIL).

Controls:
    PAD_UP / PAD_DOWN : move paddle (hold A for double speed)
    BTN_A             : start, serve, play again
    BTN_SELECT        : back to menu

Fixes in this version:
    - Ball no longer sticks to paddles/walls (it used to flip direction every frame while
      overlapping). Now the ball is pushed out of the paddle/wall and given an explicit direction.
    - Ball hit-box now matches the drawn circle.
    - Ball is shown and follows the server's paddle until it is served.
    - Loser of a point serves next (P2 serves automatically after a short pause).
    - NPC paddle uses a simple "move toward target" logic, so it can't jitter or stall.
    - Win/lose: first to WIN_SCORE wins, with a result screen (A = play again).
'''
import random
import traceback

import pygame
from pygame.font import Font
from PIL import Image

FPS = 20
WIN_SCORE = 10


#===== Simple pong game implementation using pygame and PIL image =====#
class PongGame:
    PAD_WIDTH, PAD_HEIGHT = 5, 20
    PAD_SPEED = 60          # pixels per second (player)
    PAD_BOOST = 2            # multiplier while holding A
    NPC_SPEED = 80           # pixels per second (computer) - lower = easier
    BALL_SIZE = 4            # radius
    BALL_MAX_DX = 20
    BG_COLOR = (10, 10, 40)

    def __init__(self, mini_player):
        self.mini_player = mini_player
        pygame.font.init()
        self.font = Font(None, 18)
        self.big_font = Font(None, 40)
        self.screen = pygame.Surface((self.mini_player.WIDTH, self.mini_player.HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.released = False       # ignore buttons still held from the menu
        self.prev_keys = set()
        # Playing field
        self.top_y = 10
        self.bottom_y = self.mini_player.HEIGHT
        self.center_y = (self.top_y + self.bottom_y) // 2
        self.left_x = 0
        self.right_x = self.mini_player.WIDTH
        self.center_x = self.right_x // 2
        self.reset()

    #===== Game setup =====#
    def start(self):
        self.reset()
        self.state = 'play'

    def reset(self):
        self.state = 'title'            # title, play, won, lost
        self.player1_score = 0
        self.player2_score = 0
        self.paddle1_x = 4
        self.paddle2_x = self.mini_player.WIDTH - self.PAD_WIDTH - 4
        self.paddle1_y = self.center_y - self.PAD_HEIGHT / 2
        self.paddle2_y = self.center_y - self.PAD_HEIGHT / 2
        self.ball_x = self.center_x
        self.ball_y = self.center_y
        self.ball_dx = 0
        self.ball_dy = 0
        self._prepare_serve(1)

    def _prepare_serve(self, owner):
        """Ball waits on the server's paddle. Player 1 presses A; player 2 serves on a timer."""
        self.serve = True
        self.serve_owner = owner
        self.serve_timer = FPS if owner == 2 else 0     # ~1 second pause for the NPC
        self.ball_dx = 0
        self.ball_dy = 0
        self._attach_ball()

    def _attach_ball(self):
        r = self.BALL_SIZE
        if self.serve_owner == 1:
            self.ball_x = self.paddle1_x + self.PAD_WIDTH + r + 1
            self.ball_y = self.paddle1_y + self.PAD_HEIGHT / 2
        else:
            self.ball_x = self.paddle2_x - r - 1
            self.ball_y = self.paddle2_y + self.PAD_HEIGHT / 2

    def _launch(self):
        direction = 1 if self.serve_owner == 1 else -1
        self.ball_dx = direction * random.randint(3, 5)
        self.ball_dy = random.choice((-1, 1)) * random.randint(2, 4)
        self.serve = False

    #===== Per-frame update. Returns False to leave the game =====#
    def update(self, keys, dt):
        keys = set(keys)
        new = keys - self.prev_keys
        self.prev_keys = keys

        #===== Ignore buttons held from the menu =====#
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
        #===== Player 1 controls =====#
        speed = self.PAD_SPEED * (self.PAD_BOOST if 'BTN_A' in keys else 1)
        if 'PAD_UP' in keys:
            self.paddle1_y = self._clamp_pad(self.paddle1_y - speed * dt)
        if 'PAD_DOWN' in keys:
            self.paddle1_y = self._clamp_pad(self.paddle1_y + speed * dt)
        if 'BTN_B' in new:
            self.ball_dy = -self.ball_dy
        if self.serve:
            self._attach_ball()
            if self.serve_owner == 1:
                if 'BTN_A' in new:
                    self._launch()
            else:
                self.serve_timer -= 1
                if self.serve_timer <= 0:
                    self._launch()
        else:
            self._npc_pad_logic(dt)
            self._move_ball()

    #===== Ball movement =====#
    def _move_ball(self):
        r = self.BALL_SIZE
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy

        #===== Top & bottom walls: push back inside and set direction explicitly =====#
        if self.ball_y - r < self.top_y:
            self.ball_y = self.top_y + r
            self.ball_dy = abs(self.ball_dy)
        elif self.ball_y + r > self.bottom_y:
            self.ball_y = self.bottom_y - r
            self.ball_dy = -abs(self.ball_dy)

        ball = pygame.Rect(int(self.ball_x - r), int(self.ball_y - r), 2 * r, 2 * r)
        player_1 = pygame.Rect(int(self.paddle1_x), int(self.paddle1_y), self.PAD_WIDTH, self.PAD_HEIGHT)
        player_2 = pygame.Rect(int(self.paddle2_x), int(self.paddle2_y), self.PAD_WIDTH, self.PAD_HEIGHT)

        #===== Paddle hits: only when moving toward the paddle, then push the ball out =====#
        if self.ball_dx < 0 and player_1.colliderect(ball):
            self.ball_x = player_1.right + r
            self._bounce_off(self.paddle1_y, 1)
        elif self.ball_dx > 0 and player_2.colliderect(ball):
            self.ball_x = player_2.left - r
            self._bounce_off(self.paddle2_y, -1)

        #===== Ball got past a paddle =====#
        if self.ball_x < self.left_x:
            self._point_scored(2)
        elif self.ball_x > self.right_x:
            self._point_scored(1)

    def _bounce_off(self, paddle_y, x_dir):
        """Send the ball away from the paddle. Angle depends on where it hit; each hit speeds it up a bit."""
        offset = (self.ball_y - (paddle_y + self.PAD_HEIGHT / 2)) / (self.PAD_HEIGHT / 2)
        offset = max(-1.0, min(1.0, offset))
        self.ball_dx = x_dir * min(abs(self.ball_dx) * 1.05, self.BALL_MAX_DX)
        self.ball_dy = offset * 4
        if abs(self.ball_dy) < 1:                  # never let it go perfectly flat
            self.ball_dy = 1 if self.ball_dy >= 0 else -1

    def _point_scored(self, scorer):
        if scorer == 1:
            self.player1_score += 1
        else:
            self.player2_score += 1

        if self.player1_score >= WIN_SCORE:
            self.state = 'won'
        elif self.player2_score >= WIN_SCORE:
            self.state = 'lost'
        else:
            # The player who lost the point serves next
            self._prepare_serve(2 if scorer == 1 else 1)

    #===== NPC Player Movement =====#
    def _npc_pad_logic(self, dt):
        pad_center = self.paddle2_y + self.PAD_HEIGHT / 2
        # Chase the ball while it's coming; drift back to the middle after returning it
        target = self.ball_y if self.ball_dx > 0 else self.center_y
        diff = target - pad_center
        step = self.NPC_SPEED * dt
        if abs(diff) <= step:
            self.paddle2_y = self._clamp_pad(self.paddle2_y + diff)
        else:
            self.paddle2_y = self._clamp_pad(self.paddle2_y + (step if diff > 0 else -step))

    def _clamp_pad(self, y):
        return max(self.top_y, min(self.bottom_y - self.PAD_HEIGHT, y))

    #===== Drawing =====#
    def _text(self, font, msg, center, color=(255, 255, 255)):
        surf = font.render(msg, True, color)
        self.screen.blit(surf, surf.get_rect(center=center))

    def _draw_score(self):
        self._text(self.font, str(self.player1_score), (self.center_x - 30, 20))
        self._text(self.font, str(self.player2_score), (self.center_x + 30, 20))

    def _draw_court(self):
        pygame.draw.line(self.screen, (60, 60, 100), (0, self.top_y), (self.right_x, self.top_y))
        for y in range(self.top_y, self.bottom_y, 12):
            pygame.draw.line(self.screen, (60, 60, 100), (self.center_x, y), (self.center_x, y + 6))

    def _draw_paddles(self):
        for x, y in ((self.paddle1_x, self.paddle1_y), (self.paddle2_x, self.paddle2_y)):
            pygame.draw.rect(self.screen, (255, 255, 255),
                             (int(x), int(y), self.PAD_WIDTH, self.PAD_HEIGHT))

    def _draw(self):
        self.screen.fill(self.BG_COLOR)
        if self.state == 'title':
            self._text(self.big_font, "PONG", (120, 90), (80, 100, 220))
            self._text(self.font, f"First to {WIN_SCORE} wins", (120, 120), (170, 170, 170))
            self._text(self.font, "A = start", (120, 145))
            self._text(self.font, "SELECT = menu", (120, 168), (170, 170, 170))
            return

        self._draw_court()
        self._draw_score()
        self._draw_paddles()
        pygame.draw.circle(self.screen, (255, 255, 255),
                           (int(self.ball_x), int(self.ball_y)), self.BALL_SIZE)

        if self.state == 'play' and self.serve and self.serve_owner == 1:
            self._text(self.font, "A = serve", (self.center_x, self.mini_player.HEIGHT - 30))

        if self.state in ('won', 'lost'):
            pygame.draw.rect(self.screen, (0, 0, 0), (20, 70, 200, 110))
            if self.state == 'won':
                msg, color = "YOU WON!", (255, 255, 0)
            else:
                msg, color = "YOU LOST", (255, 80, 80)
            self._text(self.big_font, msg, (120, 95), color)
            self._text(self.font, f"{self.player1_score} - {self.player2_score}", (120, 125))
            self._text(self.font, "A = play again", (120, 146))
            self._text(self.font, "SELECT = menu", (120, 164), (170, 170, 170))

    #===== Push the frame to the LCD =====#
    def _show(self):
        img = Image.frombytes("RGB", (240, 240), pygame.image.tostring(self.screen, "RGB"))
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

