# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
"""What happened in the last game, for test reports and crash reports.

ps5-launch writes LAST_GAME when a game ends: the game, how long it ran, how it ended, the FPS
KytyPS5 logged (patch 0038: a "fps-log:" line every 10 seconds) and the settings it ran with.
- A crash (an error, not closed from the PS button menu) saves a report folder with the log in
  ~/PS5-reports, and on the USB drive in PS5-logs when one is plugged in.
- A test report (OPTIONS on a game, Report a test) turns it into a GitHub issue that opens on a
  phone from a QR code, or a file on the USB drive."""

import json
import os
import re
import shutil
import time
import urllib.parse

from . import store, system, update

LAST_GAME = os.path.join(system.RUNTIME, "ps5-last-game.json")
REPORTS = os.path.expanduser("~/PS5-reports")
KEEP_REPORTS = 10
ISSUE_URL = "https://github.com/blue0x1/EmuFive/issues/new"
RESULTS = {"works": "Playable", "slow": "Runs, but slowly", "broken": "Doesn't work"}

_FPS = re.compile(r"^fps-log: ([0-9.]+)", re.M)


def fps_from_log(text):
    """{"avg", "min", "max"} from the fps-log lines (the first 30 seconds, loading, left out), or None."""
    values = [float(v) for v in _FPS.findall(text)]
    if len(values) > 3:
        values = values[3:]
    values = [v for v in values if v > 0.5]
    if not values:
        return None
    return {"avg": round(sum(values) / len(values)), "min": round(min(values)), "max": round(max(values))}


def console_model():
    return dict(system.system_info()).get("Console", "PS4").split(",")[0]


def last_game():
    """The last game's record, or None."""
    data = store.read_json(LAST_GAME)
    return data if data.get("title") else None


def write_last_game(record):
    try:
        store.write_private(LAST_GAME, json.dumps(record) + "\n")
    except OSError:
        pass


def details(record, result=None):
    """The report's lines (English, for GitHub)."""
    lines = [f"Game: {record['title']}" + (f" ({record['title_id']}" + (f", v{record['version']}" if record.get('version') else "") + ")"
                                            if record.get("title_id") else "")]
    lines.append(f"Console: {record.get('console', 'PS4')}")
    lines.append(f"EmuFive: {record.get('emufive', '?')}")
    if result:
        lines.append(f"Result: {RESULTS.get(result, result)}")
    fps = record.get("fps")
    if fps:
        lines.append(f"FPS: about {fps['avg']} (from {fps['min']} to {fps['max']})")
    minutes = int(record.get("played", 0) // 60)
    lines.append(f"Played: {minutes} min" if minutes else "Played: under a minute")
    if record.get("ended"):
        lines.append(f"Ended: {record['ended']}")
    if record.get("settings"):
        lines.append("Settings: " + ", ".join(record["settings"]))
    lines.append(f"Storage: {record.get('source', '?')}")
    return lines


def issue_url(record, result):
    title = f"Game test: {record['title']}" + (f" ({record['title_id']})" if record.get("title_id") else "")
    body = "\n".join(details(record, result)) + "\n\n(Made by EmuFive's Report a test. Attach kytyps5.log if the game stopped: Settings, System, Copy logs to USB.)"
    return ISSUE_URL + "?" + urllib.parse.urlencode({"title": title, "body": body})


def _prune():
    try:
        folders = sorted(os.listdir(REPORTS))
    except OSError:
        return
    for name in folders[:-KEEP_REPORTS]:
        shutil.rmtree(os.path.join(REPORTS, name), ignore_errors=True)


def save(record, result=None, log=True):
    """Saves a report folder (report.txt and the game's log) in ~/PS5-reports, and a copy in
    PS5-logs on the USB drive when one is plugged in. Returns (folder, USB copy or None)."""
    stamp = time.strftime("%Y-%m-%d %H.%M.%S")
    name = f"{stamp} {re.sub(r'[^A-Za-z0-9 ._-]', '', record.get('title_id') or record['title'])[:40]}".strip()
    folder = os.path.join(REPORTS, name)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(details(record, result)) + "\n")
    if log and os.path.isfile(system.GAME_LOG):
        shutil.copy(system.GAME_LOG, os.path.join(folder, "kytyps5.log"))
    _prune()
    usb = None
    if system.mounted(system.USB_MOUNT):
        try:
            usb = os.path.join(system.USB_MOUNT, "PS5-logs", "report " + name)
            shutil.copytree(folder, usb, dirs_exist_ok=True)
        except OSError:
            usb = None
    return folder, usb


def record_for(game, played, code, ended, settings_used, log_text):
    return {"title": game.title, "title_id": game.title_id, "version": game.version,
            "source": game.source_name if getattr(game, "source_name", "") else "",
            "console": console_model(), "emufive": update.installed(), "played": int(played),
            "code": code, "ended": ended, "settings": settings_used, "fps": fps_from_log(log_text),
            "time": int(time.time())}
