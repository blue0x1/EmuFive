#!/usr/bin/env python3
# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
"""Writes a 32 KB SNES test ROM: a blue screen that turns green while any
button of controller 1 is held. Checks that a game loads and gets input.

  tools/make-pad-test-rom.py out/pad-test.sfc
"""
import sys

code = bytes([
    0x78, 0x18, 0xFB,             # sei; clc; xce (native mode)
    0xE2, 0x30,                   # sep #$30 (8-bit A, X, Y)
    0xA9, 0x80, 0x8D, 0x00, 0x21, # lda #$80; sta $2100 (screen off)
    0xA9, 0x01, 0x8D, 0x00, 0x42, # lda #$01; sta $4200 (read the joypads in vblank)
    0xA9, 0x0F, 0x8D, 0x00, 0x21, # lda #$0F; sta $2100 (screen on)
    # frame: wait for vblank, then for the joypad read to finish
    0xAD, 0x12, 0x42, 0x10, 0xFB, # lda $4212; bpl -5
    0xAD, 0x12, 0x42, 0x29, 0x01, 0xD0, 0xF9,  # lda $4212; and #1; bne -7
    0x9C, 0x21, 0x21,             # stz $2121 (colour 0)
    0xAD, 0x18, 0x42,             # lda $4218
    0x0D, 0x19, 0x42,             # ora $4219
    0xF0, 0x0C,                   # beq blue
    0xA9, 0xE0, 0x8D, 0x22, 0x21, # lda #$E0; sta $2122  (green 0x03E0)
    0xA9, 0x03, 0x8D, 0x22, 0x21, # lda #$03; sta $2122
    0x80, 0x0A,                   # bra wait_end
    0xA9, 0x00, 0x8D, 0x22, 0x21, # blue: lda #$00; sta $2122  (blue 0x7C00)
    0xA9, 0x7C, 0x8D, 0x22, 0x21, # lda #$7C; sta $2122
    0xAD, 0x12, 0x42, 0x30, 0xFB, # wait_end: lda $4212; bmi -5 (until vblank ends)
    0x80, 0xCC,                   # bra frame
])
# patch the final branch to jump to "frame" (offset 20)
frame = 20
code = bytearray(code)
code[-1] = (frame - len(code)) & 0xFF

rom = bytearray(b'\xFF' * 0x8000)
rom[0:len(code)] = code
rom[0x100] = 0x40                       # rti, for the interrupt vectors
title = b'PS5ON PS4 PAD TEST'.ljust(21)
rom[0x7FC0:0x7FD5] = title
rom[0x7FD5] = 0x20                      # LoROM
rom[0x7FD6] = 0x00                      # ROM only
rom[0x7FD7] = 0x05                      # 32 KB
rom[0x7FD8] = 0x00                      # no SRAM
rom[0x7FD9] = 0x01                      # North America
rom[0x7FDA] = 0x00
rom[0x7FDB] = 0x00
for v in (0x7FEA, 0x7FEE, 0x7FFA, 0x7FFE):  # NMI/IRQ: rti at $8100
    rom[v:v + 2] = (0x8100).to_bytes(2, 'little')
rom[0x7FFC:0x7FFE] = (0x8000).to_bytes(2, 'little')  # reset
rom[0x7FDC:0x7FE0] = b'\xFF\xFF\x00\x00'
s = sum(rom) & 0xFFFF
rom[0x7FDC:0x7FDE] = (s ^ 0xFFFF).to_bytes(2, 'little')
rom[0x7FDE:0x7FE0] = s.to_bytes(2, 'little')
open(sys.argv[1], 'wb').write(rom)
