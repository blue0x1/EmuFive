# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
"""The language of the menus. The screens are written in English; the text is translated where it
is drawn (ui.Text), so every screen is translated without changes of its own.

translations.json maps each English text to its translations:
    "Settings": {"ar": "...", "fr": "...", "tr": "...", "es": "..."}
A text with blanks fills them in from the English one:
    "Close {a}? What the game has not saved is lost."
{n} and {m} only stand for a number, {q} and {r} for an amount like "12 GB", any other name for
any text. Text in a blank that is itself in the table is translated too ("Close the game? ...").
A line made of parts ("Bluetooth  ·  80%  ·  charging") is translated part by part."""

import json
import os
import re

LANGUAGES = {"en": "English", "ar": "العربية", "fr": "Français", "tr": "Türkçe", "es": "Español",
             "de": "Deutsch", "it": "Italiano", "pt": "Português (Brasil)"}
RTL_LANGUAGES = {"ar"}
TABLE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "translations.json")
SEPARATOR = "  ·  "
_BLANK = re.compile(r"\{([a-z])\}")
_PATTERNS = {"n": r"-?\d[\d.,]*", "m": r"-?\d[\d.,]*", "q": r"-?\d[\d.,]* ?[A-Za-z]{0,3}",
             "r": r"-?\d[\d.,]* ?[A-Za-z]{0,3}"}

_language = "en"
_table = {}
_templates = []     # (regex, translation), the most specific first
_done = {}          # English -> translation, and each translation -> itself


def language():
    return _language


def rtl():
    """True when the menus read from right to left (Arabic)."""
    return _language in RTL_LANGUAGES


def set_language(code):
    global _language, _table, _templates, _done
    _language = code if code in LANGUAGES else "en"
    _table, _templates, _done = {}, [], {}
    if _language == "en":
        return
    try:
        with open(TABLE_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return
    for english, translations in data.items():
        text = translations.get(_language) if isinstance(translations, dict) else None
        if not text:
            continue
        if _BLANK.search(english):
            _templates.append((_compile(english), text, len(_BLANK.sub("", english))))
        else:
            _table[english] = text
    _templates.sort(key=lambda t: -t[2])
    _templates = [(regex, text) for regex, text, _ in _templates]


def _compile(english):
    parts, seen, pos = [], set(), 0
    for m in _BLANK.finditer(english):
        parts.append(re.escape(english[pos:m.start()]))
        name = m.group(1)
        if name in seen:
            parts.append(f"(?P={name})")
        else:
            seen.add(name)
            parts.append(f"(?P<{name}>{_PATTERNS.get(name, '.+?')})")
        pos = m.end()
    parts.append(re.escape(english[pos:]))
    return re.compile("".join(parts), re.S)


class Final(str):
    """Text that is already in the menu language (a translated line cut to fit, or one line of a
    wrapped text), so it is never looked up again: a game title's second line ("PS4 drive")
    must stay as it is."""


def translate(text):
    """`text` in the menu language (unchanged when there is no translation)."""
    if _language == "en" or not text or isinstance(text, Final):
        return text
    result = _done.get(text)
    if result is None:
        result = _translate(text)
        if len(_done) > 5000:
            _done.clear()
        _done[text] = result
        _done[result] = result     # Already translated: never translated twice.
    return result


def _translate(text):
    found = _table.get(text)
    if found is not None:
        return found
    for regex, translation in _templates:
        m = regex.fullmatch(text)
        if m:
            values = {k: _translate(v.strip()) for k, v in m.groupdict().items()}
            try:
                return translation.format(**values)
            except (KeyError, IndexError, ValueError):
                return text
    if SEPARATOR in text:
        return SEPARATOR.join(_translate(part) for part in text.split(SEPARATOR))
    return text


def upper(text):
    """`text` translated, in capitals (Turkish: i becomes İ)."""
    text = translate(text)
    if _language == "tr":
        text = text.replace("i", "İ")
    return text.upper()


def has_rtl(text):
    """True when `text` has Arabic letters."""
    return any("֐" <= ch <= "ࣿ" or "יִ" <= ch <= "ﻼ" for ch in text)


# Arabic shaping. SDL_ttf here draws each letter alone and left to right, so the text is turned
# into the joined letter forms (Arabic Presentation Forms-B) and put in display order first.
# Letter: (alone, end, start, middle); letters that join only to the letter before have two.
_FORMS = {
    0x0621: (0xFE80,), 0x0622: (0xFE81, 0xFE82), 0x0623: (0xFE83, 0xFE84), 0x0624: (0xFE85, 0xFE86),
    0x0625: (0xFE87, 0xFE88), 0x0626: (0xFE89, 0xFE8A, 0xFE8B, 0xFE8C), 0x0627: (0xFE8D, 0xFE8E),
    0x0628: (0xFE8F, 0xFE90, 0xFE91, 0xFE92), 0x0629: (0xFE93, 0xFE94), 0x062A: (0xFE95, 0xFE96, 0xFE97, 0xFE98),
    0x062B: (0xFE99, 0xFE9A, 0xFE9B, 0xFE9C), 0x062C: (0xFE9D, 0xFE9E, 0xFE9F, 0xFEA0),
    0x062D: (0xFEA1, 0xFEA2, 0xFEA3, 0xFEA4), 0x062E: (0xFEA5, 0xFEA6, 0xFEA7, 0xFEA8), 0x062F: (0xFEA9, 0xFEAA),
    0x0630: (0xFEAB, 0xFEAC), 0x0631: (0xFEAD, 0xFEAE), 0x0632: (0xFEAF, 0xFEB0),
    0x0633: (0xFEB1, 0xFEB2, 0xFEB3, 0xFEB4), 0x0634: (0xFEB5, 0xFEB6, 0xFEB7, 0xFEB8),
    0x0635: (0xFEB9, 0xFEBA, 0xFEBB, 0xFEBC), 0x0636: (0xFEBD, 0xFEBE, 0xFEBF, 0xFEC0),
    0x0637: (0xFEC1, 0xFEC2, 0xFEC3, 0xFEC4), 0x0638: (0xFEC5, 0xFEC6, 0xFEC7, 0xFEC8),
    0x0639: (0xFEC9, 0xFECA, 0xFECB, 0xFECC), 0x063A: (0xFECD, 0xFECE, 0xFECF, 0xFED0),
    0x0641: (0xFED1, 0xFED2, 0xFED3, 0xFED4), 0x0642: (0xFED5, 0xFED6, 0xFED7, 0xFED8),
    0x0643: (0xFED9, 0xFEDA, 0xFEDB, 0xFEDC), 0x0644: (0xFEDD, 0xFEDE, 0xFEDF, 0xFEE0),
    0x0645: (0xFEE1, 0xFEE2, 0xFEE3, 0xFEE4), 0x0646: (0xFEE5, 0xFEE6, 0xFEE7, 0xFEE8),
    0x0647: (0xFEE9, 0xFEEA, 0xFEEB, 0xFEEC), 0x0648: (0xFEED, 0xFEEE), 0x0649: (0xFEEF, 0xFEF0),
    0x064A: (0xFEF1, 0xFEF2, 0xFEF3, 0xFEF4),
}
_LAM_ALEF = {0x0622: (0xFEF5, 0xFEF6), 0x0623: (0xFEF7, 0xFEF8), 0x0625: (0xFEF9, 0xFEFA), 0x0627: (0xFEFB, 0xFEFC)}
_TATWEEL = 0x0640
_MIRROR = {"(": ")", ")": "(", "[": "]", "]": "[", "{": "}", "}": "{", "<": ">", ">": "<", "«": "»", "»": "«"}
_LEAD = "([{\"'«"
_TRAIL = ")]}\"'».,:;!?،؟…"


def _arabic_letters(word):
    """True when the word has Arabic letters (not only Arabic punctuation like ، or ؟)."""
    return any(0x0621 <= ord(ch) <= 0x064A or 0x0660 <= ord(ch) <= 0x06FF or 0xFB50 <= ord(ch) <= 0xFEFC
               for ch in word if ch not in "،؛؟")


def _mark(ch):
    """Vowel signs: dropped (they would need placing over the letters)."""
    return 0x064B <= ord(ch) <= 0x065F or ord(ch) == 0x0670


def _joins_next(code):
    return code == _TATWEEL or len(_FORMS.get(code, ())) == 4


def _joins_prev(code):
    return code == _TATWEEL or len(_FORMS.get(code, ())) >= 2


def shape(word):
    """An Arabic word in joined letter forms, in display order (left to right)."""
    codes = [ord(ch) for ch in word if not _mark(ch)]
    out = []
    i = 0
    while i < len(codes):
        code = codes[i]
        before = i > 0 and _joins_next(codes[i - 1])
        if code == 0x0644 and i + 1 < len(codes) and codes[i + 1] in _LAM_ALEF:
            out.append(chr(_LAM_ALEF[codes[i + 1]][1 if before else 0]))
            i += 2
            continue
        forms = _FORMS.get(code)
        if forms is None:
            out.append(chr(code))
        else:
            after = i + 1 < len(codes) and _joins_prev(codes[i + 1])
            if len(forms) == 4:
                form = forms[3] if before and after else forms[1] if before else forms[2] if after else forms[0]
            elif len(forms) == 2:
                form = forms[1] if before else forms[0]
            else:
                form = forms[0]
            out.append(chr(form))
        i += 1
    return "".join(_MIRROR.get(ch, ch) for ch in reversed(out))


def visual(text):
    """A line with Arabic in display order for a left-to-right text drawer: the words go right to
    left; Latin words and numbers between them (USB, Wi-Fi 6, 12 GB) stay left to right."""
    items = []          # [text, is_latin, space_before], in reading order
    for n, word in enumerate(text.split(" ")):
        space = n > 0
        if _arabic_letters(word) or not any(ch.isalnum() for ch in word):
            items.append([shape(word), False, space])
            continue
        lead, trail = "", ""
        while word and word[0] in _LEAD:
            lead, word = lead + word[0], word[1:]
        while word and word[-1] in _TRAIL:
            trail, word = word[-1] + trail, word[:-1]
        for ch in lead:
            items.append([_MIRROR.get(ch, ch), False, space])
            space = False
        if items and items[-1][1] and space:
            items[-1][0] += " " + word          # Latin words together keep their order.
        else:
            items.append([word, True, space])
        for ch in trail:
            items.append([_MIRROR.get(ch, ch), False, False])
    out = []
    for text_part, _, space in reversed(items):
        out.append(text_part)
        if space:
            out.append(" ")
    return "".join(out)
