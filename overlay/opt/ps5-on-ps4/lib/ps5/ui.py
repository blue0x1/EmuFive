# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
"""Drawing for the home screen. Everything is laid out in units of a 1280x720 screen and drawn
at the screen's real resolution (S pixels per unit), so text, icons and pictures stay sharp on a
big TV. Also: text, sounds made in code, controller input and the built-in avatars."""

import array
import glob
import math
import os
import random

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
# A full-screen SDL window hides itself when another window takes the focus (the screenshot
# notice, say), and the kiosk window manager never shows it again: a black screen.
os.environ.setdefault("SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS", "0")
import pygame  # noqa: E402

from ps5 import i18n  # noqa: E402

W, H = 1280.0, 720.0       # The layout's size in units (W follows the screen's shape).
S = 1.0                    # Pixels per unit.

# Colors. apply_theme() sets them from the Appearance settings before the home screen draws
# (the home screen restarts when the theme changes). WHITE is the main text and button color and
# INK the text on it; in the Light theme the two swap. ART_TEXT is text over the games' pictures.
WHITE = (255, 255, 255)
SOFT = (206, 203, 246)
DIM = (150, 148, 180)
INK = (20, 18, 46)
PANEL = (24, 22, 52)
PANEL_LINE = (70, 66, 120)
ROW_ON = (60, 56, 120)
KEY = (44, 41, 86)
KEY_ON = (90, 84, 170)
GOOD = (46, 200, 130)
BAD = (255, 170, 170)
GOLD = (255, 205, 90)
BACKDROP = (14, 12, 34)
DIALOG = (30, 28, 64)
ACCENT = (124, 110, 255)
ART_TEXT = (255, 255, 255)
ART_SOFT = (206, 203, 246)

ACCENTS = {
    "purple": ("Purple", (124, 110, 255)),
    "ocean": ("Ocean blue", (40, 150, 255)),
    "spartan": ("Spartan red and gold", (196, 52, 40)),
    "emerald": ("Emerald", (40, 190, 120)),
    "sunset": ("Sunset orange", (255, 130, 50)),
    "rose": ("Rose", (240, 90, 150)),
    "mono": ("Monochrome", (170, 170, 182)),
}
THEMES = {"dark": "Dark", "midnight": "Midnight (pure black)", "light": "Light"}


def mix(a, b, t):
    """Color a mixed toward b by t (0..1)."""
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def apply_theme(theme="dark", accent="purple"):
    global WHITE, SOFT, DIM, INK, PANEL, PANEL_LINE, ROW_ON, KEY, KEY_ON, BACKDROP, DIALOG, ACCENT, GOLD
    global ART_SOFT
    a = ACCENTS.get(accent, ACCENTS["purple"])[1]
    ACCENT = a
    GOLD = (255, 205, 90) if accent != "spartan" else (240, 190, 90)
    ART_SOFT = mix(a, (236, 236, 246), 0.78)
    if theme == "light":
        WHITE, INK = (26, 24, 40), (255, 255, 255)
        SOFT, DIM = (78, 76, 100), (128, 126, 150)
        BACKDROP, PANEL, DIALOG = (232, 232, 240), (246, 246, 250), (252, 252, 255)
        PANEL_LINE, KEY = (204, 204, 218), (226, 226, 236)
        KEY_ON, ROW_ON = mix(a, (226, 226, 236), 0.45), mix(a, (246, 246, 250), 0.78)
    elif theme == "midnight":
        WHITE, INK = (255, 255, 255), (8, 8, 12)
        SOFT, DIM = mix(a, (230, 230, 240), 0.8), mix(a, (140, 140, 150), 0.75)
        BACKDROP, PANEL, DIALOG = (0, 0, 0), (8, 8, 10), (16, 16, 20)
        PANEL_LINE, KEY = mix(a, (34, 34, 40), 0.7), (26, 26, 32)
        KEY_ON, ROW_ON = mix(a, (26, 26, 32), 0.5), mix(a, (16, 16, 20), 0.75)
    else:
        WHITE, INK = (255, 255, 255), mix(a, (10, 10, 22), 0.85)
        SOFT, DIM = mix(a, (236, 236, 246), 0.75), mix(a, (150, 150, 168), 0.6)
        BACKDROP, PANEL, DIALOG = mix(a, (10, 10, 20), 0.9), mix(a, (16, 16, 28), 0.84), mix(a, (20, 20, 34), 0.76)
        PANEL_LINE, KEY = mix(a, (24, 24, 36), 0.5), mix(a, (22, 22, 36), 0.7)
        KEY_ON, ROW_ON = mix(a, (40, 40, 60), 0.3), mix(a, (24, 24, 38), 0.62)


def px(v):
    return int(round(v * S))


def init_display(size=None, windowed=False, overscan=0):
    """Opens the screen at its own resolution (or `size` for testing) and sets W and S. Returns
    (the screen, the area to draw in): with `overscan` percent, a smaller area in the middle, for
    TVs that cut off the edges."""
    global W, H, S
    pygame.init()
    if size is None:
        info = pygame.display.Info()
        size = (info.current_w or 1280, info.current_h or 720)
    flags = 0 if windowed else pygame.FULLSCREEN
    try:
        screen = pygame.display.set_mode(size, flags, vsync=1)
    except pygame.error:
        screen = pygame.display.set_mode(size, flags)
    # Dark at once (the color of the screen behind the windows, ps5-backdrop): a new window is
    # white until its first frame, which comes only after the games and pictures are loaded.
    screen.fill((12, 10, 28))
    pygame.display.flip()
    real_w, real_h = screen.get_size()
    area = screen
    if overscan:
        mx, my = int(real_w * overscan / 200), int(real_h * overscan / 200)
        area = screen.subsurface(pygame.Rect(mx, my, real_w - 2 * mx, real_h - 2 * my))
        real_w, real_h = area.get_size()
    S = real_h / 720.0
    H = 720.0
    W = real_w / S
    return screen, area


# --------------------------------------------------------------------------------------------
# Fonts and text.

def find_font(style):
    """Inter in any of the file layouts Debian has used, else None."""
    for pattern in (f"/usr/share/fonts/*/inter/Inter-{style}.*", f"/usr/share/fonts/*/inter/Inter*{style}*.*"):
        found = sorted(glob.glob(pattern))
        if found:
            return found[0]
    return None


def first_existing(paths):
    for path in paths:
        if os.path.exists(path):
            return path
    return None


FONTS = {"modern": "Modern (Inter)", "classic": "Classic (serif)", "retro": "Retro (pixel)"}


ARABIC_FONTS = ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")


class Text:
    """Cached text, sized in layout units. style: modern, classic or retro; scale: text size.
    Text is translated to the menu language here (i18n). Arabic uses DejaVu Sans (the other fonts
    have no Arabic letters), joined and in display order (i18n.visual): SDL_ttf here draws each
    letter alone and left to right."""

    def __init__(self, style="modern", scale=1.0):
        self.scale = scale
        self.smooth = style != "retro"
        if style == "classic":
            self.regular = first_existing(["/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"])
            self.bold = first_existing(["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"])
        elif style == "retro":
            self.regular = self.bold = first_existing(
                ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"])
        else:
            self.regular = self.bold = None
        self.regular = self.regular or find_font("Regular") or first_existing([
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
        self.bold = self.bold or find_font("SemiBold") or first_existing([
            "/usr/share/fonts/truetype/noto/NotoSans-SemiBold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]) or self.regular
        self.fonts = {}
        self.cache = {}

    def font(self, size, bold=False, arabic=False):
        key = (size, bold, arabic)
        if key not in self.fonts:
            path = ARABIC_FONTS[1 if bold else 0] if arabic else self.bold if bold else self.regular
            if arabic and not os.path.exists(path):
                path = self.bold if bold else self.regular
            self.fonts[key] = pygame.font.Font(path, max(6, px(size * self.scale)))
        return self.fonts[key]

    def render(self, text, size, color=None, bold=False):
        text = i18n.translate(text)
        color = WHITE if color is None else color
        key = (text, size, color, bold)
        surface = self.cache.get(key)
        if surface is None:
            if len(self.cache) > 900:
                self.cache.clear()
            if i18n.has_rtl(text):
                surface = self.font(size, bold, True).render(i18n.visual(text), True, color)
            else:
                surface = self.font(size, bold).render(text, self.smooth, color)
            self.cache[key] = surface
        return surface

    def width(self, text, size, bold=False):
        text = i18n.translate(text)
        if i18n.has_rtl(text):
            return self.font(size, bold, True).size(i18n.visual(text))[0] / S
        return self.font(size, bold).size(text)[0] / S

    def fit(self, text, size, width, bold=False):
        """The text, cut with an ellipsis to fit `width` units."""
        text = i18n.Final(i18n.translate(text))
        if self.width(text, size, bold) <= width:
            return text
        while text and self.width(text + "…", size, bold) > width:
            text = text[:-1]
        return i18n.Final(text + "…")

    def wrap(self, text, size, width, bold=False):
        text = i18n.translate(text)
        lines, line = [], ""
        for word in text.split():
            test = (line + " " + word).strip()
            if self.width(test, size, bold) <= width or not line:
                line = test
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
        return [i18n.Final(line) for line in lines]


# --------------------------------------------------------------------------------------------
# Canvas: drawing in layout units.

ALPHA_RECTS = {}

# Smooth edges. pygame draws shapes with hard, stepped edges, which show on a big TV. Shapes are
# drawn 4 times larger and scaled down (edge pixels get partial light), and kept: the corners of
# rounded rectangles, and small icon pieces (circles, arcs, lines, polygons).
SMOOTH = 4
SMOOTH_SPRITES = {}


def _keep(key, make):
    sprite = SMOOTH_SPRITES.get(key)
    if sprite is None:
        if len(SMOOTH_SPRITES) > 700:
            SMOOTH_SPRITES.clear()
        sprite = SMOOTH_SPRITES[key] = make()
    return sprite


def _smooth(size, draw, color):
    """A sprite of `size` pixels: draw(big surface, factor) in white at 4x, scaled down, in color."""
    w, h = max(1, size[0]), max(1, size[1])
    big = pygame.Surface((w * SMOOTH, h * SMOOTH), pygame.SRCALPHA)
    big.fill((255, 255, 255, 0))          # Clear white: no dark fringe when scaled down.
    draw(big, SMOOTH)
    sprite = pygame.transform.smoothscale(big, (w, h))
    color = tuple(color) + ((255,) if len(color) == 3 else ())
    if color != (255, 255, 255, 255):
        tint = pygame.Surface((w, h), pygame.SRCALPHA)
        tint.fill(color)
        sprite.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return sprite


def _corners(radius, width, color):
    """The corners (top left, top right, bottom left, bottom right) of a smooth rounded rectangle."""
    def make():
        side = radius * 2
        disc = _smooth((side, side), lambda big, k: pygame.draw.rect(
            big, (255, 255, 255, 255), big.get_rect(), width * k, border_radius=radius * k), color)
        return [disc.subsurface((x, y, radius, radius)) for y in (0, radius) for x in (0, radius)]
    return _keep(("corners", radius, width, tuple(color)), make)


def draw_round(surface, color, rect, radius, width=0, replace=False):
    """A rounded rectangle (`width` 0: filled) with smooth corners, in pixels. `replace`: on a
    see-through layer or mask, the corners replace what is there instead of being drawn over it."""
    rect = pygame.Rect(rect)
    radius = max(0, min(int(radius), rect.w // 2, rect.h // 2))
    if radius < 2 or (width and width >= radius):
        pygame.draw.rect(surface, color, rect, width, border_radius=radius)
        return
    x, y, w, h, r = rect.x, rect.y, rect.w, rect.h, radius
    if width:
        for part in ((x + r, y, w - 2 * r, width), (x + r, y + h - width, w - 2 * r, width),
                     (x, y + r, width, h - 2 * r), (x + w - width, y + r, width, h - 2 * r)):
            if part[2] > 0 and part[3] > 0:
                pygame.draw.rect(surface, color, part)
    else:
        for part in ((x, y + r, w, h - 2 * r), (x + r, y, w - 2 * r, r), (x + r, y + h - r, w - 2 * r, r)):
            if part[2] > 0 and part[3] > 0:
                pygame.draw.rect(surface, color, part)
    tl, tr, bl, br = _corners(r, width, color)
    for piece, at in ((tl, (x, y)), (tr, (x + w - r, y)), (bl, (x, y + h - r)), (br, (x + w - r, y + h - r))):
        if replace:
            surface.fill(tuple(color[:3]) + (0,), (at, (r, r)))     # Its color, clear: no dark edge.
        surface.blit(piece, at)


def round_mask(w, h, radius, width=0):
    """A white mask (alpha) of a rounded rectangle with smooth edges, to cut pictures with
    BLEND_RGBA_MIN or BLEND_RGBA_MULT."""
    mask = pygame.Surface((max(1, w), max(1, h)), pygame.SRCALPHA)
    mask.fill((255, 255, 255, 0))
    draw_round(mask, (255, 255, 255, 255), (0, 0, w, h), radius, width, True)
    return mask


def circle_mask(size):
    """A white mask (alpha) of a circle `size` pixels across, with a smooth edge."""
    return _keep(("circle mask", size), lambda: _smooth((size, size), lambda big, k: pygame.draw.circle(
        big, (255, 255, 255, 255), (size * k // 2, size * k // 2), size * k // 2), (255, 255, 255)))



class Canvas:
    def __init__(self, surface, text):
        self.s = surface
        self.t = text
        self._alpha_cache = {}

    def rect(self, color, x, y, w, h, radius=0, width=0):
        r = pygame.Rect(px(x), px(y), max(1, px(x + w) - px(x)), max(1, px(y + h) - px(y)))
        if len(color) == 4 and color[3] < 255:
            # See-through rectangles are made once and kept (the PS4's CPU is slow).
            key = (r.size, tuple(color), px(radius), px(width) if width else 0)
            layer = ALPHA_RECTS.get(key)
            if layer is None:
                layer = pygame.Surface(r.size, pygame.SRCALPHA)
                layer.fill(tuple(color[:3]) + (0,))
                draw_round(layer, color, layer.get_rect(), px(radius), max(0, px(width)) if width else 0, True)
                if len(ALPHA_RECTS) > 400:
                    ALPHA_RECTS.clear()
                ALPHA_RECTS[key] = layer
            self.s.blit(layer, r.topleft)
        else:
            draw_round(self.s, color[:3], r, px(radius), max(1, px(width)) if width else 0)
        return r

    # Circles, lines, polygons and arcs: smooth sprites, kept by shape and color. A shape's
    # position keeps its fraction of a pixel (in 1/4 pixels), so it sits where it should.

    def _piece(self, color, key, left, top, right, bottom, draw):
        """Draws a smooth shape over the pixel box (left, top)-(right, bottom); draw(big, k, ox, oy)
        draws it 4x larger, with (ox, oy) the box's corner in big pixels."""
        x0, y0 = int(math.floor(left)) - 1, int(math.floor(top)) - 1
        x1, y1 = int(math.ceil(right)) + 2, int(math.ceil(bottom)) + 2
        fx, fy = round((left - x0) * SMOOTH), round((top - y0) * SMOOTH)
        size = (x1 - x0, y1 - y0)
        sprite = _keep(key + (size, fx, fy, tuple(color)),
                       lambda: _smooth(size, lambda big, k: draw(big, k, fx, fy), color))
        self.s.blit(sprite, (x0, y0))

    def circle(self, color, x, y, r, width=0, fast=False):
        """`fast`: plain pygame (for things that move and change color every frame, the orbs)."""
        thick = max(1, px(width)) if width else 0
        if fast:
            pygame.draw.circle(self.s, color[:3], (px(x), px(y)), max(1, px(r)), thick)
            return
        cx, cy, radius = x * S, y * S, max(1.0, r * S)
        self._piece(color, ("circle", round(radius * SMOOTH), thick), cx - radius, cy - radius,
                    cx + radius, cy + radius,
                    lambda big, k, ox, oy: pygame.draw.circle(
                        big, (255, 255, 255, 255), (ox + round(radius * k), oy + round(radius * k)),
                        round(radius * k), thick * k))

    def line(self, color, x1, y1, x2, y2, width=1):
        a, b = (x1 * S, y1 * S), (x2 * S, y2 * S)
        thick = max(1, px(width))
        left, top = min(a[0], b[0]) - thick, min(a[1], b[1]) - thick
        right, bottom = max(a[0], b[0]) + thick, max(a[1], b[1]) + thick
        rel = (round((a[0] - left) * SMOOTH), round((a[1] - top) * SMOOTH),
               round((b[0] - left) * SMOOTH), round((b[1] - top) * SMOOTH))
        self._piece(color, ("line", rel, thick), left, top, right, bottom,
                    lambda big, k, ox, oy: pygame.draw.line(
                        big, (255, 255, 255, 255), (ox + rel[0], oy + rel[1]), (ox + rel[2], oy + rel[3]),
                        thick * k))

    def polygon(self, color, points, width=0):
        pts = [(x * S, y * S) for x, y in points]
        left, top = min(p[0] for p in pts), min(p[1] for p in pts)
        right, bottom = max(p[0] for p in pts), max(p[1] for p in pts)
        rel = tuple((round((p[0] - left) * SMOOTH), round((p[1] - top) * SMOOTH)) for p in pts)
        thick = max(1, px(width)) if width else 0
        self._piece(color, ("polygon", rel, thick), left, top, right, bottom,
                    lambda big, k, ox, oy: pygame.draw.polygon(
                        big, (255, 255, 255, 255), [(ox + p[0], oy + p[1]) for p in rel], thick * k))

    def arc(self, color, x, y, w, h, start, stop, width=1):
        thick = max(1, px(width))
        left, top, ww, hh = x * S, y * S, w * S, h * S
        size = (round(ww * SMOOTH), round(hh * SMOOTH))
        self._piece(color, ("arc", size, round(start, 3), round(stop, 3), thick), left, top,
                    left + ww, top + hh,
                    lambda big, k, ox, oy: pygame.draw.arc(
                        big, (255, 255, 255, 255), pygame.Rect(ox, oy, size[0], size[1]), start, stop,
                        thick * k))

    def blit(self, surface, x, y, anchor="topleft"):
        r = surface.get_rect(**{anchor: (px(x), px(y))})
        self.s.blit(surface, r)
        return r

    def text(self, text, size, x, y, color=None, bold=False, anchor="topleft", shadow=False):
        """Draws text at (x, y) units; returns its width in units."""
        if not text:
            return 0
        surface = self.t.render(text, size, WHITE if color is None else color, bold)
        if shadow:
            under = self.t.render(text, size, (0, 0, 0), bold)
            r = under.get_rect(**{anchor: (px(x) + max(1, px(2)), px(y) + max(1, px(2)))})
            self.s.blit(under, r)
        self.blit(surface, x, y, anchor)
        return surface.get_width() / S

    def dim(self, alpha, color=(6, 5, 16)):
        """A dark veil over everything (cached: an alpha blit of a plain surface)."""
        size = self.s.get_size()
        key = (size, color)
        veil = self._alpha_cache.get(key)
        if veil is None:
            veil = pygame.Surface(size)
            veil.fill(color)
            self._alpha_cache[key] = veil
        veil.set_alpha(max(0, min(255, int(alpha))))
        self.s.blit(veil, (0, 0))


# --------------------------------------------------------------------------------------------
# Sounds, made here (no files): a tick when moving, a chime when choosing, a low note back.

SOUND_STYLES = {"crystal": "Crystal", "chimes": "Soft chimes", "clicks": "Clicks", "retro": "Retro 8-bit"}
# Recorded styles: WAV files (made in code, not samples) in share/sounds/<style>/.
SOUND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "share", "sounds")


class Sounds:
    """Menu sounds, made here: style chimes, clicks or retro; volume 0-100; on or off."""

    def __init__(self, style="chimes", volume=100, enabled=True):
        self.ok = False
        self.enabled = enabled
        try:
            pygame.mixer.init(44100, -16, 1, 512)
            self.ok = True
        except pygame.error:
            return
        self.style = style
        v = max(0, min(100, volume)) / 100
        if style == "crystal" and self.load_style(style, v):
            pass
        elif style == "clicks":
            self.move = self.tone([(2600, 0.012)], 0.22 * v, "click")
            self.select = self.tone([(1800, 0.018), (2600, 0.02)], 0.25 * v, "click")
            self.back = self.tone([(1400, 0.02)], 0.22 * v, "click")
            self.error = self.tone([(500, 0.05), (380, 0.06)], 0.25 * v, "click")
        elif style == "retro":
            self.move = self.tone([(990, 0.03)], 0.12 * v, "square")
            self.select = self.tone([(660, 0.05), (990, 0.05), (1320, 0.08)], 0.12 * v, "square")
            self.back = self.tone([(880, 0.04), (660, 0.06)], 0.12 * v, "square")
            self.error = self.tone([(220, 0.1), (180, 0.14)], 0.12 * v, "square")
        else:
            self.move = self.tone([(1760, 0.035)], 0.18 * v)
            self.select = self.tone([(880, 0.06), (1318, 0.12)], 0.22 * v)
            self.back = self.tone([(660, 0.05), (440, 0.08)], 0.2 * v)
            self.error = self.tone([(300, 0.12), (220, 0.18)], 0.22 * v)
        self.test = self.tone([(523, 0.18), (659, 0.18), (784, 0.18), (1046, 0.4)], 0.3)
        self.shutter = self.tone([(3000, 0.015), (1500, 0.03)], 0.25 * max(v, 0.4), "click")

    @staticmethod
    def tone(notes, volume, wave="sine"):
        rate = 44100
        samples = array.array("h")
        for frequency, length in notes:
            count = int(rate * length)
            for n in range(count):
                t = n / rate
                envelope = math.exp(-t * 18 / max(1.0, length * 8)) * min(1.0, n / 120)
                phase = math.sin(2 * math.pi * frequency * t)
                if wave == "square":
                    phase = 0.6 if phase >= 0 else -0.6
                elif wave == "click":
                    envelope = math.exp(-t * 260) * min(1.0, n / 20)
                samples.append(int(32767 * volume * envelope * phase))
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def load_style(self, style, volume):
        """Loads a recorded style; False when its files are missing (then chimes are used)."""
        sounds = {}
        for name in ("move", "select", "back", "error"):
            try:
                sound = pygame.mixer.Sound(os.path.join(SOUND_DIR, style, name + ".wav"))
            except (pygame.error, FileNotFoundError):
                return False
            sound.set_volume(volume)
            sounds[name] = sound
        for name, sound in sounds.items():
            setattr(self, name, sound)
        return True

    def play(self, name):
        if self.ok and (self.enabled or name == "test"):
            getattr(self, name).play()


# --------------------------------------------------------------------------------------------
# Input: keyboard and controllers, turned into a few actions.

LEFT, RIGHT, UP, DOWN, OK, BACK, SQUARE, TRIANGLE, OPTIONS, GUIDE, PAGE_UP, PAGE_DOWN = range(12)


class Input:
    """swap: X and O swapped (Button layout setting). The PS button acts when it is released, and
    not at all when another button was pressed while it was held (PS + Square: a screenshot)."""
    REPEAT_DELAY, REPEAT_RATE = 0.35, 0.09

    def __init__(self, swap=False, rumble=True, strength=100):
        self.swap = swap
        self.rumble_on = rumble
        self.strength = max(0, min(100, strength)) / 100
        self.guide_down = False
        self.guide_combo = False
        self.pads = {}
        self.held = {}        # Direction -> time of next repeat.
        self.stick = [0.0, 0.0]
        self.typed = []
        self.last_input = 0.0
        try:
            from pygame._sdl2 import controller
            controller.init()
            self.controller = controller
        except (ImportError, pygame.error):
            self.controller = None

    def pad_count(self):
        return len(self.pads)

    def rumble(self):
        if not self.rumble_on or not self.strength:
            return
        for pad in self.pads.values():
            try:
                pad.rumble(0, 0.12 * self.strength, 35)
            except (pygame.error, AttributeError):
                pass

    def handle(self, event, now):
        actions = []
        if event.type == pygame.KEYDOWN:
            keys = {pygame.K_LEFT: LEFT, pygame.K_RIGHT: RIGHT, pygame.K_UP: UP, pygame.K_DOWN: DOWN,
                    pygame.K_RETURN: OK, pygame.K_KP_ENTER: OK, pygame.K_ESCAPE: BACK,
                    pygame.K_BACKSPACE: SQUARE, pygame.K_TAB: TRIANGLE, pygame.K_F1: OPTIONS,
                    pygame.K_HOME: GUIDE, pygame.K_PAGEUP: PAGE_UP, pygame.K_PAGEDOWN: PAGE_DOWN}
            if event.key in keys:
                actions.append(keys[event.key])
        elif event.type == pygame.TEXTINPUT:
            self.typed.append(event.text)
        elif self.controller is not None and event.type == pygame.CONTROLLERDEVICEADDED:
            try:
                pad = self.controller.Controller(event.device_index)
                self.pads[pad.as_joystick().get_instance_id()] = pad
            except pygame.error:
                pass
        elif event.type == pygame.CONTROLLERDEVICEREMOVED:
            self.pads.pop(event.instance_id, None)
        elif event.type == pygame.CONTROLLERBUTTONDOWN:
            buttons = {pygame.CONTROLLER_BUTTON_DPAD_LEFT: LEFT, pygame.CONTROLLER_BUTTON_DPAD_RIGHT: RIGHT,
                       pygame.CONTROLLER_BUTTON_DPAD_UP: UP, pygame.CONTROLLER_BUTTON_DPAD_DOWN: DOWN,
                       pygame.CONTROLLER_BUTTON_A: OK, pygame.CONTROLLER_BUTTON_B: BACK,
                       pygame.CONTROLLER_BUTTON_X: SQUARE, pygame.CONTROLLER_BUTTON_Y: TRIANGLE,
                       pygame.CONTROLLER_BUTTON_START: OPTIONS, pygame.CONTROLLER_BUTTON_GUIDE: GUIDE,
                       pygame.CONTROLLER_BUTTON_LEFTSHOULDER: PAGE_UP,
                       pygame.CONTROLLER_BUTTON_RIGHTSHOULDER: PAGE_DOWN}
            action = buttons.get(event.button)
            if self.swap and action in (OK, BACK):
                action = BACK if action == OK else OK
            if action == GUIDE:
                self.guide_down, self.guide_combo = True, False
                action = None
            elif self.guide_down and action is not None:
                self.guide_combo = True       # PS + this button: not for the menus.
                action = None
            if action is not None:
                actions.append(action)
                if action in (LEFT, RIGHT, UP, DOWN):
                    self.held[action] = now + self.REPEAT_DELAY
        elif event.type == pygame.CONTROLLERBUTTONUP and event.button == pygame.CONTROLLER_BUTTON_GUIDE:
            if self.guide_down and not self.guide_combo:
                actions.append(GUIDE)
            self.guide_down = False
        elif event.type == pygame.CONTROLLERBUTTONUP:
            directions = {pygame.CONTROLLER_BUTTON_DPAD_LEFT: LEFT, pygame.CONTROLLER_BUTTON_DPAD_RIGHT: RIGHT,
                          pygame.CONTROLLER_BUTTON_DPAD_UP: UP, pygame.CONTROLLER_BUTTON_DPAD_DOWN: DOWN}
            self.held.pop(directions.get(event.button), None)
        elif event.type == pygame.CONTROLLERAXISMOTION and event.axis in (
                pygame.CONTROLLER_AXIS_LEFTX, pygame.CONTROLLER_AXIS_LEFTY):
            index = 0 if event.axis == pygame.CONTROLLER_AXIS_LEFTX else 1
            value = event.value / 32767.0
            before = self.stick[index]
            self.stick[index] = value
            minus, plus = (LEFT, RIGHT) if index == 0 else (UP, DOWN)
            for direction, active, was in ((minus, value < -0.6, before < -0.6),
                                           (plus, value > 0.6, before > 0.6)):
                if active and not was:
                    actions.append(direction)
                    self.held[direction] = now + self.REPEAT_DELAY
                elif was and not active:
                    self.held.pop(direction, None)
            if abs(value) > 0.6:
                self.last_input = now
        if actions or event.type == pygame.TEXTINPUT:
            self.last_input = now
        return actions

    def repeats(self, now):
        actions = []
        for direction, when in list(self.held.items()):
            if now >= when:
                actions.append(direction)
                self.held[direction] = now + self.REPEAT_RATE
        return actions


# --------------------------------------------------------------------------------------------
# Icons, drawn (no files, no Sony artwork).

def draw_wifi(c, x, y, color, bars):
    """A Wi-Fi symbol with `bars` of 3 lit; its dot sits at (x, y)."""
    c.circle(color if bars > 0 else DIM, x, y, 3)
    for i in range(3):
        r = 8 + i * 6
        c.arc(color if bars > i + 1 else DIM, x - r, y - r, r * 2, r * 2, math.radians(50), math.radians(130), 3)


def draw_pad(c, x, y, color):
    """A small controller symbol centered at (x, y)."""
    c.rect(color, x - 13, y - 7, 26, 14, 7, 2)
    c.line(color, x - 8, y, x - 4, y, 2)
    c.line(color, x - 6, y - 2, x - 6, y + 2, 2)
    c.circle(color, x + 6, y, 2)


def draw_gear(c, x, y, color, r=11):
    for i in range(8):
        a = i * math.pi / 4
        c.line(color, x + math.cos(a) * (r - 3), y + math.sin(a) * (r - 3),
               x + math.cos(a) * (r + 2), y + math.sin(a) * (r + 2), 4)
    c.circle(color, x, y, r - 2, 3)
    c.circle(color, x, y, 3)


def draw_power(c, x, y, radius, color, width=4):
    c.arc(color, x - radius, y - radius, radius * 2, radius * 2, math.radians(120), math.radians(420), width)
    c.line(color, x, y - radius - 2, x, y - 2, width)


def draw_globe(c, x, y, radius, color, width=4):
    """The Internet tile: a globe with its meridians and parallels."""
    c.circle(color, x, y, radius, width)
    c.arc(color, x - radius * 0.45, y - radius, radius * 0.9, radius * 2, 0, math.pi * 2, max(1, width - 1))
    c.line(color, x, y - radius, x, y + radius, max(1, width - 1))
    c.line(color, x - radius, y, x + radius, y, max(1, width - 1))
    for dy in (-0.5, 0.5):
        half = radius * math.sqrt(1 - dy * dy) * 0.96
        c.line(color, x - half, y + dy * radius, x + half, y + dy * radius, max(1, width - 1))


BATTERY_HIGH, BATTERY_MID, BATTERY_LOW = (60, 205, 110), (240, 200, 60), (235, 70, 70)


def draw_battery(c, x, y, percent, color, charging=False):
    """A battery 24 units wide at (x, y) top-left. The fill is green above 50%, yellow from 16 to
    50% and red at 15% or less; charging adds a small lightning bolt on its left."""
    c.rect(color, x, y, 22, 12, 3, 2)
    c.rect(color, x + 22, y + 3, 3, 6, 1)
    if percent is not None:
        fill = max(0.0, min(1.0, percent / 100))
        inner = BATTERY_HIGH if percent > 50 else BATTERY_MID if percent > 15 else BATTERY_LOW
        if fill > 0:
            c.rect(inner, x + 3, y + 3, max(1.5, 16 * fill), 6, 1)
    if charging:
        c.polygon(BATTERY_MID, [(x - 4, y - 1), (x - 10, y + 7), (x - 6, y + 7), (x - 8, y + 13),
                                (x - 2, y + 4), (x - 6, y + 4)])


def draw_star(c, x, y, r, color):
    points = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        points.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    c.polygon(color, points)


def draw_lock(c, x, y, color):
    c.rect(color, x - 7, y, 14, 11, 2)
    c.arc(color, x - 5, y - 8, 10, 14, 0, math.pi, 2)


def draw_button(c, kind, x, y, size=11):
    """PlayStation face button symbols, drawn: cross, circle, square, triangle, options, ps, l1r1."""
    c.circle((60, 58, 92), x, y, size)
    s = size * 0.48
    if kind == "cross":
        c.line((150, 180, 255), x - s, y - s, x + s, y + s, 2)
        c.line((150, 180, 255), x - s, y + s, x + s, y - s, 2)
    elif kind == "circle":
        c.circle((255, 120, 140), x, y, s + 1, 2)
    elif kind == "square":
        c.rect((240, 150, 220), x - s, y - s, s * 2, s * 2, 0, 2)
    elif kind == "triangle":
        c.polygon((120, 230, 200), [(x, y - s - 1), (x - s - 1, y + s), (x + s + 1, y + s)], 2)
    elif kind == "options":
        for dy in (-3, 0, 3):
            c.line(WHITE, x - 5, y + dy, x + 5, y + dy, 1)
    elif kind == "ps":
        c.text("PS", 9, x, y, WHITE, True, "center")
    elif kind == "l1r1":
        c.text("L1R1", 7, x, y, WHITE, True, "center")


def draw_hints(c, hints, x=64, y=None, soft=None, dim=None):
    """Button hints along the bottom: [(button, label)]; a button of None is plain text. The
    colors are the theme's, or `soft` and `dim` (over the game's art)."""
    y = H - 37 if y is None else y
    for kind, label in hints:
        if kind is None:
            x += c.text(label, 15, x, y - 9, dim or DIM) + 30
            continue
        draw_button(c, kind, x + 11, y)
        x += c.text(label, 15, x + 28, y - 9, soft or SOFT) + 58


def rounded_image(surface, size_px, radius_px):
    """A copy of `surface` scaled to a square of size_px with rounded corners."""
    tile = pygame.transform.smoothscale(surface, (size_px, size_px)).convert_alpha()
    tile.blit(round_mask(size_px, size_px, radius_px), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return tile


def circle_image(surface, size_px):
    """A copy of `surface`, center-cropped to a square, scaled and cut to a circle."""
    w, h = surface.get_size()
    side = min(w, h)
    square = surface.subsurface(pygame.Rect((w - side) // 2, (h - side) // 2, side, side))
    image = pygame.transform.smoothscale(square, (size_px, size_px)).convert_alpha()
    image.blit(circle_mask(size_px), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return image


# --------------------------------------------------------------------------------------------
# Built-in avatars: a soft two-color background and a shape, all drawn here.

AVATAR_COLORS = [
    ((88, 80, 236), (190, 90, 240)), ((20, 160, 200), (60, 90, 220)), ((240, 110, 90), (250, 190, 80)),
    ((40, 180, 120), (20, 110, 160)), ((230, 70, 140), (120, 60, 220)), ((70, 70, 90), (140, 140, 170)),
    ((250, 160, 60), (230, 70, 80)), ((30, 120, 90), (140, 210, 90)), ((60, 40, 120), (20, 160, 220)),
    ((200, 60, 60), (90, 20, 60)), ((90, 170, 250), (200, 230, 255)), ((140, 90, 60), (230, 170, 110)),
]
AVATAR_SHAPES = ["cross", "circle", "square", "triangle", "star", "heart",
                 "moon", "bolt", "note", "crown", "leaf", "diamond"]
BUILTIN_AVATARS = len(AVATAR_SHAPES)


def builtin_avatar(index, size_px):
    """A built-in avatar, drawn 4 times larger and scaled down for smooth edges."""
    big = _builtin_avatar(index, size_px * SMOOTH)
    return pygame.transform.smoothscale(big, (size_px, size_px))


def _builtin_avatar(index, size_px):
    index %= BUILTIN_AVATARS
    a, b = AVATAR_COLORS[index]
    surface = pygame.Surface((size_px, size_px), pygame.SRCALPHA)
    for y in range(size_px):
        t = y / max(1, size_px - 1)
        color = tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
        pygame.draw.line(surface, color, (0, y), (size_px, y))
    shape = AVATAR_SHAPES[index]
    s = size_px
    cx = cy = s / 2
    r = s * 0.24
    white = (255, 255, 255, 235)
    w = max(2, int(s * 0.06))
    if shape == "cross":
        pygame.draw.line(surface, white, (cx - r, cy - r), (cx + r, cy + r), w)
        pygame.draw.line(surface, white, (cx - r, cy + r), (cx + r, cy - r), w)
    elif shape == "circle":
        pygame.draw.circle(surface, white, (int(cx), int(cy)), int(r), w)
    elif shape == "square":
        pygame.draw.rect(surface, white, pygame.Rect(cx - r, cy - r, 2 * r, 2 * r), w)
    elif shape == "triangle":
        pygame.draw.polygon(surface, white, [(cx, cy - r * 1.1), (cx - r * 1.1, cy + r * 0.8),
                                             (cx + r * 1.1, cy + r * 0.8)], w)
    elif shape == "star":
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rr = r * 1.15 if i % 2 == 0 else r * 0.5
            pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
        pygame.draw.polygon(surface, white, pts)
    elif shape == "heart":
        pygame.draw.circle(surface, white, (int(cx - r * 0.5), int(cy - r * 0.2)), int(r * 0.55))
        pygame.draw.circle(surface, white, (int(cx + r * 0.5), int(cy - r * 0.2)), int(r * 0.55))
        pygame.draw.polygon(surface, white, [(cx - r * 1.02, cy - r * 0.05), (cx + r * 1.02, cy - r * 0.05),
                                             (cx, cy + r * 1.05)])
    elif shape == "moon":
        pygame.draw.circle(surface, white, (int(cx), int(cy)), int(r * 1.05))
        pygame.draw.circle(surface, (0, 0, 0, 0), (int(cx + r * 0.45), int(cy - r * 0.3)), int(r * 0.9))
    elif shape == "bolt":
        pygame.draw.polygon(surface, white, [(cx + r * 0.2, cy - r * 1.2), (cx - r * 0.7, cy + r * 0.15),
                                             (cx - r * 0.05, cy + r * 0.15), (cx - r * 0.25, cy + r * 1.2),
                                             (cx + r * 0.7, cy - r * 0.2), (cx + r * 0.05, cy - r * 0.2)])
    elif shape == "note":
        pygame.draw.circle(surface, white, (int(cx - r * 0.45), int(cy + r * 0.7)), int(r * 0.38))
        pygame.draw.line(surface, white, (cx - r * 0.1, cy + r * 0.7), (cx - r * 0.1, cy - r), w)
        pygame.draw.line(surface, white, (cx - r * 0.1, cy - r), (cx + r * 0.7, cy - r * 0.6), w)
    elif shape == "crown":
        pygame.draw.polygon(surface, white, [(cx - r, cy + r * 0.6), (cx - r, cy - r * 0.5), (cx - r * 0.5, cy),
                                             (cx, cy - r * 0.9), (cx + r * 0.5, cy), (cx + r, cy - r * 0.5),
                                             (cx + r, cy + r * 0.6)])
    elif shape == "leaf":
        pygame.draw.ellipse(surface, white, pygame.Rect(cx - r * 0.6, cy - r * 1.1, r * 1.2, r * 2.2))
        pygame.draw.line(surface, a + (255,), (cx, cy - r * 0.9), (cx, cy + r * 1.2), max(1, w // 2))
    elif shape == "diamond":
        pygame.draw.polygon(surface, white, [(cx, cy - r * 1.2), (cx + r * 0.9, cy), (cx, cy + r * 1.2),
                                             (cx - r * 0.9, cy)], w)
    mask = pygame.Surface((size_px, size_px), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (size_px // 2, size_px // 2), size_px // 2)
    surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return surface


# --------------------------------------------------------------------------------------------
# On-screen keyboard (used for Wi-Fi passwords and every text setting).

KEY_ROWS = {
    "lower": ["1234567890", "qwertyuiop", "asdfghjkl'", "zxcvbnm,.-"],
    "upper": ["1234567890", "QWERTYUIOP", "ASDFGHJKL\"", "ZXCVBNM;:_"],
    "symbols": ["!@#$%^&*()", "~`=+[]{}\\|", "<>/?'\";:,.", "-_€£¥§°±µ¿"],
}


class Keyboard:
    """Text entry with the controller. act() returns "done", "cancel" or None."""

    def __init__(self, title, text="", secret=False, done_label="Done", max_length=128):
        self.title = title
        self.text = text
        self.secret = secret
        self.show = False
        self.done_label = done_label
        self.max_length = max_length
        self.row, self.col, self.mode = 1, 0, "lower"
        self.status = ""      # A line under the keys (an error).
        self.status_good = False

    def special(self):
        return ["Shift", "#+=", "Space", "Delete", "Show" if self.secret else "Clear", self.done_label]

    def rows(self):
        return KEY_ROWS[self.mode] + [self.special()]

    def type(self, chunk):
        self.text = (self.text + chunk)[:self.max_length]

    def act(self, action, sounds):
        rows = self.rows()
        if action == BACK:
            sounds.play("back")
            return "cancel"
        if action in (UP, DOWN):
            self.row = (self.row + (1 if action == DOWN else -1)) % len(rows)
            self.col = min(self.col, len(rows[self.row]) - 1)
            sounds.play("move")
        elif action in (LEFT, RIGHT):
            self.col = (self.col + (1 if action == RIGHT else -1)) % len(rows[self.row])
            sounds.play("move")
        elif action == SQUARE:
            self.text = self.text[:-1]
            sounds.play("back")
        elif action == TRIANGLE:
            self.mode = "symbols" if self.mode != "symbols" else "lower"
            sounds.play("move")
        elif action == OPTIONS:
            return "done"
        elif action == OK:
            key = rows[self.row][self.col]
            if self.row < len(rows) - 1:
                self.type(key)
                if self.mode == "upper":
                    self.mode = "lower"
                sounds.play("move")
            elif key == "Shift":
                self.mode = "lower" if self.mode == "upper" else "upper"
            elif key == "#+=":
                self.mode = "symbols" if self.mode != "symbols" else "lower"
            elif key == "Space":
                self.type(" ")
            elif key == "Delete":
                self.text = self.text[:-1]
            elif key == "Show":
                self.show = not self.show
            elif key == "Clear":
                self.text = ""
            elif key == self.done_label:
                return "done"
        return None

    def draw(self, c, x, y, width, t):
        """Title, field and keys from (x, y), `width` units wide; returns the bottom."""
        c.text(self.title, 17, x, y, WHITE)
        field_y = y + 30
        c.rect(BACKDROP, x - 4, field_y, width + 8, 52, 10)
        c.rect(ACCENT, x - 4, field_y, width + 8, 52, 10, 2)
        shown = self.text if self.show or not self.secret else \
            ("•" * max(0, len(self.text) - 1) + self.text[-1:])
        surface = c.t.render(shown or " ", 22)
        room = px(width - 24)
        clip = max(0, surface.get_width() - room)
        c.s.blit(surface, (px(x + 10), px(field_y + 12)), area=pygame.Rect(clip, 0, room, surface.get_height()))
        if int(t * 2) % 2 == 0:
            cx = x + 10 + min(surface.get_width(), room) / S + 2 if self.text else x + 10
            c.line(WHITE, cx, field_y + 12, cx, field_y + 40, 2)
        rows = self.rows()
        ky = field_y + 76
        for r, row in enumerate(rows):
            if r < len(rows) - 1:
                key_w = (width - 9 * 6) / 10
                for col, ch in enumerate(row):
                    kx = x + col * (key_w + 6)
                    on = r == self.row and col == self.col
                    c.rect(WHITE if on else KEY, kx, ky, key_w, 46, 8)
                    c.text(ch, 20, kx + key_w / 2, ky + 23, INK if on else WHITE, on, "center")
                ky += 52
            else:
                ky += 6
                gaps = 6 * (len(row) - 1)
                shares = [0.15, 0.13, 0.19, 0.16, 0.14]
                widths = [(width - gaps) * share for share in shares]
                widths.append(width - gaps - sum(widths))
                kx = x
                for col, name in enumerate(row):
                    on = r == self.row and col == self.col
                    main = name == self.done_label
                    active = (name == "Shift" and self.mode == "upper") or \
                             (name == "#+=" and self.mode == "symbols") or (name == "Show" and self.show)
                    color = WHITE if on else ACCENT if main else KEY_ON if active else KEY
                    c.rect(color, kx, ky, widths[col], 46, 8)
                    label = "Hide" if name == "Show" and self.show else name
                    c.text(label, 15, kx + widths[col] / 2, ky + 23, INK if on else WHITE, main or on, "center")
                    kx += widths[col] + 6
                ky += 46
        if self.status:
            for n, line in enumerate(c.t.wrap(self.status, 16, width)[:2]):
                c.text(line, 16, x, ky + 14 + n * 22, GOOD if self.status_good else BAD)
        return ky


def new_particle(anywhere=False):
    return [random.uniform(W * 0.35, W), random.uniform(H * 0.3, H) if anywhere else H + 10,
            random.uniform(8, 26), random.uniform(1.2, 3.2), random.uniform(0, math.tau)]
