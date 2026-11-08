# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
"""The About page: a pixel-art sunset with hills, grass and spears, and a bronze-framed panel with
the project, its author and the credits, in gold serif letters. Everything is drawn here; the
author's GitHub picture is downloaded once (when online) and kept in ~/.cache."""

import math
import os
import random
import threading
import urllib.request

from . import ui

pygame = ui.pygame

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
AVATAR_URL = "https://github.com/blue0x1.png?size=128"
AVATAR_CACHE = os.path.expanduser("~/.cache/ps5-on-ps4/blue0x1.png")

GOLD_TOP, GOLD_BOTTOM = (255, 236, 170), (196, 120, 40)
PANEL_FILL = (40, 16, 8)
FRAME = (150, 80, 30)
FRAME_INNER = (90, 40, 14)
LABEL = (230, 170, 90)
NAME = (255, 230, 190)
WHAT = (220, 170, 120)
RED = (255, 140, 120)

CREDITS = [
    ("KytyPS5", "the PS5 emulator"),
    ("PS4 Linux", "the kernel"),
    ("Mesa", "the PS4 GPU drivers"),
    ("fail0verflow", "PS4 GPU patches"),
    ("pygame and SDL", "this home screen"),
    ("Inter", "the font"),
    ("DiceBear", "cartoon avatars"),
    ("Lorem Picsum", "photo avatars"),
    ("smbnetfs", "games from a PC"),
]


def _font(size, bold):
    path = SERIF_BOLD if bold else SERIF
    if not os.path.exists(path):
        path = None
    return pygame.font.Font(path, max(6, ui.px(size)))


def _spaced(text, size, bold, spacing, color):
    font = _font(size, bold)
    glyphs = [font.render(ch, True, color) for ch in text]
    gap = ui.px(size * spacing)
    width = sum(g.get_width() for g in glyphs) + gap * max(0, len(glyphs) - 1)
    out = pygame.Surface((max(1, width), font.get_height()), pygame.SRCALPHA)
    x = 0
    for g in glyphs:
        out.blit(g, (x, 0))
        x += g.get_width() + gap
    return out


def _place(target, surface, x, y, anchor):
    rect = surface.get_rect(**{anchor: (ui.px(x), ui.px(y))})
    target.blit(surface, rect)
    return rect


def _gold(target, text, size, x, y, anchor="midtop", spacing=0.12):
    """Engraved gold letters: a gold gradient with a dark edge and shadow."""
    shape = _spaced(text, size, True, spacing, (255, 255, 255))
    w, h = shape.get_size()
    gold = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(h):
        k = 0.5 + 0.5 * math.cos(i / max(1, h - 1) * math.pi * 1.2)
        color = tuple(int(GOLD_BOTTOM[j] + (GOLD_TOP[j] - GOLD_BOTTOM[j]) * k) for j in range(3))
        pygame.draw.line(gold, color + (255,), (0, i), (w, i))
    gold.blit(shape, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    dark = _spaced(text, size, True, spacing, (40, 16, 4))
    rect = gold.get_rect(**{anchor: (ui.px(x), ui.px(y))})
    step = max(1, ui.px(size / 20))
    for dx, dy in ((-step, 0), (step, 0), (0, -step), (0, step), (step * 2, step * 2)):
        target.blit(dark, rect.move(dx, dy))
    target.blit(gold, rect)


def _text(target, text, size, x, y, color, anchor="topleft", bold=False, spacing=0.02):
    return _place(target, _spaced(text, size, bold, spacing, color), x, y, anchor)


def _landscape(width, height):
    """The pixel-art sunset, drawn at 1/6 size and scaled up with hard pixels."""
    scale = 6
    sw, sh = max(1, width // scale), max(1, height // scale)
    small = pygame.Surface((sw, sh))
    bands = [(252, 226, 160), (246, 200, 120), (232, 160, 80), (206, 116, 50), (160, 70, 30), (110, 40, 20)]
    for i in range(sh):
        pygame.draw.line(small, bands[min(len(bands) - 1, int(i / sh * len(bands) * 1.3))], (0, i), (sw, i))
    rng = random.Random(12)

    def hills(base, amp, color, step):
        pts = [(0, sh)]
        for x in range(0, sw + step, step):
            pts.append((x, base + int(amp * math.sin(x / 11 + base)) + rng.randint(-1, 1)))
        pts.append((sw, sh))
        pygame.draw.polygon(small, color, pts)

    hills(int(sh * 0.58), 6, (150, 80, 46), 4)
    hills(int(sh * 0.68), 4, (96, 44, 24), 3)
    hills(int(sh * 0.82), 2, (40, 16, 8), 2)
    for x in range(0, sw, 3):
        if rng.random() < 0.6:
            pygame.draw.line(small, (40, 16, 8), (x, int(sh * 0.82) - rng.randint(1, 4)), (x, int(sh * 0.82)))
    for x0, h in ((14, 60), (22, 54), (sw - 18, 62), (sw - 28, 50)):
        top_x = x0 + (6 if x0 < sw / 2 else -6)
        pygame.draw.line(small, (40, 16, 8), (x0, int(sh * 0.83)), (top_x, int(sh * 0.83) - h))
        pygame.draw.polygon(small, (40, 16, 8), [(top_x - 1, int(sh * 0.83) - h + 2), (top_x + 1, int(sh * 0.83) - h + 2),
                                                 (top_x, int(sh * 0.83) - h - 3)])
    return pygame.transform.scale(small, (width, height)), scale


class AboutArt:
    def __init__(self, versions):
        self.versions = versions        # (system version, KytyPS5 version)
        self.cache = None
        self.cache_size = None
        self.avatar = None
        self.avatar_state = "none"      # none, loading, ready, failed
        self.stars = [(random.uniform(0, 1280), random.uniform(0, 300), random.uniform(0, math.tau))
                      for _ in range(40)]
        self.dust = [[random.uniform(0, 1280), random.uniform(0, 720), random.uniform(6, 18),
                      random.uniform(0, math.tau)] for _ in range(36)]

    def _load_avatar(self, online):
        if self.avatar_state != "none":
            return
        if os.path.exists(AVATAR_CACHE):
            try:
                self.avatar = pygame.image.load(AVATAR_CACHE)
                self.avatar_state = "ready"
                return
            except (pygame.error, OSError):
                pass
        if not online:
            return
        self.avatar_state = "loading"

        def work():
            try:
                request = urllib.request.Request(AVATAR_URL, headers={"User-Agent": "ps5-on-ps4"})
                with urllib.request.urlopen(request, timeout=12) as reply:
                    data = reply.read(2_000_000)
                os.makedirs(os.path.dirname(AVATAR_CACHE), exist_ok=True)
                with open(AVATAR_CACHE + ".part", "wb") as f:
                    f.write(data)
                os.replace(AVATAR_CACHE + ".part", AVATAR_CACHE)
                self.avatar = pygame.image.load(AVATAR_CACHE)
                self.avatar_state = "ready"
                self.cache = None           # Draw the page again with the picture.
            except Exception:
                self.avatar_state = "failed"

        threading.Thread(target=work, daemon=True).start()

    def _pixel_avatar(self, size_px):
        if self.avatar is not None:
            small = pygame.transform.smoothscale(self.avatar, (32, 32))
            return pygame.transform.scale(small, (size_px, size_px))
        # No picture yet: a pixel "B" monogram.
        grid = ["11110", "10001", "10001", "11110", "10001", "10001", "11110"]
        surface = pygame.Surface((size_px, size_px))
        surface.fill((200, 120, 50))
        cell = size_px // 9
        for r, row in enumerate(grid):
            for col, bit in enumerate(row):
                if bit == "1":
                    pygame.draw.rect(surface, (40, 16, 8), pygame.Rect((col + 2) * cell, (r + 1) * cell, cell, cell))
        return surface

    def _build(self, size):
        width, height = size
        page, scale = _landscape(width, height)
        W = ui.W
        cx = W / 2
        # Panel with a bronze frame.
        pygame.draw.rect(page, PANEL_FILL, pygame.Rect(ui.px(cx - 360), ui.px(70), ui.px(720), ui.px(520)))
        pygame.draw.rect(page, FRAME, pygame.Rect(ui.px(cx - 360), ui.px(70), ui.px(720), ui.px(520)), ui.px(6))
        pygame.draw.rect(page, FRAME_INNER, pygame.Rect(ui.px(cx - 348), ui.px(82), ui.px(696), ui.px(496)),
                         max(1, ui.px(2)))
        _gold(page, "PS5 ON PS4", 44, cx, 96, "midtop", 0.14)
        # The author.
        pygame.draw.rect(page, (176, 112, 52), pygame.Rect(ui.px(cx - 266), ui.px(176), ui.px(140), ui.px(140)))
        page.blit(self._pixel_avatar(ui.px(128)), (ui.px(cx - 260), ui.px(182)))
        _text(page, "CREATED BY", 13, cx - 96, 192, LABEL, bold=True, spacing=0.3)
        _gold(page, "CHOKRI HAMMEDI", 26, cx - 96, 214, "topleft", 0.08)
        _text(page, "blue0x1", 18, cx - 96, 256, RED, bold=True)
        _text(page, "github.com/blue0x1", 16, cx - 96, 286, NAME, bold=True)
        # The credits.
        _text(page, "ALLIES", 13, cx - 300, 346, LABEL, bold=True, spacing=0.4)
        for i, (name, what) in enumerate(CREDITS):
            col, row = i % 2, i // 2
            x = cx - 300 + col * 320
            y = 372 + row * 38
            _text(page, name, 16, x, y, NAME, bold=True)
            _text(page, what, 12, x, y + 20, WHAT)
        version, kyty = self.versions
        _text(page, f"Version {version}   ·   KytyPS5 {kyty}", 11, cx, 560, (170, 120, 80), "midtop")
        return page.convert()

    def draw(self, c, t, online):
        self._load_avatar(online)
        size = c.s.get_size()
        if self.cache is None or self.cache_size != size:
            self.cache = self._build(size)
            self.cache_size = size
        c.s.blit(self.cache, (0, 0))
        # Stars twinkle; dust drifts up through the warm light.
        block = max(2, ui.px(4))
        for x, y, phase in self.stars:
            if x < ui.W / 2 - 370 or x > ui.W / 2 + 370 or y < 60:
                light = int(200 + 55 * math.sin(t * 2 + phase))
                if light > 220:
                    pygame.draw.rect(c.s, (255, 244, 210), pygame.Rect(ui.px(x), ui.px(y), block, block))
        for p in self.dust:
            p[1] -= p[2] * 0.016
            p[0] += math.sin(t * 0.7 + p[3]) * 0.15
            if p[1] < 0:
                p[1] = ui.H
                p[0] = random.uniform(0, ui.W)
            if ui.W / 2 - 370 < p[0] < ui.W / 2 + 370 and 60 < p[1] < 600:
                continue
            pygame.draw.rect(c.s, (255, 214, 150), pygame.Rect(ui.px(p[0]), ui.px(p[1]), block, block))
