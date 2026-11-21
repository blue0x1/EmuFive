# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
"""Reads the home screen's files (name, icon, backgrounds) from a .zar game dump.

A .zar is a ZArchive (github.com/Exzap/ZArchive, Cemu's format, which KytyPS5 runs games from):
the files one after another in 64 KiB blocks, each compressed with zstd (or stored as is), then
the block table, the names and the file tree, and a 144-byte footer at the end. All numbers are
big-endian. Only the few small files of sce_sys are read; they are kept in
~/.cache/ps5-on-ps4/zar/<archive>/sce_sys, so a game's tile is read from the archive only once."""

import ctypes
import ctypes.util
import hashlib
import os
import struct

BLOCK = 64 * 1024
RECORD_BLOCKS = 16                  # Blocks per offset record: a 64-bit base and 16 sizes - 1.
RECORD = struct.Struct(">Q16H")
FOOTER = struct.Struct(">12Q32sQII")
MAGIC, VERSION1 = 0x169F52D6, 0x61BF3A01
ENTRY = struct.Struct(">IIII")      # Name offset (top bit: file), then file or folder fields.
TABLE_LIMIT = 64 * 1024 * 1024      # Names and file tree: a game has far less.
FILE_LIMIT = 48 * 1024 * 1024       # A picture or param.json.
CACHE = os.path.expanduser("~/.cache/ps5-on-ps4/zar")

_zstd = None


def _decompress(data):
    global _zstd
    if _zstd is None:
        lib = ctypes.CDLL(ctypes.util.find_library("zstd") or "libzstd.so.1")
        lib.ZSTD_decompress.restype = ctypes.c_size_t
        lib.ZSTD_decompress.argtypes = (ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t)
        lib.ZSTD_isError.restype = ctypes.c_uint
        lib.ZSTD_isError.argtypes = (ctypes.c_size_t,)
        _zstd = lib
    out = ctypes.create_string_buffer(BLOCK)
    size = _zstd.ZSTD_decompress(out, BLOCK, data, len(data))
    if _zstd.ZSTD_isError(size) or size != BLOCK:
        raise ValueError("broken .zar block")
    return out.raw


class Archive:
    def __init__(self, path):
        self.file = open(path, "rb")
        try:
            self._open()
        except Exception:
            self.file.close()
            raise

    def close(self):
        self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _read(self, offset, size):
        self.file.seek(offset)
        data = self.file.read(size)
        if len(data) != size:
            raise ValueError("the .zar file is cut short")
        return data

    def _open(self):
        total = os.fstat(self.file.fileno()).st_size
        if total < FOOTER.size:
            raise ValueError("not a .zar file")
        f = FOOTER.unpack(self._read(total - FOOTER.size, FOOTER.size))
        if f[15] != MAGIC or f[14] != VERSION1:
            raise ValueError("not a .zar file")
        sections = [(f[i], f[i + 1]) for i in range(0, 12, 2)]
        for offset, size in sections:
            if offset > total or size > total - offset:
                raise ValueError("broken .zar file")
        (self.data_offset, self.data_size), records, names, tree = sections[:4]
        if records[1] > TABLE_LIMIT or names[1] > TABLE_LIMIT or tree[1] > TABLE_LIMIT:
            raise ValueError("the .zar file's tables are too large")
        self.records = self._read(*records)
        self.names = self._read(*names)
        self.tree = self._read(*tree)
        if len(self.tree) < ENTRY.size:
            raise ValueError("broken .zar file")

    def _entry(self, index):
        if index < 0 or (index + 1) * ENTRY.size > len(self.tree):
            raise ValueError("broken .zar file")
        name, a, b, c = ENTRY.unpack_from(self.tree, index * ENTRY.size)
        return bool(name & 0x80000000), name & 0x7FFFFFFF, a, b, c

    def _name(self, offset):
        if offset >= len(self.names):
            return ""
        length = self.names[offset] & 0x7F
        if self.names[offset] & 0x80:
            length |= self.names[offset + 1] << 7
            offset += 2
        else:
            offset += 1
        return self.names[offset:offset + length].decode("utf-8", "replace")

    def children(self, index):
        """[(name, index, is_file)] in a folder."""
        is_file, _, start, count, _ = self._entry(index)
        if is_file:
            return []
        found = []
        for i in range(start, start + count):
            file, name, *_ = self._entry(i)
            found.append((self._name(name), i, file))
        return found

    def lookup(self, path):
        """The entry at a path like "sce_sys/param.json" (any letter case), or None."""
        index = 0
        for part in [p for p in path.split("/") if p]:
            match = next((i for name, i, _ in self.children(index) if name.lower() == part.lower()), None)
            if match is None:
                return None
            index = match
        return index

    def _block(self, number):
        record, sub = divmod(number, RECORD_BLOCKS)
        if (record + 1) * RECORD.size > len(self.records):
            raise ValueError("broken .zar file")
        base, *sizes = RECORD.unpack_from(self.records, record * RECORD.size)
        offset = base + sum(s + 1 for s in sizes[:sub])
        size = sizes[sub] + 1
        if offset + size > self.data_size:
            raise ValueError("broken .zar file")
        data = self._read(self.data_offset + offset, size)
        return data if size == BLOCK else _decompress(data)

    def read(self, index, limit=FILE_LIMIT):
        is_file, _, low_offset, low_size, high = self._entry(index)
        if not is_file:
            raise ValueError("not a file")
        offset = low_offset | (high & 0xFFFF) << 32
        size = low_size | (high >> 16) << 32
        if size > limit:
            raise ValueError("the file is too large")
        out = bytearray()
        while len(out) < size:
            at = offset + len(out)
            block = self._block(at // BLOCK)
            start = at % BLOCK
            out += block[start:start + size - len(out)]
        return bytes(out)

    def game_folder(self):
        """Where sce_sys is: the archive's top, or the one folder at its top ("PPSA12345/")."""
        if self.lookup("sce_sys") is not None:
            return ""
        for name, _, is_file in self.children(0):
            if not is_file and self.lookup(name + "/sce_sys") is not None:
                return name + "/"
        return None


def cache_dir(path):
    """The cache folder of an archive (a new one when the archive changes)."""
    try:
        st = os.stat(path)
        tag = f"{os.path.realpath(path)}|{st.st_size}|{int(st.st_mtime)}"
    except OSError:
        tag = path
    name = os.path.splitext(os.path.basename(path))[0][:40]
    return os.path.join(CACHE, f"{name}-{hashlib.sha1(tag.encode()).hexdigest()[:12]}", "sce_sys")


def extract(path, names):
    """Makes sure the cache has these sce_sys files of the archive (those it has); returns the
    cache's sce_sys folder. A file the archive does not have is remembered as missing."""
    folder = cache_dir(path)
    wanted = [n for n in names if not os.path.exists(os.path.join(folder, n))
              and not os.path.exists(os.path.join(folder, "." + n + ".missing"))]
    if not wanted:
        return folder
    os.makedirs(folder, exist_ok=True)
    try:
        _extract(path, folder, wanted)
    except (struct.error, IndexError) as error:
        raise ValueError(f"broken .zar file: {error}") from error
    return folder


def _extract(path, folder, wanted):
    with Archive(path) as archive:
        top = archive.game_folder()
        for name in wanted:
            index = archive.lookup(f"{top or ''}sce_sys/{name}") if top is not None else None
            target = os.path.join(folder, name)
            if index is None:
                open(os.path.join(folder, "." + name + ".missing"), "w").close()
                continue
            data = archive.read(index)
            with open(target + ".part", "wb") as f:
                f.write(data)
            os.replace(target + ".part", target)
