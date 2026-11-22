# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
"""Tested games (the README's Games tables) for the badges on the game tiles: Works, Slow or
Doesn't work, with the result people reported.

compat.json comes with EmuFive (made by tools/make-compat.py from README.md). A newer list is
downloaded from GitHub at most once a day and kept in ~/.cache, so new test results show without
an update."""

import json
import os
import re
import threading
import time
import unicodedata
import urllib.request

BUNDLED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "compat.json")
CACHE = os.path.expanduser("~/.cache/ps5-on-ps4/compat.json")
URL = "https://raw.githubusercontent.com/blue0x1/EmuFive/main/overlay/opt/ps5-on-ps4/lib/ps5/compat.json"
LIMIT = 512 * 1024
REFRESH_SECONDS = 24 * 3600
STATUSES = ("works", "slow", "broken")
LABELS = {"works": "Works", "slow": "Slow", "broken": "Doesn't work"}
COLORS = {"works": (46, 160, 90), "slow": (214, 150, 30), "broken": (200, 60, 60)}

_lock = threading.Lock()
_games = None       # {normalized title or title ID: entry}


def normalize(title):
    """Lowercase letters and digits only: 'Hollow Knight: Silksong™' -> 'hollowknightsilksong'."""
    text = unicodedata.normalize("NFKD", re.sub("[\u2122\u00ae\u00a9]", "", title or ""))
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _parse(data):
    """{key: entry} from compat.json bytes; ValueError when it isn't a valid list."""
    doc = json.loads(data.decode("utf-8"))
    games = {}
    for entry in doc.get("games", []) if isinstance(doc, dict) else []:
        if not isinstance(entry, dict) or entry.get("status") not in STATUSES:
            continue
        clean = {k: str(entry.get(k, ""))[:200] for k in ("title", "status", "console", "version", "result")}
        if not clean["title"]:
            continue
        games[normalize(clean["title"])] = clean
        for title_id in entry.get("title_ids", []) if isinstance(entry.get("title_ids"), list) else []:
            if re.fullmatch(r"PPSA[0-9]{5}", str(title_id)):
                games[str(title_id)] = clean
    if not games:
        raise ValueError("no games in the list")
    return games


def _load():
    global _games
    for path in (CACHE, BUNDLED):
        try:
            with open(path, "rb") as f:
                games = _parse(f.read(LIMIT))
        except (OSError, ValueError):
            continue
        with _lock:
            _games = games
        return
    with _lock:
        _games = {}


def lookup(title_id, title):
    """The tested entry for a game ({"title", "status", "console", "version", "result"}), or None."""
    if _games is None:
        _load()
    with _lock:
        games = _games or {}
        return games.get(title_id or "") or games.get(normalize(title))


def refresh(done=None):
    """Downloads a newer list in the background when the cached one is a day old; calls done()
    when the list changed."""
    try:
        if time.time() - os.path.getmtime(CACHE) < REFRESH_SECONDS:
            return
    except OSError:
        pass

    def work():
        try:
            request = urllib.request.Request(URL, headers={"User-Agent": "EmuFive"})
            with urllib.request.urlopen(request, timeout=15) as reply:
                data = reply.read(LIMIT + 1)
            if len(data) > LIMIT:
                return
            _parse(data)
            os.makedirs(os.path.dirname(CACHE), exist_ok=True)
            with open(CACHE + ".new", "wb") as f:
                f.write(data)
            os.replace(CACHE + ".new", CACHE)
        except (OSError, ValueError):
            return
        _load()
        if done is not None:
            done()

    threading.Thread(target=work, daemon=True).start()
