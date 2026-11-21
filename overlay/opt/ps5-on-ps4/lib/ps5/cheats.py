# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
"""Cheats for PS5 games (the cheat manager on the home screen, Settings > Games).

The cheats come from the HEN Cheats Collection (github.com/TeeKay87/HEN-Cheats-Collection), the
files etaHEN and GoldHEN players use, in three formats: json (etaHEN), shn (a GoldHEN trainer in
XML) and mc4 (the same XML, encrypted). Each file is for one game version (title ID and version
in its name). shn and mc4 are turned into the json form, which is what KytyPS5 reads
(--game-patch, src/loader/gamePatch.cpp): it checks the game and version, finds the module by each
cheat's original bytes ("off") and writes the cheat's bytes ("on") before the game runs them.

    ~/.config/ps5-on-ps4/cheats/index.json      the PS5 files in the collection (Update)
    ~/.config/ps5-on-ps4/cheats/files/NAME.json each file, downloaded when its game is opened
    ~/.config/ps5-on-ps4/cheats/selection.json  the cheats turned on, per title ID and version

ps5-launch writes the chosen cheats of the game that starts to $XDG_RUNTIME_DIR/ps5-cheats.json."""

import base64
import json
import os
import re
import shutil
import subprocess
import time
import urllib.request
import xml.etree.ElementTree as ET

from . import store

REPO = "https://raw.githubusercontent.com/TeeKay87/HEN-Cheats-Collection/master/cheats/"
SOURCE = "HEN Cheats Collection (TeeKay87)"
FORMATS = ("json", "shn", "mc4")      # The order used when one version has files in several.
DIR = os.path.join(store.CONFIG_DIR, "cheats")
INDEX_FILE = os.path.join(DIR, "index.json")
FILES_DIR = os.path.join(DIR, "files")
SELECTION_FILE = os.path.join(DIR, "selection.json")
USER_AGENT = "EmuFive"
INDEX_LIMIT = 4 * 1024 * 1024
FILE_LIMIT = 8 * 1024 * 1024
# MC4 is base64 of AES-256-CBC with a fixed key and IV (as in KytyPS5's launcher, cheatFile.cpp).
MC4_KEY = b"304c6528f659c766110239a51cl5dd9c"
MC4_IV = b"u@}kzW2u[u(8DWar"

_NAME = re.compile(r"\A(PPSA[0-9]{5})_([0-9]+(?:\.[0-9]+)+)_[A-Za-z0-9_.-]+\.(json|mc4|shn)\Z")
_HEX = re.compile(r"\A(?:[0-9a-fA-F]{2})+\Z")
_OFFSET = re.compile(r"\A(?:0[xX])?[0-9a-fA-F]{1,16}\Z")
_SECTION_KEYS = ("section", "sectionName", "sectionProtection", "logicalOffset", "sectionOffset")


def _fetch(url, limit):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=20) as reply:
        data = reply.read(limit + 1)
    if len(data) > limit:
        raise ValueError("the download is too large")
    return data


def _write(path, text):
    store.write_private(path, text)


# Index -----------------------------------------------------------------------------------------

def read_index():
    """{"updated": seconds, "games": {title_id: [{"file", "version", "format", "title"}]}}."""
    data = store.read_json(INDEX_FILE)
    if not isinstance(data.get("games"), dict):
        data["games"] = {}
    return data


def update_index():
    """Downloads the list of PS5 cheat files. Returns (ok, message)."""
    games = {}
    for fmt in FORMATS:
        try:
            text = _fetch(REPO + fmt + ".txt", INDEX_LIMIT).decode("utf-8", "replace")
        except (OSError, ValueError) as error:
            return False, f"Could not download the cheat list: {error}"
        for line in text.lstrip("﻿").splitlines():
            name, _, title = line.strip().partition("=")
            match = _NAME.match(name)
            if not match or match.group(3) != fmt:
                continue
            games.setdefault(match.group(1), []).append(
                {"file": name, "version": match.group(2), "format": fmt, "title": title.strip()})
    if not games:
        return False, "The cheat list was empty. Try again later."
    for entries in games.values():
        entries.sort(key=lambda e: (e["version"], FORMATS.index(e["format"]), e["file"]))
    _write(INDEX_FILE, json.dumps({"updated": int(time.time()), "games": games}) + "\n")
    # Files may have changed: download them again when they are needed, and now for the cheats
    # that are turned on (so those games keep them without the internet).
    shutil.rmtree(FILES_DIR, ignore_errors=True)
    for choice in read_selection().values():
        if choice.get("on") and choice.get("file"):
            load(choice["file"])
    return True, f"Cheats for {len(games)} PS5 games."


def entries(index, title_id, version=None):
    """The cheat files for a game (only those for `version` when given)."""
    found = index["games"].get(title_id.upper(), []) if title_id else []
    return [e for e in found if version is None or e["version"] == version]


# Files -----------------------------------------------------------------------------------------

def _hex(text):
    return re.sub(r"[\s-]", "", text or "")


def trainer_to_plan(data):
    """A GoldHEN trainer (shn, or decrypted mc4) as the json form."""
    text = data.decode("utf-8", "replace").lstrip("﻿")
    end = text.find("</Trainer>")
    if end < 0:
        raise ValueError("not a cheat trainer file")
    root = ET.fromstring(text[:end + len("</Trainer>")])
    mods = []
    for cheat in root.iter("Cheat"):
        memory = []
        for line in cheat.iter("Cheatline"):
            write = {"offset": (line.findtext("Offset") or "").strip(),
                     "on": _hex(line.findtext("ValueOn")), "off": _hex(line.findtext("ValueOff"))}
            section = (line.findtext("Section") or "0").strip()
            if section not in ("", "0"):
                write["section"] = section
            if (line.findtext("Absolute") or "").strip().lower() == "true":
                write["absolute"] = True
            memory.append(write)
        mods.append({"name": cheat.get("Text", "").strip(), "description": cheat.get("Description", ""),
                     "memory": memory})
    return {"name": root.get("Game", ""), "id": root.get("Cusa", ""), "version": root.get("Version", ""),
            "process": root.get("Process", ""), "credits": [root.get("Moder", "")] if root.get("Moder") else [],
            "mods": mods}


def mc4_to_plan(data):
    raw = base64.b64decode(data)
    done = subprocess.run(["openssl", "enc", "-d", "-aes-256-cbc", "-nopad", "-K", MC4_KEY.hex(),
                           "-iv", MC4_IV.hex()], input=raw[:len(raw) // 16 * 16],
                          capture_output=True, timeout=20)
    if done.returncode != 0:
        raise ValueError("could not decrypt the mc4 file")
    return trainer_to_plan(done.stdout)


def problem(plan):
    """Why KytyPS5 can't use this file, or None. The same checks as KytyPS5's launcher
    (cheatFile.cpp ValidateImport), except that the writes may name their module (sectionName, as
    a Unity game's Il2CppUserAssemblies.prx) when all the file's writes are in that one module:
    the emulator finds the module by the original bytes, the same for every write."""
    if not isinstance(plan, dict) or not isinstance(plan.get("mods"), list) or not plan["mods"]:
        return "The cheat file has no cheats."
    if "master" in plan:
        return "This cheat file uses master codes, which are not supported yet."
    if str(plan.get("process", "")).lower() != "eboot.bin":
        return "This cheat file is for another program of the game."
    sections = set()
    for mod in plan["mods"]:
        if not isinstance(mod, dict) or not str(mod.get("name", "")).strip():
            return "The cheat file has a cheat without a name."
        if "module_name" in mod:
            return "This cheat file uses module cheats, which are not supported yet."
        memory = mod.get("memory")
        if not isinstance(memory, list) or not memory:
            return f"The cheat \"{mod.get('name')}\" has nothing to write."
        for write in memory:
            if not isinstance(write, dict):
                return "The cheat file has an invalid entry."
            if write.get("absolute") \
                    or ("expected" in write and str(write["expected"]).lower() != str(write.get("off", "")).lower()):
                return "This cheat file uses memory addressing that is not supported yet."
            # The module a write is in: its sectionName ("executable" is eboot.bin, like writes
            # without one), else a numbered section of a trainer file.
            section = str(write.get("section", 0) or 0)
            sections.add(write.get("sectionName") or ("executable" if section == "0" else "section " + section))
            off, on = str(write.get("off", "")), str(write.get("on", ""))
            if not _OFFSET.match(str(write.get("offset", ""))) or not _HEX.match(off) \
                    or not _HEX.match(on) or len(off) != len(on):
                return f"The cheat \"{mod.get('name')}\" has invalid bytes."
    if len(sections) > 1:
        return "This cheat file writes into several modules of the game, which is not supported yet."
    return None


def _cached(name):
    return os.path.join(FILES_DIR, os.path.splitext(name)[0] + ".json")


def load(name):
    """(plan, None) for a cheat file of the index, downloaded the first time; (None, message)."""
    path = _cached(name)
    plan = store.read_json(path)
    if not plan:
        match = _NAME.match(name)
        if not match:
            return None, "Unknown cheat file."
        fmt = match.group(3)
        try:
            data = _fetch(REPO + fmt + "/" + name, FILE_LIMIT)
            plan = json.loads(data.decode("utf-8-sig")) if fmt == "json" else \
                trainer_to_plan(data) if fmt == "shn" else mc4_to_plan(data)
        except (OSError, ValueError, ET.ParseError, subprocess.SubprocessError) as error:
            return None, f"Could not download the cheats: {error}"
        if not isinstance(plan, dict):
            return None, "The cheat file is not valid."
        try:
            _write(path, json.dumps(plan, indent=1) + "\n")
        except OSError:
            pass
    return plan, None


def mod_names(plan):
    return [str(m.get("name", "")).strip() for m in plan.get("mods", []) if isinstance(m, dict)]


def credits(plan):
    names = plan.get("credits") or []
    return ", ".join(str(n) for n in names if str(n).strip()) if isinstance(names, list) else str(names)


# Selection -------------------------------------------------------------------------------------

def _key(title_id, version):
    return f"{title_id.upper()}_{version}"


def read_selection():
    return store.read_json(SELECTION_FILE)


def choice(title_id, version):
    """{"file": name, "on": [cheat names]} for a game version ({} when nothing was chosen)."""
    found = read_selection().get(_key(title_id, version))
    return found if isinstance(found, dict) else {}


def set_choice(title_id, version, file, on):
    selection = read_selection()
    key = _key(title_id, version)
    if on or file:
        selection[key] = {"file": file, "on": list(on)}
    else:
        selection.pop(key, None)
    _write(SELECTION_FILE, json.dumps(selection, indent=1) + "\n")


def enabled_count(title_id, version):
    return len(choice(title_id, version).get("on", [])) if title_id and version else 0


def launch_plan(title_id, version, path):
    """Writes the cheats turned on for this game version to `path` (KytyPS5's --game-patch file).
    Returns the names written, [] when there are none (and nothing is written), or a message."""
    chosen = choice(title_id, version)
    names = set(chosen.get("on", []))
    if not names or not chosen.get("file"):
        return []
    plan, error = load(chosen["file"])
    if plan is None:
        return error
    if str(plan.get("id", "")).upper() != title_id.upper() or str(plan.get("version", "")) != version:
        return "the cheat file is for another game version"
    why = problem(plan)
    if why:
        return why
    mods = [dict(m, enabled=True) for m in plan["mods"] if str(m.get("name", "")).strip() in names]
    if not mods:
        return []
    out = dict(plan, mods=mods)
    _write(path, json.dumps(out) + "\n")
    return [m["name"] for m in mods]
