<h1 align="center">PS5 on PS4</h1>

<p align="center">
  <img src="https://img.shields.io/badge/platform-PS4-003791?logo=playstation&logoColor=white" alt="Platform: PS4">
  <img src="https://img.shields.io/badge/status-experimental-red" alt="Status: experimental">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--2.0-blue" alt="License: GPL-2.0"></a>
</p>

The [KytyPS5](https://github.com/KytyPS5/KytyPS5) PS5 emulator on a jailbroken PlayStation 4: Linux, the PS4's own GPU through Vulkan, and an emulator build made for the PS4's CPU.

Created by **[Chokri Hammedi (blue0x1)](https://github.com/blue0x1)**. Built on [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot).

> **Status: experimental research.** On a PS4 Pro, a native PS5 homebrew app (Snes9x PS5, rebuilt for the PS4's CPU) runs in KytyPS5 and draws its screen. KytyPS5 now rewrites the PS5-only CPU instructions in game code (patch `0004`); whether and how fast a game runs on the PS4 is being tested. See [The CPU problem](#the-cpu-problem).

## How it works

- **[PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot)** starts Linux on the PS4 and installs Linux systems on its internal drive, from the controller.
- **PS4 Mesa**, part of PS4 Multiboot, gives the PS4 GPU (Liverpool on the PS4 and Slim, Gladius on the Pro) Vulkan 1.3. KytyPS5 needs sparse resources, which RADV offers on this GPU with `RADV_EXPERIMENTAL=sparse`.
- **KytyPS5**, upstream at a pinned commit with this project's patches (`patches/kytyps5/`), built with `-march=btver2` for the PS4's AMD Jaguar CPU. The official build uses AVX2 and stops with "Illegal instruction" on the PS4.
  - `0001`: the `KYTY_HOST_ARCH` build option (the CPU the emulator is compiled for).
  - `0002`: a C library for homebrew. PS5 homebrew built with the ps5-native-app-boilerplate ships a stand-in `sce_module/libc.prx` whose functions all return 0 (the console uses its own C library), so in KytyPS5 its `malloc` failed. The patch adds the C library functions such homebrew imports and uses them only for such a stand-in module.
  - `0003`: more for homebrew: files and folders, system calls, the foreground user, and extra mounts (`KYTY_MOUNTS`).
  - `0004`: PS5 code on the PS4's CPU. Every AVX2, FMA and BMI2 instruction is rewritten into SSE4.2/AVX/BMI1 code when a module loads; one that cannot be rewritten there is replaced the first time it runs. See [The CPU problem](#the-cpu-problem).
- **PS5 on PS4** packs all of it into a small Linux system that boots straight into the emulator, full screen, with no desktop. It installs through PS4 Multiboot like any other system.

## The CPU problem

KytyPS5 does not emulate the PS5's CPU: it runs the game's own x86-64 code directly. PS5 games are built for the PS5's Zen 2 CPU and use AVX2, BMI2 and FMA instructions throughout. The PS4's Jaguar CPU has none of them, so game code stops at the first such instruction.

Patch `0004` adds that to KytyPS5's guest instruction patcher. When the host CPU lacks AVX2, FMA or BMI2, each such instruction is replaced by code with the same effect: 256-bit integer operations as two 128-bit halves, permutes across halves with AVX moves and blends, per-element shifts one element at a time, FMA computed in double precision, gathers one element at a time, BMI2 with saved registers. The jump to a replacement goes where the instruction was; an instruction too short for one, in a spot the patcher cannot rearrange, faults and is replaced at run time.

`tools/jaguar-test/` checks every replacement on a PC that has these instructions: it takes each instruction form found in a program's code, runs the original and the replacement from the same random state, and compares all registers, flags and memory. The forms found in the programs tested so far match: 287 in God of War Sons of Sparta (gathers and VFMADDSUB included) and 227 in the programs tested before. The exceptions are rare last-bit differences in FMA (single precision is rounded twice, double precision is a multiply and an add) and a NaN corner case of 0 times infinity.

The Jaguar is still far slower than the PS5's CPU, and the replacements add to that, so even a game that runs may run slowly.

## Plan

| Step | Status |
|---|---|
| Vulkan on the PS4 GPU meets KytyPS5's requirements | Done (`RADV_EXPERIMENTAL=sparse`) |
| KytyPS5 built for the PS4's CPU | Done (`KYTY_HOST_ARCH=btver2`) |
| KytyPS5 starts on the PS4 and sets up the GPU | Done, PS4 Pro |
| PS5 on PS4 system image, installs through PS4 Multiboot | Done, PS4 Pro |
| A PS5 homebrew app without AVX2 runs and draws | Done: Snes9x PS5 2.11 rebuilt for btver2, PS4 Pro |
| Controller, `/data` and USB storage, loading a game in that app | Done on a PC test build (same patches); PS4 next |
| AVX2, BMI2 and FMA translation for game code | Done (`0004`), checked on a PC; first game test on the PS4 next |
| Home screen: pick a game with the controller; Wi-Fi; Settings | Done, checked on a PC |
| Games from the USB drive, the PS4 drive or a PC share | Done, checked on a PC; PS4 next |

## Building

Needs Docker, git and the PS4 Mesa from PS4 Multiboot (`../PS4-Multiboot/out/ps4-mesa.tar.xz`, built with `make mesa` there). `build-kyty.sh` clones KytyPS5 into `build/kytyps5` the first time, then resets it to the pinned commit and applies the patches on every build.

```bash
scripts/build-kyty.sh      # out/kytyps5-ps4.tar.xz
scripts/build-rootfs.sh    # out/ps5-ps4-rootfs.tar.xz
```

`PS4_MESA` and `KYTY` point `build-rootfs.sh` at other paths.

## Installing

1. Copy `ps5-ps4-rootfs.tar.xz` to `/user/home/` on the PS4 (GoldHEN FTP).
2. Start PS4 Multiboot and install **PS5 on PS4** from the menu.
3. Put your games in one of the places below. A game is a folder with `eboot.bin` (and `sce_sys`), or a ZArchive (`.zar`) dump.

The system starts in the home screen and needs no keyboard:

- The games show up as tiles, each labeled with where it is: **USB**, **PS4** or **PC**. Pick one and press Play; when it quits, the home screen comes back.
- At the top: Wi-Fi (with an on-screen keyboard for the password) and Settings, and two tabs, **Games** and **Media** (L1 / R1). Media shows your screenshots; open one, and Square deletes it.
- OPTIONS on a game: favorite, hide, its own settings, its trophies and how long you played it.
- The PS button during a game pauses it and opens the quick menu: Resume, **Home** (the home screen, with the game still paused: PS or Resume goes back to it; starting another game asks first, then closes it), Close the game, volume, power.
- Screenshots: PS + Square, or Share, also in a game. They go to `PS5-screenshots` on the USB drive (or `~/Screenshots` without one), with a small notice in the corner.
- Settings, Appearance: accent color, theme (dark, midnight, light), background (the game's art, a gradient, a solid color or your own picture from the USB drive), background dim, floating orbs, animations, tile size and shape, text size and font, clock, what the top bar shows (the battery is the controller's), menu sounds, rumble, button hints, screen edges (overscan) and a screensaver.
- Settings, Controllers: light bar color, vibration, swapping X and O, and a test page for every button and stick. Settings, Games: defaults for all games, game language, HDR and frame pacing. Settings, System: the menu language (English, Arabic, French, Turkish or Spanish), temperature and CPU load, back up the settings to the USB drive, or reset them all.
- Menu languages: the translations are in `lib/ps5/translations.json`, one entry per English text. Arabic is right-aligned and drawn with DejaVu Sans; its letters are joined in `lib/ps5/i18n.py`, since SDL_ttf here does not join them.
- The program sees the USB drive as `/mnt/usb0` and a folder of the system (`~/data`, kept between starts) as `/data`. For Snes9x PS5, ROMs go in `snes9x/roms` on the USB drive or in `~/data/snes9x/roms`.
- If the emulator stops with an error, the home screen shows the reason.
- `PS5_GAME` in `/etc/ps5-on-ps4.conf` runs one game straight away instead of the home screen.
- Controllers: a DualShock 4 on a cable, or over Bluetooth after holding SHARE + PS until the light bar double-blinks.
- Sound goes to the TV over HDMI, also when a controller on a cable brings its own sound card (`/etc/wireplumber/wireplumber.conf.d/51-ps5-hdmi.conf`).

### Where games can be

- **USB drive:** the `PS5` folder at the top of the drive. exFAT is best (files over 4 GB); NTFS works too.
- **PS4 drive:** `/user/home/PS5` on the PS4, copied there with GoldHEN FTP. The system reads the PS4 drive read-only and never changes it. Not available when the system itself was installed on a USB drive.
- **A PC:** a shared folder on Windows or Linux. In Settings, turn on **Use games from PC** and set the PC address, the shared folder and, unless it is a guest share, a username and password; then Connect. Games can be at the top of the shared folder or in a `PS5` folder in it. A network cable is faster than Wi-Fi.
  - Windows: share the folder (Properties, Sharing). For a guest share, share it with Everyone and turn off *Password protected sharing* in Advanced sharing settings.
  - Linux (Samba): a share with `guest ok = yes` for a guest share, or a Samba user (`smbpasswd -a`).
  - The PS4 kernel has no SMB client, so the system uses smbnetfs (FUSE). The settings, password included, are kept in `~/.config/ps5-on-ps4/pc-share.json`, readable only by the `ps5` user.

`tools/make-pad-test-rom.py` writes a tiny SNES ROM for checking a controller: blue, green while a button is held.

Login: `ps5` / `ps5` on tty2 or SSH. The emulator's output is in `~/kytyps5.log` (the run before: `~/kytyps5.log.1`).

## Games

This project contains no PS5 system software and no games. Use only games you own and dumped yourself.

## Project layout

| Path | Contents |
|---|---|
| `scripts/build-kyty.sh` | Builds KytyPS5 (upstream plus `patches/kytyps5/`) for the PS4's CPU |
| `patches/kytyps5/` | This project's changes to KytyPS5 |
| `scripts/build-rootfs.sh` | Builds the system image for PS4 Multiboot |
| `docker/` | Build environments for both |
| `overlay/` | Files added to the system: session, home screen, settings, USB and PS4 drive mounts, controller pairing |
| `tools/` | Logo converter, controller test ROM, `extract-code.py` (the code of a PS5 SELF/ELF) |
| `tools/jaguar-test/` | Checks patch `0004`'s replacements against the real instructions |

## Credits

- [KytyPS5](https://github.com/KytyPS5/KytyPS5), the PS5 emulator (GPL-2.0)
- [Mesa](https://mesa3d.org), and the PS4 GPU patches by fail0verflow, DionKill and striker91n
- The PS4 Linux kernel developers ([sony-jaguar-devs/ps4-linux](https://github.com/sony-jaguar-devs/ps4-linux))

## License

Copyright (C) 2026 [Chokri Hammedi (blue0x1)](https://github.com/blue0x1).

GPL-2.0 (see `LICENSE`). KytyPS5, Mesa and the Linux kernel are under their own licenses. PlayStation is a trademark of Sony Interactive Entertainment; this project is not affiliated with Sony.
