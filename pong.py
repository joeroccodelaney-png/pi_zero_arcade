'''
Created 8 Oct 26. Output from gemma3:4b.
Desired Pong games for the MiniPlayer
Using pygame

Current:
    Player 2 getting stuck in the middle
    It is starting before serve
    no bouncing off player 1

'''
#TEST NOTES:
#First run crash

#games/pong.py   v1.0
import pygame
from pygame.font import Font
from PIL.Image import frombytes
from PIL import Image
import random


FPS = 30
DT_MAX = 0.05
'''
States:
    play
    title
    win
    loose
'''


#===== Simple pong game implementation using pygame and PIL image=====#
class PongGame:
    PAD_WIDTH, PAD_HEIGHT, PAD_SPEED = 5, 20, 40
    BALL_SIZE, BALL_SPEED = 4, 10
    SCORE_TARGET = 10
    BG_COLOR = (10,10,40)
    def __init__(self, mini_player):
        self.mini_player = mini_player
        pygame.font.init()
        self.font = Font(None, 18)
        self.big_font = pygame.font.Font(None, 40)
        self.screen = pygame.Surface((self.mini_player.WIDTH, self.mini_player.HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.released = False
        self.prev_keys = set()
        self.top_y = 10
        self.bottom_y = self.mini_player.HEIGHT
        self.center_y = (self.bottom_y - self.top_y) // 2
        self.left_x = 0
        self.right_x = self.mini_player.WIDTH
        self.center_x = self.right_x // 2
        self.paddle1_dy = 0
        self.paddle2_dy = 0
        self.reset()
    def start(self):
        self.reset()
        self.state = 'play'
    def reset(self):
        self.state = 'title'
        self.player1_score = 0
        self.player2_score = 0
        #self.ball_x = self.center_x
        #self.ball_y = self.center_y
        self.ball_dx = 2
        self.ball_dy = 2
        self.paddle1_x = self.PAD_WIDTH // 2
        self.paddle1_y = self.center_y - self.PAD_HEIGHT // 2
        self.paddle2_x = self.mini_player.WIDTH - self.PAD_WIDTH
        self.paddle2_y = self.center_y - self.PAD_HEIGHT // 2        
        self.serve = True

    def update(self, keys, dt):
        keys = set(keys)
        new = keys - self.prev_keys
        self.prev_keys = keys
        paddle1_y_start = self.paddle1_y
        paddle2_y_start = self.paddle2_y
        #===== Ignore A button held from menu =====#
        if not self.released:
            if not keys:
                self.released = True
            return True
        if 'BTN_SELECT' in new:
            return False
        #===== If in play state =====#
        elif self.state == 'play':
            #=====Player 1 Controls =====#
            if 'PAD_UP' in keys:
                self.paddle1_y = self._pad_move_up(self.paddle1_y, dt)
                if 'BTN_A' in keys:
                    self.paddle1_y = self._pad_move_up(self.paddle1_y, dt, self.PAD_SPEED*3)
            if 'PAD_DOWN' in keys:
                self.paddle1_y = self._pad_move_down(self.paddle1_y, dt)
                if 'BTN_A' in keys:
                    self.paddle1_y = self._pad_move_down(self.paddle1_y, dt)
            # ===== Exit game =====#
            if 'BTN_SELECT' in new:
                self.state = 'lost'
                self.player1_score = 0
                self.player2_score = 0
                self.serve = True
                return False  # Select exits play
            if not self.serve:
                self._npc_pad_logic(dt)
                self._move_ball()
            self.paddle1_dy = self.paddle1_y - paddle1_y_start
            self.paddle2_dy = self.paddle2_y - paddle2_y_start
            if 'BTN_A' in new and self.serve is True:
                self.serve = False
                self._serve_player1()
        elif self.state == 'title':
            if 'BTN_A' in new:
                self.state = 'play'
        return True
    #===== Ball Movements =====#
    def _move_ball(self):
        player_1 = pygame.Rect(self.paddle1_x, self.paddle1_y, self.PAD_WIDTH, self.PAD_HEIGHT)
        player_2 = pygame.Rect(self.paddle2_x, self.paddle2_y, self.PAD_WIDTH, self.PAD_HEIGHT)
        ball = pygame.Rect(self.ball_x-self.BALL_SIZE//2, self.ball_y+self.BALL_SIZE//2, self.BALL_SIZE, self.BALL_SIZE)
        #===== Check for collision with top & bottom
        if self.ball_y < self.top_y - self.BALL_SIZE or self.ball_y > self.bottom_y - self.BALL_SIZE:
            self.ball_dy = -self.ball_dy
        #===== Check for collision with player 1 =====#
        if player_1.colliderect(ball):
            self.ball_dx = -self.ball_dx
        if player_2.colliderect(ball):
            self.ball_dx = -self.ball_dx
        #===== Ball hit left side =====#
        if self.ball_x < self.left_x + self.PAD_WIDTH // 2:
            self.player2_score += 1
            print(f"Player 2 Score: {self.player2_score}")
            self._serve_player2()
        #===== Ball hit right side =====#
        elif self.ball_x > self.right_x - self.PAD_WIDTH // 2:
            self.player1_score += 1
            self.serve = True
            self._serve_player1()
            print(f"Player 1 Score: {self.player1_score}")
        #===== Move forward one frame =====#
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy
    def _serve_player1(self):
        print("Player 1 serve")
        self.ball_x = self.paddle1_x + self.PAD_WIDTH
        self.ball_y = self.paddle1_y + self.PAD_HEIGHT
        self.ball_dx = random.randint(3,5)
        self.ball_dy = max(self.paddle1_dy, random.randint(2,4))
    def _serve_player2(self):
        print("Player 2 serve")
        print("Pad2_x: {self.paddle2_x} Pad2_y: {self.paddle2_y}")
        self.ball_x = self.paddle2_x - self.PAD_WIDTH
        self.ball_y = self.paddle2_y + (self.PAD_HEIGHT // 2)
        self.ball_dx = -1 * random.randint(3,5)
        self.ball_dy = max(self.paddle2_dy, random.randint(2,4))
    def _ball_reset(self, x_dir=1, y_dir=1):
        self.ball_x = self.center_x
        self.ball_y = self.center_y
        self.ball_dx = x_dir*random.randint(1,3)
        self.ball_dy = y_dir*random.randint(1,3)
    #===== NPC Player Movement =====#
    def _npc_pad_logic(self, dt):
        pad_center = self.paddle2_y + self.PAD_HEIGHT // 2
        movingRight = True if self.ball_dx > 0 else False
        movingUp = True if self.ball_dy < 0 else False
        #Moving up and to the right
        if movingRight and movingUp:
            #Pad lower than the ball
            if pad_center > self.ball_y:
                self.paddle2_y = self._pad_move_up(self.paddle2_y, dt)
        #Moving down and to the right
        elif movingRight and not movingUp:
            #Pad higher than the ball
            if pad_center < self.ball_y:
                self.paddle2_y = self._pad_move_down(self.paddle2_y, dt)
        #After ball returned paddle moves towards the middle
        elif not movingRight:
            #Paddle moves down if in the upper half of screen
            if pad_center < self.center_y-2:
                self.paddle2_y = self._pad_move_down(self.paddle2_y, dt)
            elif pad_center > self.center_y+2:
                self.paddle2_y = self._pad_move_up(self.paddle2_y, dt)
            
    def _pad_move_up(self, y, dt, speed=PAD_SPEED):
        return max(self.top_y, y - speed * dt)
    def _pad_move_down(self, y, dt, speed=PAD_SPEED):
        return min(self.bottom_y - self.PAD_HEIGHT, y + speed*dt)
            
    def _text(self, font, msg, center, color=(255,255,255)):
        surf = font.render(msg, True, color)
        self.screen.blit(surf, surf.get_rect(center=center))
    def _draw_score(self):
        #===== PLAYER 1 SCORE =====#
        score_text = self.font.render(str(self.player1_score), 1, (255, 255, 255))
        score_text_rect = score_text.get_rect()
        score_text_rect.center = (self.center_x, 20)
        self.screen.blit(score_text, score_text_rect)
        #===== PLAYER 2 SCORE =====#
        score_text = self.font.render(str(self.player2_score), 1, (255, 255, 255))
        score_text_rect = score_text.get_rect()
        score_text_rect.center = (self.center_x, 60)
        self.screen.blit(score_text, score_text_rect)
    def _draw_paddles(self):
        #Set color
        paddle1_color = (255,255,255)
        paddle2_color = (255,255,255)
        #Set Size
        paddle1_rect = (self.paddle1_x, self.paddle1_y, self.PAD_WIDTH, self.PAD_HEIGHT)
        paddle2_rect = (self.paddle2_x, self.paddle2_y, self.PAD_WIDTH, self.PAD_HEIGHT)
        #Draw
        pygame.draw.rect(self.screen, paddle1_color, paddle1_rect)
        pygame.draw.rect(self.screen, paddle2_color, paddle2_rect)
    #===== Draw the current frame =====#
    def _draw(self):
        self.screen.fill(self.BG_COLOR)
        if self.state == 'title':
            self._text(self.big_font, "PONG", (120,90), (80, 100, 220))
            self._text(self.font, "A = start", (120,135))
            self._text(self.font, "SELECT = menu", (120,160), (170, 170, 170))
            return
        if self.state == 'play':
            self._draw_score()
            self._draw_paddles()
            # Draw ball
            if not self.serve:
                pygame.draw.circle(self.screen, (255, 255, 255), (self.ball_x, self.ball_y), self.BALL_SIZE)
        if self.state in ('won', 'lost'):
            pygame.draw.rect(self.screen, (0,0,0), (20,80,200,100))
            if self.state == 'won': msg, color = ("YOU WON!", (255,255,0))
            if self.state == 'lost': msg, color = ("GAME OVER", (255,80,80))
            self._text(self.big_font, msg, (120, 100), color)
            self._text(self.font, "A = play again", (120, 142))
            self._text(self.font, "SELECT = menu", (120, 164), (170, 170, 170))
            
        if self.serve:
            serve_text = self.font.render("Serve", 1, (255, 255, 255))
            serve_text_rect = serve_text.get_rect()
            serve_text_rect.center = (self.mini_player.WIDTH // 2, self.mini_player.HEIGHT - 30)
            self.screen.blit(serve_text, serve_text_rect)
    #===== Push the frame to the LCD ====#
    def _show(self):
        img = Image.frombytes("RGB", (240,240), pygame.image.tostring(self.screen, "RGB"))
        self.mini_player.device.display(img)
    def run(self):
        try: 
            self.running = True
            while self.running:
                dt = min(self.clock.tick(20) / 1000.0, 0.1)
                keys = self.mini_player.pressed()
                if not self.update(keys, dt):
                    self.running = False
                self._draw()
                self._show()
        except Exception as e:
            print(f"Error playing game: {e}")
        finally:
            pygame.quit()
        return False
    def device_display(self, image):
        """Displays the rendered screen image."""
        self.screen.blit(image, (0, 0))
        return image
