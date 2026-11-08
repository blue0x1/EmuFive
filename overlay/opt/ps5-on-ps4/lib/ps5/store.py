# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
"""Saved settings of the home screen, in ~/.config/ps5-on-ps4 (readable only by the PS5 user)."""

import json
import os
import threading
import time

CONFIG_DIR = os.path.expanduser("~/.config/ps5-on-ps4")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")
GAMES_FILE = os.path.join(CONFIG_DIR, "games.json")
AVATAR_FILE = os.path.join(CONFIG_DIR, "avatar.png")

DEFAULT_SETTINGS = {
    "name": "Player",          # Shown on the home screen and given to games as the user name.
    "avatar": "builtin:0",     # builtin:N, or "file" for AVATAR_FILE (a chosen online picture).
    "sort": "recent",          # recent or name
    "show_hidden": False,
    "clock_24h": True,
    "auto_off_minutes": 0,     # 0: never. Only while the home screen is idle.
    "fps_counter": False,      # A small FPS counter in the bottom-left corner of games.
    "menu_language": "en",     # i18n.LANGUAGES
    # Appearance.
    "theme": "dark",           # dark, midnight, light
    "accent": "purple",        # ui.ACCENTS
    "background": "art",       # art, gradient, solid, picture (BACKGROUND_FILE)
    "dim": 0,                  # 0-80: extra darkness over the background
    "orbs": True,
    "orb_amount": "normal",    # few, normal, many
    "orb_speed": "normal",     # slow, normal, fast
    "orb_color": "white",      # white, accent, gold
    "animations": "full",      # full, reduced, off
    "tile_size": "medium",     # small, medium, large
    "tile_shape": "rounded",   # rounded, square, circle
    "source_labels": True,
    "text_size": 100,          # 90-130 percent
    "font": "modern",          # ui.FONTS
    "clock_date": False,
    "clock_seconds": False,
    "show_name": True,
    "show_avatar": True,
    "show_battery": True,      # The controller's battery (Bluetooth).
    "show_ip": False,
    "sounds": True,
    "sound_volume": 80,
    "sound_style": "chimes",   # ui.SOUND_STYLES
    "rumble": True,
    "hints": True,
    "overscan": 0,             # 0-10 percent
    "screensaver_minutes": 0,  # 0: off
    "screensaver_mode": "dim", # dim, slideshow
    # Controller.
    "lightbar": "blue",        # LIGHTBAR_COLORS
    "vibration": 100,          # 0-100
    "swap_buttons": False,     # X and O swapped
    # Games (all games).
    "default_shader_cache": False,
    "default_perf_overlay": False,
    "default_full_hd": False,
    "console_language": 1,     # 1: English (US); LANGUAGES
    "hdr": False,
    "present_mode": "Mailbox", # Mailbox, Fifo, Immediate
}

LIGHTBAR_COLORS = {
    "blue": ("Blue", (0, 70, 255)), "red": ("Red", (255, 20, 20)), "green": ("Green", (0, 220, 60)),
    "purple": ("Purple", (150, 40, 255)), "orange": ("Orange", (255, 110, 0)), "pink": ("Pink", (255, 60, 160)),
    "white": ("White", (255, 255, 255)), "cyan": ("Cyan", (0, 220, 255)), "off": ("Off", (0, 0, 0)),
}

# PlayStation system languages, by number (KytyPS5 --console-language).
LANGUAGES = ["Japanese", "English (US)", "French", "Spanish", "German", "Italian", "Dutch", "Portuguese",
             "Russian", "Korean", "Chinese (traditional)", "Chinese (simplified)", "Finnish", "Swedish",
             "Danish", "Norwegian", "Polish", "Portuguese (Brazil)", "English (UK)", "Turkish",
             "Spanish (Latin America)", "Arabic", "French (Canada)", "Czech", "Hungarian", "Greek",
             "Romanian", "Thai", "Vietnamese", "Indonesian"]

PRESENT_MODES = {"Mailbox": "Balanced (default)", "Fifo": "Smooth (no tearing)", "Immediate": "Lowest latency"}

BACKGROUND_FILE = os.path.join(CONFIG_DIR, "background.png")

# KytyPS5 options a game can have, shown in its Game settings: (key, label, option).
GAME_OPTIONS = [
    ("perf_overlay", "Performance overlay", ["--perf-overlay"]),
    ("skip_logos", "Skip startup logos", ["--skip-notice-screen"]),
    ("shader_cache", "Keep compiled shaders", ["--shader-cache"]),
    ("full_hd", "Render at 1920x1080", ["--screen-width", "1920", "--screen-height", "1080"]),
    ("network", "Local network for the game", ["--network-connected"]),
]


def write_private(path, text):
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    temp = path + ".new"
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.chmod(temp, 0o600)
    os.replace(temp, path)


def read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


class Settings:
    def __init__(self):
        self.lock = threading.Lock()
        self.data = dict(DEFAULT_SETTINGS)
        saved = read_json(SETTINGS_FILE)
        for key, default in DEFAULT_SETTINGS.items():
            if isinstance(saved.get(key), type(default)):
                self.data[key] = saved[key]

    def __getitem__(self, key):
        with self.lock:
            return self.data[key]

    def set(self, **changes):
        with self.lock:
            self.data.update(changes)
            text = json.dumps(self.data, indent=2) + "\n"
        try:
            write_private(SETTINGS_FILE, text)
        except OSError:
            pass


def game_key(game_path, title_id):
    """Games are remembered by title ID, so the same game from another drive keeps its settings."""
    return title_id or os.path.basename(game_path.rstrip("/"))


class Games:
    """Per game: favorite, hidden, last played, KytyPS5 options."""

    def __init__(self):
        self.lock = threading.Lock()
        self.data = read_json(GAMES_FILE)

    def get(self, key):
        with self.lock:
            entry = self.data.get(key)
            return dict(entry) if isinstance(entry, dict) else {}

    def update(self, key, **changes):
        with self.lock:
            entry = self.data.get(key)
            entry = dict(entry) if isinstance(entry, dict) else {}
            entry.update(changes)
            self.data[key] = entry
            text = json.dumps(self.data, indent=2) + "\n"
        try:
            write_private(GAMES_FILE, text)
        except OSError:
            pass

    def played(self, key):
        self.update(key, last_played=int(time.time()))

    def options(self, key, settings=None):
        """The KytyPS5 command-line options for this game: its own, and the defaults for all games
        (Settings, Games) when `settings` is given."""
        entry = self.get(key)
        args = []
        for name, _, option in GAME_OPTIONS:
            if entry.get(name) or (settings is not None and settings.data.get("default_" + name)):
                args += option
        return args

    def add_play_time(self, key, seconds):
        entry = self.get(key)
        self.update(key, play_seconds=int(entry.get("play_seconds", 0)) + int(seconds),
                    last_played=int(time.time()))
