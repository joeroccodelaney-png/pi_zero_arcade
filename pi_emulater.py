# -*- coding: utf-8 -*-
"""
dev_run.py - run the Mini_Player project on a desktop computer.

Put this file next to main.py and run:   python dev_run.py

It fakes the Raspberry Pi hardware (RPi.GPIO and the luma ST7789 LCD) so your
real main.py, mini_player.py, game_menu.py and games/*.py run unmodified.
The LCD becomes a 2x window and the buttons become keyboard keys.

Needs: Pillow and pygame (pip install pillow pygame). Tkinter ships with Python
(on Debian/Ubuntu: sudo apt install python3-tk).
"""
import os, sys, subprocess, threading

HERE = os.path.dirname(os.path.abspath(__file__))


#===== Detect Spyder / IPython / Jupyter =====#
def _in_ipython():
    mod = sys.modules.get("IPython")
    try:
        return mod is not None and mod.get_ipython() is not None
    except Exception:
        return False


#===== Run the emulator in its own process so it can never take down the Spyder kernel =====#
def _relaunch_in_new_process():
    env = dict(os.environ, MINI_PLAYER_CHILD="1", PYTHONUNBUFFERED="1")
    proc = subprocess.Popen([sys.executable, os.path.abspath(__file__)], cwd=HERE, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1, errors="replace")

    def _forward():                       # show the emulator's output in the Spyder console
        for line in proc.stdout:
            print(line, end="")

    threading.Thread(target=_forward, daemon=True).start()
    print("Emulator started in a separate process. Close its window to stop it.")


_RUN_HERE = not (_in_ipython() and os.environ.get("MINI_PLAYER_CHILD") != "1")
if not _RUN_HERE:
    _relaunch_in_new_process()

if _RUN_HERE:
    import runpy, types, time

    # Games only use pygame as an off-screen surface; keep it from opening windows.
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

    import tkinter as tk
    from PIL import Image, ImageDraw, ImageFont, ImageTk

    SCALE = 2          # window is 240*SCALE square

    #===== Keyboard -> board button mapping =====#
    KEYMAP = {
        "up": "PAD_UP", "down": "PAD_DOWN", "left": "PAD_LEFT", "right": "PAD_RIGHT",
        "space": "PAD_PRESS",
        "x": "BTN_A", "s": "BTN_B", "z": "BTN_X", "a": "BTN_Y",
        "return": "BTN_START", "escape": "BTN_SELECT", "backspace": "BTN_SELECT",
        "q": "BTN_LEFT", "w": "BTN_RIGHT",
    }


    #===== Raised inside the game loop when the emulator window is closed =====#
    class EmulatorClosed(SystemExit):
        pass


    #===== Desktop window that acts as the LCD + buttons =====#
    class Window:
        def __init__(self):
            self.closed = False
            self.root = tk.Tk()
            self.root.title("Mini Player (dev)")
            self.root.resizable(False, False)
            self.label = tk.Label(self.root, bd=0)
            self.label.pack()
            self.photo = None
            self.held = set()
            self.release_jobs = {}
            self._last_pump = 0.0
            self.root.bind("<KeyPress>", self._on_press)
            self.root.bind("<KeyRelease>", self._on_release)
            # The X button only sets a flag; the game loop notices it and exits cleanly.
            # (os._exit would kill the whole Spyder kernel, not just the emulator.)
            self.root.protocol("WM_DELETE_WINDOW", self._request_close)
            self.show(Image.new("RGB", (240, 240), "black"))
            self.root.focus_force()

        def _on_press(self, e):
            name = KEYMAP.get(e.keysym.lower())
            if not name:
                return
            job = self.release_jobs.pop(name, None)
            if job:
                self.root.after_cancel(job)
            self.held.add(name)

        def _on_release(self, e):
            name = KEYMAP.get(e.keysym.lower())
            if not name:
                return
            # Delay the release a few ms: Linux key auto-repeat sends fake release/press pairs.
            def _drop(n=name):
                self.held.discard(n)
                self.release_jobs.pop(n, None)
            self.release_jobs[name] = self.root.after(25, _drop)

        def show(self, image):
            img = image.convert("RGB").resize((240 * SCALE, 240 * SCALE), Image.NEAREST)
            # master=self.root: otherwise Tk uses the *first* root ever created, which in
            # Spyder/IPython can be a stale window from an earlier run ("pyimageN doesn't exist").
            self.photo = ImageTk.PhotoImage(img, master=self.root)
            self.label.configure(image=self.photo)
            self.root.update()
            self._check_closed()

        def pump(self):
            # Throttled event processing so key state stays fresh while polling.
            now = time.time()
            if now - self._last_pump > 0.004:
                self._last_pump = now
                self.root.update()
                self._check_closed()

        def _request_close(self):
            self.closed = True

        def _check_closed(self):
            if self.closed:
                raise EmulatorClosed(0)

        def close(self):
            """Destroy the window. Safe to call more than once."""
            self.closed = True
            try:
                self.root.destroy()
            except tk.TclError:
                pass


    window = Window()


    #===== Fake RPi.GPIO =====#
    class FakeGPIO:
        BCM, BOARD = 11, 10
        IN, OUT = 1, 0
        PUD_UP, PUD_DOWN = 22, 21
        LOW, HIGH = 0, 1

        @staticmethod
        def setmode(*a, **k): pass
        @staticmethod
        def setwarnings(*a, **k): pass
        @staticmethod
        def setup(*a, **k): pass
        @staticmethod
        def cleanup(*a, **k): pass

        @staticmethod
        def input(pin):
            window.pump()
            keys = sys.modules["mini_player"].Mini_Player.board_keys
            for name, p in keys.items():
                if p == pin:
                    return 0 if name in window.held else 1   # LOW = pressed
            return 1


    #===== Fake luma LCD pieces =====#
    class FakeSpi:
        def __init__(self, *a, **k): pass


    class FakeST7789:
        mode = "RGB"
        size = (240, 240)
        width = height = 240
        bounding_box = (0, 0, 239, 239)

        def __init__(self, *a, **k): pass

        def display(self, image):
            window.show(image)


    class canvas:
        """Same behaviour as luma.core.render.canvas."""
        def __init__(self, device, background="black", **kw):
            self.device = device
            self.image = Image.new("RGB", device.size, background)
            self.draw = ImageDraw.Draw(self.image)

        def __enter__(self):
            return self.draw

        def __exit__(self, exc_type, exc, tb):
            if exc_type is None:
                self.device.display(self.image)
            return False


    def _stub(name, **attrs):
        m = types.ModuleType(name)
        m.__dict__.update(attrs)
        sys.modules[name] = m
        return m


    _rpi = _stub("RPi")
    _rpi.GPIO = _stub("RPi.GPIO", **{k: getattr(FakeGPIO, k) for k in dir(FakeGPIO) if not k.startswith("__")})
    _stub("luma")
    _stub("luma.core")
    _stub("luma.core.interface")
    _stub("luma.core.interface.serial", spi=FakeSpi)
    _stub("luma.core.render", canvas=canvas)
    _stub("luma.lcd")
    _stub("luma.lcd.device", st7789=FakeST7789)


    #===== Font fallback (mini_player.py hardcodes a Linux font path) =====#
    _real_truetype = ImageFont.truetype

    def _truetype(font=None, size=10, *a, **k):
        try:
            return _real_truetype(font, size, *a, **k)
        except OSError:
            name = os.path.basename(str(font))
            for d in ("/usr/share/fonts/truetype/dejavu", "/Library/Fonts",
                      "/System/Library/Fonts/Supplemental", "C:/Windows/Fonts"):
                try:
                    return _real_truetype(os.path.join(d, name), size)
                except OSError:
                    pass
            alts = ["arialbd.ttf", "Arial Bold.ttf"] if "Bold" in name else ["arial.ttf", "Arial.ttf"]
            for alt in alts + ["DejaVuSans.ttf"]:
                try:
                    return _real_truetype(alt, size)
                except OSError:
                    pass
            return ImageFont.load_default(size)   # needs Pillow >= 10.1

    ImageFont.truetype = _truetype


    #===== Never actually shut the computer down =====#
    _real_run = subprocess.run

    def _run(cmd, *a, **k):
        if cmd and cmd[0] == "shutdown":
            print("[dev] 'Power off' chosen - closing the emulator instead of shutting down.")
            sys.exit(0)
        return _real_run(cmd, *a, **k)

    subprocess.run = _run


    if __name__ == "__main__":
        print("Mini Player dev emulator")
        print("  D-pad: arrow keys    PAD_PRESS: Space")
        print("  A: x   B: S   X: Z   Y: A   Start: Enter   Select: Esc/Backspace")
        print("  Left/Right shoulder: Q / W")
        print("Click the window first so it has keyboard focus.\n")
        sys.path.insert(0, HERE)
        try:
            runpy.run_path(os.path.join(HERE, "main.py"), run_name="__main__")
        except SystemExit:
            pass          # main.py's sys.exit(), "Power off", or the window's X button
        finally:
            window.close()   # always take the window down, however the program ended
            print("Emulator closed.")



