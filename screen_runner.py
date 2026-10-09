# -*- coding: utf-8 -*-
"""
Created on Sun Oct  4 22:18:03 2026
Test game for Raspberry pi Zero Game Display hat

@author: Joey
"""
import os, random
#os.environ["SDL_VIDEODRIVER"] = "dummy"   # no real window needed
import pygame
from PIL import Image

#===== Start Screen Runner Game =====#
class Screen_Runner:
    PLAYER_W, PLAYER_H, PLAYER_SPEED = 24, 12, 5
    BLOCK_W, BLOCK_H = 24, 20
    SHOT_W, SHOT_H, SHOT_SPEED = 4,10,8
    PLAYER_COLOR = (80, 220, 120)
    SHOT_COLOR = (0,0,250)
    BLOCK_COLOR = (230, 60, 60)
    #===== Initialize the game =====#
    def __init__(self, mini_player):
        self.mini_player = mini_player
        pygame.init()
        self.screen = pygame.Surface((self.mini_player.WIDTH, self.mini_player.HEIGHT))
        self.font = pygame.font.Font(None, 28)
        self.clock = pygame.time.Clock()
        self.g = self._new_game()
        print("New Game made")
        self.running = True
        print(f"game running: {self.running}")
    #====== Show Screen ========#
    def _show(self):
        img = Image.frombytes("RGB", (240, 240), pygame.image.tostring(self.screen, "RGB"))
        self.mini_player.device.display(img)
    #====== Create a blank game ======#
    def _new_game(self):
        return {"x": 110,         #Starting position in the middle of screen
                "blocks": [],     #Array of falling blocks
                "shots": [],      #Array of shots
                "score": 0,       #Score (based on blocks shot and number of frames)
                "alive": True,    #Is running flag
                "tick": 0,        #Number of frames
                "cooldown":0      #Cool down between shots
                }
    #====== Move Player at SPEED ======#
    def _move_player(self, keys):
        if "PAD_LEFT" in keys:
            self.g["x"] = max(0,self.g["x"] - self.PLAYER_SPEED)
        if "PAD_RIGHT" in keys:
            self.g["x"] = min(240 - self.PLAYER_W, self.g["x"] + self.PLAYER_SPEED)
    #====== Create shots and add to array ======#
    def _shoot(self, keys):
        #Shoot with cooldown to pace the shots
        if self.g["cooldown"] > 0:
            self.g["cooldown"] -= 1
        if "BTN_X" in keys and self.g["cooldown"] == 0:
            self.g["shots"].append([self.g["x"] + self.PLAYER_W //2 - self.SHOT_W//2, 240-self.PLAYER_H])
            self.g["cooldown"] = 6 #frames between shots    
        #Move existing shots
        for shot in self.g["shots"]:
            shot[1] -= self.SHOT_SPEED
    #======= Create blocks, increase speed with time. Move them down ======#
    def _create_blocks(self):
        self.g["tick"] += 1
        if self.g["tick"] % 12 == 0:
            self.g["blocks"].append([random.randint(0, 216), -20])
        #Move blocks
        for b in self.g["blocks"]:
            b[1] += 4 + self.g["score"] // 10   # gets faster over time
        self.g["blocks"] = [b for b in self.g["blocks"] if b[1] < 240]
    #===== Check if the blocks have been shot =====#
    def _check_shot_blocks(self):
        #Shot and block collisions
        surviving_shots = []
        for shot in self.g["shots"]:
            shot_rect = pygame.Rect(shot[0], shot[1], self.SHOT_W, self.SHOT_H)
            hit = False
            for b in self.g["blocks"]:
                if shot_rect.colliderect(pygame.Rect(b[0], b[1], self.BLOCK_W, self.BLOCK_H)):
                    self.g["blocks"].remove(b)
                    self.g["score"] += 1
                    hit = True
                    break
            if not hit:
                surviving_shots.append(shot)
        self.g["shots"] = surviving_shots
    #===== Check if the player has been hit by a block =====#
    def _check_player_hit(self):
        player = pygame.Rect(self.g["x"], 220, self.PLAYER_W, self.PLAYER_H)
        #Check for block hitting player
        for bx, by in self.g["blocks"]:
            if player.colliderect(pygame.Rect(bx, by, self.BLOCK_W, self.BLOCK_H)):
                self.g["alive"] = False
        self.g["score"] += 0.1    
    #===== Draw current game frame =====#
    def _draw(self):
        # --- draw ---
        self.screen.fill((10, 10, 40))
        pygame.draw.rect(self.screen, self.PLAYER_COLOR, (self.g["x"], 220, self.PLAYER_W, self.PLAYER_H))
        for sx, sy in self.g["shots"]:
            pygame.draw.rect(self.screen, self.SHOT_COLOR, (sx,sy, self.SHOT_W, self.SHOT_H))
        for bx, by in self.g["blocks"]:
            pygame.draw.rect(self.screen, self.BLOCK_COLOR, (bx, by, self.BLOCK_W, self.BLOCK_H))
        self.screen.blit(self.font.render(f"Score {int(self.g['score'])}", True, (255, 255, 255)), (6, 6))
        if not self.g["alive"]:
            self.screen.blit(self.font.render("GAME OVER", True, (255, 255, 0)), (70, 100))
            self.screen.blit(self.font.render("A = restart", True, (200, 200, 200)), (70, 128))   
    #===== Running the game =====#
    def run(self):
        print("Start Game")
        try:
            while self.running:
                keys = self.mini_player.pressed()
                #===== EXIT =====#
                if "BTN_SELECT" in keys:
                    self.running = False
                    return False
                #====== IS RUNNING LOOP ======#
                if self.g["alive"]:
                    self._move_player(keys)
                    self._shoot(keys)
                    self._create_blocks()
                    self._check_shot_blocks()
                    self._check_player_hit()
                    self._draw()
                #====== Start new Game =======#
                elif "BTN_A" in keys:
                    self.g = self._new_game()
                self._show()
                self.clock.tick(20)
        finally:
            pygame.quit()
