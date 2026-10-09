# -*- coding: utf-8 -*-
"""
This is the configuration of the mini_player device. 
It sets up the LCD screen and adds all the keys
It has the basic fonts and main functions
"""
import sys 
import os
from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.lcd.device import st7789
from PIL import Image, ImageDraw, ImageFont
import RPi.GPIO as GPIO
import time

class Mini_Player:
    #===== PINS =====#
    DC_PIN = 22      
    RST_PIN = 27     #Reset pin
    #===== BUTTONS =====#
    board_keys = {
        "PAD_PRESS": 3,
        "PAD_UP": 5,
        "PAD_DOWN": 16,
        "PAD_LEFT": 13,
        "PAD_RIGHT": 6,
        "BTN_START": 19,
        "BTN_SELECT": 26,
        "BTN_LEFT": 14,
        "BTN_RIGHT": 23,
        "BTN_X": 15,
        "BTN_Y": 12,
        "BTN_B": 20,
        "BTN_A": 21,
    }
    WIDTH = 240
    HEIGHT = 240
    FONT_DIR = "/usr/share/fonts/truetype/dejavu/"
    SPLASH_FONT = ImageFont.truetype(FONT_DIR + "DejaVuSans-Bold.ttf",32)
    TITLE_FONT = ImageFont.truetype(FONT_DIR + "DejaVuSans-Bold.ttf", 22)
    ITEM_FONT = ImageFont.truetype(FONT_DIR + "DejaVuSans.ttf", 20)
    HERE = os.path.dirname(os.path.abspath(__file__))
    LOADING_IMG = os.path.join(HERE, "images", "penguin_char.png")
    SPLASH_IMG = os.path.join(HERE, "images", "dark_squid.jpg")
    #===== Initilizer =====#
    def __init__(self):    
        #===== DISPLAY =====#
        self.serial = spi(port=0, device=0, gpio_DC=self.DC_PIN, gpio_RST=self.RST_PIN,
                     bus_speed_hz=32000000)
        self.device = st7789(self.serial, width=240, height=240, rotate=0)
        #===== FONT =====#
        for _pin in self.board_keys.values():
            GPIO.setup(_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    #===== Clear screen =====#
    def clear(self, color="black"):
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, fill=color)
    #===== print message at position (x,y), font, color, bg =====#
    def say(self, msg, xy=(10, 10), font=SPLASH_FONT, color="white", bg="black"):
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, fill=bg)
            draw.text(xy, msg, font=font, fill=color)         
    #===== Return list of buttons pressed =====#
    def pressed(self):
        return [name for name, pin in self.board_keys.items()
                if GPIO.input(pin) == GPIO.LOW]
    #===== Block until a button is pressed =====#
    def wait_for_press(self, timeout=None):
        start = time.time()
        while True:
            p = self.pressed()
            if p:
                return p[0]
            if timeout and time.time() - start > timeout:
                return None
            time.sleep(0.01)
    #===== Show helf button on the LCD live =====#
    def button_test(self):
        last = None
        try:
            while True:
                p = self.pressed()
                if p != last:
                    with canvas(self.device) as draw:
                        draw.rectangle(self.device.bounding_box, fill="black")
                        draw.text((10, 10), "Buttons:", font=self.small_font, fill="gray")
                        for i, name in enumerate(p):
                            draw.text((10, 40 + i * 24), name, font=self.small_font, fill="white")
                    last = p
                time.sleep(0.01)
        except KeyboardInterrupt:
            self.clear()
    #===== Draw Splash Screen =====#
    def draw_splash(self):
        with canvas(self.device) as draw:
            img = Image.open(self.SPLASH_IMG).convert("RGB").resize((240,240))
            self.device.display(img)
            time.sleep(3)
            ImageDraw.Draw(img).text((20, 100), "Mini Player",font=self.SPLASH_FONT, fill=(220,0,100))
            self.device.display(img)
            time.sleep(3)
    def show_loading(self, label="Loading..."):
        try:
            img = Image.open(self.LOADING_IMG).convert("RGB").resize((240,240))
        except Exception:
            self.message(label)    #fallback if image is missing
            return
        d = ImageDraw.Draw(img)
        d.rectangle((0,200,240,240), fill=(0,0,0))   #dark box to make font visible
        d.text((14,207), label, font=self.ITEM_FONT, fill="white")
        self.device.display(img)
        time.sleep(2)
    def message(self,*lines):
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, fill="black")
            for i, line in enumerate(lines):
                draw.text((14, 70 + i * 30), line, font=self.ITEM_FONT, fill="white")
