# -*- coding: utf-8 -*-
"""
Main program for the Mini_Player device
Controls the flow of the program. 
Starts with the Game Menu allows for a list of games to be chosen
Once a game or other option is chosen, it is called.
"""
import time, subprocess, sys
from mini_player import Mini_Player, GPIO
from game_menu import Game_Menu
import os

HERE = os.path.dirname(os.path.abspath(__file__))
GAME_PATH = os.path.join(HERE, "games")
sys.path.insert(0, GAME_PATH)
from screen_runner import Screen_Runner


player = Mini_Player()

Mini_Player.draw_splash(player)
menu = Game_Menu(player)
selected_option = menu.run()
is_running = True
while is_running:
    if selected_option == "off":
        player.message("Shutting down", "Wait ~15 sec,", "then unplug")
        GPIO.cleanup()
        subprocess.run(["shutdown", "-h", "now"])
        time.sleep(60)
        is_running = False
    elif selected_option == "exit":
        player.message("Menu closed")
        GPIO.cleanup()
        is_running = False
        sys.exit(0)
    else:
        if selected_option == "Screen Runner":
            game = Screen_Runner(player)
            print("Game initialized, running")
            game_running = game.run()
            player.show_loading(label="Return to Main")
            time.sleep(2)
        else:
            print("Not the right selection")
    selected_option = menu.run()
