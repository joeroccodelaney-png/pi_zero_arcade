# -*- coding: utf-8 -*-
"""
This file demonstrates some of the ways to use the LCD screen.
"""

from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.lcd.device import st7789

serial = spi(port=0, device=0, gpio_DC=22, gpio_RST=27, bus_speed_hz=32000000)
device = st7789(serial, width=240, height=240, rotate=0)

with canvas(device) as draw:
    draw.rectangle(device.bounding_box, fill="black")   # clear the screen
    draw.text((20, 20), "Hello!", fill="white")
    

with canvas(device) as draw:
    draw.rectangle((10, 10, 100, 60), outline="white", fill="blue")    # (left, top, right, bottom)
    draw.ellipse((120, 10, 220, 60), outline="yellow", width=3)
    draw.line((10, 80, 230, 80), fill="green", width=2)               # (x1, y1, x2, y2)
    draw.polygon([(120, 100), (160, 160), (80, 160)], fill="orange")  # triangle
    draw.arc((20, 170, 100, 230), start=0, end=270, fill="cyan", width=3)
    draw.point((200, 200), fill="white")                              # single pixel
    
from PIL import ImageFont

big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)

with canvas(device) as draw:
    draw.text((10, 10), "Big text", font=big, fill="white")
    draw.text((10, 60), "Small text", font=small, fill="gray")    
    text = "Centered"
    box = draw.textbbox((0, 0), text, font=big)       # (left, top, right, bottom)
    w, h = box[2] - box[0], box[3] - box[1]
    draw.text(((240 - w) // 2, (240 - h) // 2), text, font=big, fill="white")

from PIL import Image
img = Image.open("photo.jpg").convert("RGB").resize((240, 240))
device.display(img)

import time
x = 0
while True:
    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, fill="black")
        draw.ellipse((x, 100, x + 40, 140), fill="red")
    x = (x + 5) % 200
    time.sleep(0.03)