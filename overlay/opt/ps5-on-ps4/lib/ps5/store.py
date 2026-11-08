# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
"""Saved settings of the home screen, in ~/.config/ps5-on-ps4 (readable only by the PS5 user)."""

import json
import os
import threading
import time

CONFIG_DIR = os.path.expanduser("~/.config/ps5-on-ps4")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")
GAMES_FILE = os.path.join(CONFIG_DIR, "games.json")
AVATAR_FILE = os.path.join(CONFIG_DIR, "avatar.png")     # The first profile's picture.
PROFILES_FILE = os.path.join(CONFIG_DIR, "profiles.json")
KYTY_WORK = os.path.expanduser("~/.kytyps5")              # KytyPS5's files for the first profile.
FIRST_PROFILE = 1000                                      # KytyPS5's user ID of the first profile.
MAX_PROFILES = 8
SHARED_KYTY = ("_PipelineCache", "_DownloadData")         # The same for every profile.

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
    "vibration_on": True,
    "lightbar_brightness": 100,  # 25, 50, 75, 100 percent
    "controller_mic": True,    # The controller's microphone (on a USB cable)
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

def lightbar_rgb(settings):
    """The light bar color with its brightness."""
    rgb = LIGHTBAR_COLORS.get(settings["lightbar"], LIGHTBAR_COLORS["blue"])[1]
    level = max(0, min(100, settings["lightbar_brightness"])) / 100
    return tuple(int(round(v * level)) for v in rgb)


def vibration(settings):
    """Vibration strength 0-100 (0 when vibration is off)."""
    return max(0, min(100, settings["vibration"])) if settings["vibration_on"] else 0


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


# --------------------------------------------------------------------------------------------
# Profiles: each has a name, a picture and a KytyPS5 user ID; its saves and trophies are in its
# own KytyPS5 folder, and play time is counted per profile. The first profile (1000) is what there
# was before profiles: ~/.kytyps5 and avatar.png. The current profile's name and picture are also
# in Settings ("name", "avatar"), where the screens read them.

def avatar_file(profile_id):
    if profile_id == FIRST_PROFILE:
        return AVATAR_FILE
    return os.path.join(CONFIG_DIR, f"avatar-{profile_id}.png")


def work_dir(profile_id):
    """KytyPS5's folder for a profile (made when missing): saves, trophies; caches are shared."""
    if profile_id == FIRST_PROFILE:
        os.makedirs(KYTY_WORK, exist_ok=True)
        return KYTY_WORK
    path = os.path.join(KYTY_WORK, "users", str(profile_id))
    os.makedirs(path, exist_ok=True)
    for name in SHARED_KYTY:
        shared = os.path.join(KYTY_WORK, name)
        link = os.path.join(path, name)
        os.makedirs(shared, exist_ok=True)
        if not os.path.lexists(link):
            os.symlink(os.path.join("..", "..", name), link)
    return path


class Profiles:
    def __init__(self, settings=None):
        self.lock = threading.Lock()
        data = read_json(PROFILES_FILE)
        profiles = [p for p in data.get("profiles", []) if isinstance(p, dict) and isinstance(p.get("id"), int)]
        if not profiles:
            settings = settings or Settings()
            profiles = [{"id": FIRST_PROFILE, "name": settings["name"], "avatar": settings["avatar"]}]
        self.profiles = profiles
        ids = [p["id"] for p in profiles]
        self.current_id = data.get("current") if data.get("current") in ids else ids[0]

    def _save(self):
        text = json.dumps({"current": self.current_id, "profiles": self.profiles}, indent=2) + "\n"
        try:
            write_private(PROFILES_FILE, text)
        except OSError:
            pass

    def all(self):
        with self.lock:
            return [dict(p) for p in self.profiles]

    def current(self):
        with self.lock:
            return dict(next(p for p in self.profiles if p["id"] == self.current_id))

    def switch(self, profile_id, settings):
        with self.lock:
            profile = next((p for p in self.profiles if p["id"] == profile_id), None)
            if profile is None:
                return
            self.current_id = profile_id
            self._save()
        settings.set(name=profile["name"], avatar=profile["avatar"])

    def update(self, profile_id, **changes):
        with self.lock:
            for p in self.profiles:
                if p["id"] == profile_id:
                    p.update(changes)
            self._save()

    def add(self, name, avatar):
        """A new profile's ID, or None when there are MAX_PROFILES already."""
        with self.lock:
            if len(self.profiles) >= MAX_PROFILES:
                return None
            new_id = max(p["id"] for p in self.profiles) + 1
            self.profiles.append({"id": new_id, "name": name, "avatar": avatar})
            self._save()
        return new_id

    def remove(self, profile_id, settings):
        """Deletes a profile with its saves, trophies and picture (never the last profile)."""
        with self.lock:
            if len(self.profiles) <= 1:
                return False
            self.profiles = [p for p in self.profiles if p["id"] != profile_id]
            if self.current_id == profile_id:
                self.current_id = self.profiles[0]["id"]
            first = self.profiles[0] if self.current_id == self.profiles[0]["id"] else None
            self._save()
        if first is not None:
            settings.set(name=first["name"], avatar=first["avatar"])
        import shutil
        folder = work_dir(profile_id)
        for name in ("_SaveData", "_Trophies", "_TempData"):
            shutil.rmtree(os.path.join(folder, name), ignore_errors=True)
        if profile_id != FIRST_PROFILE:
            shutil.rmtree(folder, ignore_errors=True)
            try:
                os.remove(avatar_file(profile_id))
            except OSError:
                pass
        Games().forget_profile(profile_id)
        return True


class Games:
    """Per game: favorite, hidden, KytyPS5 options; play time and last played per profile
    ("plays": {profile ID: {"seconds", "last"}}; the first profile's are also the old
    play_seconds and last_played)."""

    def __init__(self, profile_id=None):
        self.lock = threading.Lock()
        self.data = read_json(GAMES_FILE)
        self.profile_id = FIRST_PROFILE if profile_id is None else profile_id

    def get(self, key):
        with self.lock:
            entry = self.data.get(key)
            entry = dict(entry) if isinstance(entry, dict) else {}
        play = (entry.get("plays") or {}).get(str(self.profile_id))
        if isinstance(play, dict):
            entry["play_seconds"], entry["last_played"] = play.get("seconds", 0), play.get("last", 0)
        elif self.profile_id != FIRST_PROFILE:
            entry["play_seconds"], entry["last_played"] = 0, 0
        return entry

    def _set_play(self, key, seconds, last):
        with self.lock:
            entry = self.data.get(key)
            entry = dict(entry) if isinstance(entry, dict) else {}
            plays = dict(entry.get("plays") or {})
            plays[str(self.profile_id)] = {"seconds": int(seconds), "last": int(last)}
            entry["plays"] = plays
            if self.profile_id == FIRST_PROFILE:
                entry["play_seconds"], entry["last_played"] = int(seconds), int(last)
            self.data[key] = entry
            text = json.dumps(self.data, indent=2) + "\n"
        try:
            write_private(GAMES_FILE, text)
        except OSError:
            pass

    def forget_profile(self, profile_id):
        with self.lock:
            for entry in self.data.values():
                if isinstance(entry, dict) and isinstance(entry.get("plays"), dict):
                    entry["plays"].pop(str(profile_id), None)
            text = json.dumps(self.data, indent=2) + "\n"
        try:
            write_private(GAMES_FILE, text)
        except OSError:
            pass

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
        entry = self.get(key)
        self._set_play(key, entry.get("play_seconds", 0), time.time())

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
        self._set_play(key, int(entry.get("play_seconds", 0)) + int(seconds), time.time())
