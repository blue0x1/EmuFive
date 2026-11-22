#!/usr/bin/env python3
# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
# Makes overlay/opt/ps5-on-ps4/lib/ps5/compat.json (the badges on the game tiles) from the two
# Games tables in README.md. Run it after changing a table:
#   tools/make-compat.py
# "Games that work": a result starting with "Playable" is Works, others (Runs, Starts) are Slow.
# "Games that don't work yet": Doesn't work. TITLE_IDS adds title IDs for games whose param.json
# name differs from the README's.
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "overlay/opt/ps5-on-ps4/lib/ps5/compat.json")
TITLE_IDS = {
    "Invincible VS": ["PPSA30568"],
    "DRAGON BALL: Sparking! ZERO": ["PPSA15210", "PPSA15211"],
    "Plants vs. Zombies: Replanted": ["PPSA29802"],
}


def tables(text):
    """[(summary, [rows])] for each <details> section."""
    out = []
    for summary, body in re.findall(r"<summary><b>(.*?)</b></summary>(.*?)</details>", text, re.S):
        rows = []
        for line in body.splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == 4 and cells[0] not in ("Game", "") and not set(cells[0]) <= set("-"):
                rows.append(cells)
        out.append((summary, rows))
    return out


def main():
    with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
        text = f.read()
    games = []
    for summary, rows in tables(text):
        broken = "don't work" in summary
        for title, console, version, result in rows:
            status = "broken" if broken else "works" if result.lower().startswith("playable") else "slow"
            entry = {"title": title, "status": status, "console": console, "version": version, "result": result}
            if title in TITLE_IDS:
                entry["title_ids"] = TITLE_IDS[title]
            games.append(entry)
    if not games:
        sys.exit("No Games tables found in README.md")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"games": games}, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"{OUT}: {len(games)} games")


if __name__ == "__main__":
    main()
