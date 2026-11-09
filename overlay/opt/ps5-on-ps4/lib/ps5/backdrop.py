# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
"""The EmuFive screen behind every window (the X root window). It shows in the gaps between
windows: while a game closes, while the home screen starts again, and while the PS4 turns off or
restarts (with "Powering off..." or "Restarting...").

render() draws the screens once (with pygame) and keeps them as raw pixels; show() puts one on
the root window with Xlib alone (ctypes, no pygame), so it is quick."""

import ctypes
import ctypes.util
import os

RUNTIME = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
DIR = os.path.join(RUNTIME, "ps5-backdrop")
SCREENS = {"plain": "", "poweroff": "Powering off...", "reboot": "Restarting..."}
COLOR = (12, 10, 28)         # Also the first color of a new home screen window (ui.init_display).
TOP, BOTTOM = (26, 20, 58), (9, 7, 20)
GLOW = (124, 110, 255)


class _X:
    """The few Xlib calls used here."""

    def __init__(self):
        lib = ctypes.CDLL(ctypes.util.find_library("X11") or "libX11.so.6")
        p, ul, i, u = ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_uint
        sigs = {
            "XOpenDisplay": (p, [ctypes.c_char_p]),
            "XDefaultScreen": (i, [p]),
            "XRootWindow": (ul, [p, i]),
            "XDisplayWidth": (i, [p, i]),
            "XDisplayHeight": (i, [p, i]),
            "XDefaultDepth": (i, [p, i]),
            "XDefaultVisual": (p, [p, i]),
            "XCreatePixmap": (ul, [p, ul, u, u, u]),
            "XCreateGC": (p, [p, ul, ul, p]),
            "XFreeGC": (i, [p, p]),
            "XCreateImage": (p, [p, p, u, i, i, ctypes.c_char_p, u, u, i, i]),
            "XPutImage": (i, [p, ul, p, p, i, i, i, i, u, u]),
            "XSetWindowBackgroundPixmap": (i, [p, ul, ul]),
            "XClearWindow": (i, [p, ul]),
            "XInternAtom": (ul, [p, ctypes.c_char_p, i]),
            "XGetWindowProperty": (i, [p, ul, ul, ctypes.c_long, ctypes.c_long, i, ul,
                                       ctypes.POINTER(ul), ctypes.POINTER(i), ctypes.POINTER(ul),
                                       ctypes.POINTER(ul), ctypes.POINTER(p)]),
            "XChangeProperty": (i, [p, ul, ul, ul, i, i, p, i]),
            "XFree": (i, [p]),
            "XKillClient": (i, [p, ul]),
            "XSetCloseDownMode": (i, [p, i]),
            "XFlush": (i, [p]),
            "XSync": (i, [p, i]),
            "XCloseDisplay": (i, [p]),
        }
        for name, (res, args) in sigs.items():
            f = getattr(lib, name)
            f.restype, f.argtypes = res, args
        self.lib = lib


def screen_size():
    """The X screen's size in pixels, or None without a display."""
    x = _X().lib
    dpy = x.XOpenDisplay(None)
    if not dpy:
        return None
    try:
        scr = x.XDefaultScreen(dpy)
        return x.XDisplayWidth(dpy, scr), x.XDisplayHeight(dpy, scr)
    finally:
        x.XCloseDisplay(dpy)


def _path(name):
    return os.path.join(DIR, name + ".bgra")


def draw(w, h, text="", font="modern"):
    """One screen as a pygame surface: a dark gradient, a soft glow, the gold EMUFIVE title and
    `text` under it."""
    from . import about, ui
    pygame = ui.pygame
    pygame.font.init()
    ui.S = h / 720.0
    ui.H = 720.0
    ui.W = w / ui.S
    surface = pygame.Surface((w, h))
    for y in range(h):
        t = y / max(1, h - 1)
        pygame.draw.line(surface, ui.mix(TOP, BOTTOM, t), (0, y), (w, y))
    glow = pygame.Surface((max(1, w // 8), max(1, h // 8)))
    glow.fill((0, 0, 0))
    gw, gh = glow.get_size()
    r = int(gh * 0.55)
    for k in range(r, 0, -1):
        strength = (1 - k / r) ** 2.2 * 0.16
        pygame.draw.circle(glow, tuple(int(c * strength) for c in GLOW), (gw // 2, int(gh * 0.42)), k)
    surface.blit(pygame.transform.smoothscale(glow, (w, h)), (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    about._gold(surface, "EMUFIVE", 56, ui.W / 2, 300, "midbottom", 0.16)
    if text:
        words = ui.Text(font).render(text, 22, (206, 203, 246))
        surface.blit(words, words.get_rect(midtop=(w // 2, ui.px(330))))
    return surface


def render(size=None):
    """Draws every screen at the screen's size and keeps them in DIR (in the menu language)."""
    from . import i18n, store, ui
    pygame = ui.pygame
    size = size or screen_size()
    if not size:
        return False
    settings = store.Settings()
    i18n.set_language(settings["menu_language"])
    os.makedirs(DIR, exist_ok=True)
    for name, text in SCREENS.items():
        surface = draw(size[0], size[1], text, settings["font"])
        data = pygame.image.tobytes(surface, "BGRA") if hasattr(pygame.image, "tobytes") \
            else pygame.image.tostring(surface, "BGRA")
        tmp = _path(name) + ".tmp"
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, _path(name))
    return True


def show(name="plain"):
    """Puts a kept screen on the root window. Without it (or at another size), a plain dark color.
    The picture stays after this program ends; the one before is freed."""
    X = _X()
    x = X.lib
    dpy = x.XOpenDisplay(None)
    if not dpy:
        return False
    scr = x.XDefaultScreen(dpy)
    root = x.XRootWindow(dpy, scr)
    w, h = x.XDisplayWidth(dpy, scr), x.XDisplayHeight(dpy, scr)
    depth = x.XDefaultDepth(dpy, scr)
    try:
        with open(_path(name), "rb") as f:
            data = f.read()
    except OSError:
        data = b""
    if len(data) != w * h * 4 or depth not in (24, 32):
        data = bytes((COLOR[2], COLOR[1], COLOR[0], 255)) * (w * h)
    pixmap = x.XCreatePixmap(dpy, root, w, h, depth)
    gc = x.XCreateGC(dpy, pixmap, 0, None)
    buf = ctypes.create_string_buffer(data, len(data))
    image = x.XCreateImage(dpy, x.XDefaultVisual(dpy, scr), depth, 2, 0, buf, w, h, 32, 0)   # ZPixmap
    x.XPutImage(dpy, pixmap, gc, image, 0, 0, 0, 0, w, h)
    x.XFreeGC(dpy, gc)
    x.XSetWindowBackgroundPixmap(dpy, root, pixmap)
    x.XClearWindow(dpy, root)
    # The picture before (kept by an earlier run): free it.
    atom = x.XInternAtom(dpy, b"_EMUFIVE_BACKDROP", 0)
    kind, fmt = ctypes.c_ulong(), ctypes.c_int()
    count, after, prop = ctypes.c_ulong(), ctypes.c_ulong(), ctypes.c_void_p()
    if x.XGetWindowProperty(dpy, root, atom, 0, 1, 0, 20, ctypes.byref(kind), ctypes.byref(fmt),
                            ctypes.byref(count), ctypes.byref(after), ctypes.byref(prop)) == 0 and prop.value:
        if kind.value == 20 and fmt.value == 32 and count.value == 1:     # XA_PIXMAP
            old = ctypes.cast(prop, ctypes.POINTER(ctypes.c_ulong))[0]
            if old and old != pixmap:
                x.XKillClient(dpy, old)
        x.XFree(prop)
    value = ctypes.c_ulong(pixmap)
    x.XChangeProperty(dpy, root, atom, 20, 32, 0, ctypes.byref(value), 1)   # PropModeReplace
    x.XSetCloseDownMode(dpy, 1)      # RetainPermanent: the pixmap stays after we close.
    x.XSync(dpy, 0)
    x.XCloseDisplay(dpy)
    return True
