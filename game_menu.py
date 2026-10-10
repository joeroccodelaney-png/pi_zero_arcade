# -*- coding: utf-8 -*-
"""PROPOSED replacement: Joey review and manual target installation required.

Retains the existing menu contract, fonts, canvas and 34-pixel row spacing.
A four-row scrolling window keeps all six entries above the footer.
"""
import time
from luma.core.render import canvas


class Game_Menu:
    # Display names must match explicit launcher dispatch branches.
    GAMES = ["Screen Runner", "Snake", "Pong", "Breakout", "Asteroids", "Blocks", "Flappy", "Space Invader", "Frogger", "Pac-Man"]
    ITEMS = [(n, "game") for n in GAMES] + [
        ("Power off", "off"),
        ("Exit to shell", "exit"),
    ]
    VISIBLE_ROWS = 4

    def __init__(self, player):
        self.selected = 0
        self.first_visible = 0
        self.player = player
        self._wait_release()
        self._draw_menu()
        self.running = True

    def _wait_release(self):
        while self.player.pressed():
            time.sleep(0.02)

    def _draw_menu(self):
        # Keep selection visible, including either direction of wraparound.
        if self.selected < self.first_visible:
            self.first_visible = self.selected
        elif self.selected >= self.first_visible + self.VISIBLE_ROWS:
            self.first_visible = self.selected - self.VISIBLE_ROWS + 1
        with canvas(self.player.device) as d:
            d.rectangle(self.player.device.bounding_box, fill="black")
            d.text((14, 8), "GAME MENU", font=self.player.TITLE_FONT, fill="yellow")
            visible = self.ITEMS[self.first_visible:self.first_visible + self.VISIBLE_ROWS]
            for row, (name, _) in enumerate(visible):
                i = self.first_visible + row
                y = 48 + row * 34
                if i == self.selected:
                    d.rectangle((8, y - 3, 232, y + 27), fill=(40, 90, 200))
                d.text((18, y), name, font=self.player.ITEM_FONT, fill="white")
            d.text((18, 190), f"{self.selected + 1}/{len(self.ITEMS)}", fill="gray")
            d.text((10, 218), "Up/Down  A=select", fill="gray")

    def _confirm_off(self):
        self.player.message("Power off?", "A = yes", "B = cancel")
        self._wait_release()
        while True:
            p = self.player.pressed()
            if "BTN_A" in p:
                return True
            if "BTN_B" in p:
                return False
            time.sleep(0.02)

    def run(self):
        self.running = True
        self._draw_menu()
        # On every entry, consume held launch/return/navigation inputs until
        # all keys release. Do not relaunch or move on an inherited hold.
        self._wait_release()
        prev = set()
        while self.running:
            now = set(self.player.pressed())
            new = now - prev
            prev = now
            if "PAD_UP" in new:
                self.selected = (self.selected - 1) % len(self.ITEMS)
                self._draw_menu()
            elif "PAD_DOWN" in new:
                self.selected = (self.selected + 1) % len(self.ITEMS)
                self._draw_menu()
            elif "BTN_A" in new or "PAD_PRESS" in new:
                name, kind = self.ITEMS[self.selected]
                if kind == "game":
                    self.player.show_loading(f"Loading {name}...")
                    self.running = False
                    print(f"Game Selected {name}")
                    return name
                elif kind == "off":
                    if self._confirm_off():
                        return "off"
                    else:
                        self._wait_release()
                        prev = set()
                        self._draw_menu()
                elif kind == "exit":
                    return "exit"
            time.sleep(0.02)
