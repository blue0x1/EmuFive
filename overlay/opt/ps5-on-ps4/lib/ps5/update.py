# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
"""EmuFive updates from the GitHub releases of REPO.

A release is tagged with its version (1.0.1 or v1.0.1) and has two files:
  emufive-1.0.1.tar          the update pack (scripts/make-release.sh makes it):
                               update.json      {"version", "restart", "remove": [paths], "notes"}
                               files.tar        new and changed files, paths from / (optional)
                               kytyps5.tar.xz   a new emulator for /opt/kytyps5 (optional)
                               post.sh          run as root after the files are in (optional)
  emufive-1.0.1.tar.sha256   its SHA-256

The home screen checks (as the ps5 user) and shows the result; installing and rolling back run as
root in bin/ps5-update (started by ps5-admin), which writes its progress to STATUS. Pre-releases
and drafts are skipped."""

import json
import os
import re
import time
import urllib.error
import urllib.request

REPO = "blue0x1/EmuFive"
# For tests on a PC: another folder as / and another release list (a file:// URL works).
ROOT = os.environ.get("EMUFIVE_TEST_ROOT", "").rstrip("/")
API = os.environ.get("EMUFIVE_TEST_RELEASES") or f"https://api.github.com/repos/{REPO}/releases?per_page=50"
VERSION_FILE = ROOT + "/etc/ps5-on-ps4-version"
STATE_DIR = ROOT + "/var/lib/ps5-on-ps4/update"
BACKUP = os.path.join(STATE_DIR, "backup")          # The files before the last update (Roll back).
BACKUP_INFO = os.path.join(BACKUP, "info.json")
STATUS_DIR = ROOT + "/run/emufive-update"
STATUS = os.path.join(STATUS_DIR, "status.json")
USER_AGENT = "EmuFive-updater"
_VERSION = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


def parse(text):
    """'1.0.1' or 'v1.0.1' as (1, 0, 1), or None."""
    m = _VERSION.match((text or "").strip())
    return tuple(int(n) for n in m.groups()) if m else None


def name(version):
    return ".".join(str(n) for n in version)


def installed():
    """The installed version as text (1.0.0 when the file is missing)."""
    try:
        with open(VERSION_FILE) as f:
            text = f.readline().strip()
        if parse(text):
            return text.lstrip("v")
    except OSError:
        pass
    return "1.0.0"


def fetch(url, timeout=15):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                   "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def releases(with_pack=True):
    """The published releases, oldest first: dicts with version (tuple), tag, pack and sha256
    (download URLs, None when the release has no update pack) and notes. with_pack: only those
    that can be installed."""
    try:
        data = json.loads(fetch(API).decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code == 404:           # The repository has no releases yet (or is not public yet).
            return []
        raise
    found = []
    for r in data if isinstance(data, list) else []:
        if r.get("draft") or r.get("prerelease"):
            continue
        version = parse(r.get("tag_name"))
        if not version:
            continue
        assets = {a.get("name"): a.get("browser_download_url") for a in r.get("assets", [])}
        pack = f"emufive-{name(version)}.tar"
        has_pack = pack in assets and pack + ".sha256" in assets
        if has_pack or not with_pack:
            found.append({"version": version, "tag": r.get("tag_name"), "pack": assets.get(pack) if has_pack else None,
                          "sha256": assets.get(pack + ".sha256") if has_pack else None,
                          "notes": (r.get("body") or "").strip()})
    found.sort(key=lambda r: r["version"])
    return found


def pending(current=None):
    """The releases newer than the installed version, oldest first (each one is installed in
    turn, so none is skipped)."""
    now = parse(current or installed())
    return [r for r in releases() if r["version"] > now]


def check():
    """What the Settings page shows: {"installed", "newest" (installable), "count", "unpacked"
    (a newer release without its update pack: it cannot be installed yet), "error"}."""
    current = installed()
    now = parse(current)
    try:
        everything = [r for r in releases(with_pack=False) if r["version"] > now]
    except Exception as error:      # No network, GitHub not reachable, rate limit...
        return {"installed": current, "newest": None, "count": 0, "unpacked": None,
                "error": str(error) or "error"}
    newer = [r for r in everything if r["pack"]]
    newest = name(newer[-1]["version"]) if newer else None
    latest = name(everything[-1]["version"]) if everything else None
    return {"installed": current, "newest": newest, "count": len(newer),
            "unpacked": latest if latest and latest != newest else None, "error": None}


def status():
    """The progress of an update or roll back now (or the last one since the PS4 started)."""
    try:
        with open(STATUS) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def write_status(**fields):
    os.makedirs(STATUS_DIR, mode=0o755, exist_ok=True)
    fields["time"] = time.time()
    tmp = STATUS + ".tmp"
    with open(tmp, "w") as f:
        json.dump(fields, f)
    os.chmod(tmp, 0o644)
    os.replace(tmp, STATUS)


def backup_info():
    """The last update that can be rolled back: {"from", "to", "restart"}, or None."""
    try:
        with open(BACKUP_INFO) as f:
            info = json.load(f)
        return info if info.get("from") else None
    except (OSError, ValueError):
        return None
