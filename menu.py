import os, sys, time, subprocess
from PIL import ImageFont, Image, ImageDraw
from lcd_init import device, canvas, pressed, GPIO

HERE = os.path.dirname(os.path.abspath(__file__))
LOADING_IMG = os.path.join(HERE, "images", "penguin_char.png")
SPLASH_IMG = os.path.join(HERE, "images", "dark_squid.jpg")
PY = sys.executable
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
splash_font = ImageFont.truetype(FONT,32)
title_font = ImageFont.truetype(FONT, 22)
item_font = ImageFont.truetype(FONT, 20)

# Add games here: ("Name shown", "file.py")
GAMES = [
    ("Dodge", "dodge.py"),
    ("Space Invader", "games/space_invader.py"),
    ("Screen Runner", "games/screen_runner.py")
]
#All Menu Options
ITEMS = [(n, "game", f) for n, f in GAMES] + [
    ("Power off", "off", None),
    ("Exit to shell", "exit", None),
]
#Wait for button pressed
def wait_release():
    while pressed():
        time.sleep(0.02)
#Draw splash screen
def draw_splash():
    with canvas(device) as draw:
        img = Image.open(SPLASH_IMG).convert("RGB").resize((240,240))
        device.display(img)
        time.sleep(5)
        ImageDraw.Draw(img).text((20, 100), "Mini Player",font=splash_font, fill=(220,0,100))
        device.display(img)
        time.sleep(4)
def show_loading(label="Loading..."):
    try:
        img = Image.open(LOADING_IMG).convert("RGB").resize((240,240))
    except Exception:
        message(label)    #fallback if image is missing
        return
    d = ImageDraw.Draw(img)
    d.rectangle((0,200,240,240), fill=(0,0,0))   #dark box to make font visible
    d.text((14,207), label, font=item_font, fill="white")
    device.display(img)
#Draw the start menu
def draw_menu(sel):
    with canvas(device) as d:
        d.rectangle(device.bounding_box, fill="black")
        d.text((14, 8), "GAME MENU", font=title_font, fill="yellow")
        for i, (name, _, _) in enumerate(ITEMS):
            y = 48 + i * 34
            if i == sel:
                d.rectangle((8, y - 3, 232, y + 27), fill=(40, 90, 200))
            d.text((18, y), name, font=item_font, fill="white")
        d.text((10, 218), "Up/Down  A=select", fill="gray")

def message(*lines):
    with canvas(device) as d:
        d.rectangle(device.bounding_box, fill="black")
        for i, line in enumerate(lines):
            d.text((14, 70 + i * 30), line, font=item_font, fill="white")
#Menu to confirm power off option
def confirm_off():
    message("Power off?", "A = yes", "B = cancel")
    wait_release()
    while True:
        p = pressed()
        if "BTN_A" in p:
            return True
        if "BTN_B" in p:
            return False
        time.sleep(0.02)

def release_hardware():
    GPIO.cleanup()

#Highlighted item
draw_splash()
sel = 0
wait_release()
draw_menu(sel)
prev = set()

while True:
    now = set(pressed())
    new = now - prev
    prev = now

    if "PAD_UP" in new:
        sel = (sel - 1) % len(ITEMS)
        draw_menu(sel)
    elif "PAD_DOWN" in new:
        sel = (sel + 1) % len(ITEMS)
        draw_menu(sel)
    elif "BTN_A" in new or "PAD_PRESS" in new:
        name, kind, arg = ITEMS[sel]
        if kind == "game":
            show_loading(f"Loading {name}...")
            time.sleep(2)
            print('Release hardware')
            release_hardware()
            time.sleep(2)
            print('Start subrocess')
            subprocess.run([PY, os.path.join(HERE, arg)], cwd=HERE)
            os.execv(PY, [PY] + sys.argv)       # restart the menu cleanly
        elif kind == "off":
            if confirm_off():
                message("Shutting down", "Wait ~15 sec,", "then unplug")
                subprocess.run(["shutdown", "-h", "now"])
                time.sleep(60)
            else:
                wait_release()
                draw_menu(sel)
        elif kind == "exit":
            message("Menu closed")
            sys.exit(0)

    time.sleep(0.02)
