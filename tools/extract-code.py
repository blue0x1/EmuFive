#!/usr/bin/env python3
# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
# Writes the executable segments of a PS5 SELF or ELF file as raw files:
#   extract-code.py FILE OUTDIR  ->  OUTDIR/<vaddr in hex>.bin
import os, struct, sys

data = open(sys.argv[1], 'rb').read()
out = sys.argv[2]
os.makedirs(out, exist_ok=True)
segs = None
eoff = 0
if data[:4] in (b'\x4f\x15\x3d\x1d', b'\x54\x14\xf5\xee'):
    n = struct.unpack_from('<H', data, 0x18)[0]
    segs = {}
    for i in range(n):
        props, off, fsz, msz = struct.unpack_from('<4Q', data, 0x20 + i * 32)
        if props & 0x800:
            segs[(props >> 20) & 0xFFF] = (off, fsz, bool(props & 8))
    eoff = 0x20 + n * 32
assert data[eoff:eoff + 4] == b'\x7fELF', 'no ELF header'
phoff, = struct.unpack_from('<Q', data, eoff + 0x20)
phnum, = struct.unpack_from('<H', data, eoff + 0x38)
for i in range(phnum):
    p_type, p_flags, p_off, p_vaddr, _, p_filesz, _, _ = struct.unpack_from('<IIQQQQQQ', data, eoff + phoff + i * 56)
    if p_type != 1 or not p_flags & 1 or p_filesz == 0:
        continue
    if segs is not None:
        off, fsz, compressed = segs[i]
        assert not compressed, 'compressed segment'
        blob = data[off:off + fsz]
    else:
        blob = data[p_off:p_off + p_filesz]
    open(os.path.join(out, '%x.bin' % p_vaddr), 'wb').write(blob)
