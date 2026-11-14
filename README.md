<h1 align="center"><img src="assets/emufive-logo.png" alt="EmuFive" width="480"></h1>

<p align="center">
  <img src="https://img.shields.io/badge/platform-PS4-003791?logo=playstation&logoColor=white" alt="Platform: PS4">
  <img src="https://img.shields.io/badge/status-experimental-red" alt="Status: experimental">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--2.0-blue" alt="License: GPL-2.0"></a>
</p>

<p align="center">
  <b>EN</b> · <a href="README.ar.md">AR</a> · <a href="README.zh-CN.md">ZH</a> · <a href="README.fr.md">FR</a> · <a href="README.es.md">ES</a> · <a href="README.de.md">DE</a> · <a href="README.it.md">IT</a> · <a href="README.pt-BR.md">PT</a> · <a href="README.tr.md">TR</a>
</p>

A PS5 emulator for the PS4.

Created by **[Chokri Hammedi (blue0x1)](https://github.com/blue0x1)**. Built on [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot).

> **Status: experimental research.** On a PS4 Pro, "Sons of Sparta" runs at about 40 FPS and more. KytyPS5 rewrites the PS5-only CPU instructions in game code (patch `0004`). Other games are still being tested, and many are slow for now. See [The CPU problem](#the-cpu-problem).

<p align="center"><img src="assets/home-screen.png" alt="The EmuFive home screen on a PS4 Pro, with God of War Sons of Sparta selected" width="900"></p>

<p align="center">
  <b><a href="#installing">Installing</a></b> · <b><a href="#games">Games</a></b> · <b><a href="#changelog">Changelog</a></b> · <a href="#how-it-works">How it works</a> · <a href="#the-cpu-problem">The CPU problem</a> · <a href="#plan">Plan</a> · <a href="#building">Building</a> · <a href="#credits">Credits</a>
</p>

## How it works

- **[PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot)** starts Linux on the PS4 and installs Linux systems on its internal drive, from the controller.
- **PS4 Mesa**, part of PS4 Multiboot, gives the PS4 GPU (Liverpool on the PS4 and Slim, Gladius on the Pro) Vulkan 1.3. KytyPS5 needs sparse resources, which RADV offers on this GPU with `RADV_EXPERIMENTAL=sparse`.
- **KytyPS5**, upstream at a pinned commit with this project's patches (`patches/kytyps5/`), built with `-march=btver2` for the PS4's AMD Jaguar CPU. The official build uses AVX2 and stops with "Illegal instruction" on the PS4.
  - `0001`: the `KYTY_HOST_ARCH` build option (the CPU the emulator is compiled for).
  - `0002`: a C library for homebrew. PS5 homebrew built with the ps5-native-app-boilerplate ships a stand-in `sce_module/libc.prx` whose functions all return 0 (the console uses its own C library), so in KytyPS5 its `malloc` failed. The patch adds the C library functions such homebrew imports and uses them only for such a stand-in module.
  - `0003`: more for homebrew: files and folders, system calls, the foreground user, and extra mounts (`KYTY_MOUNTS`).
  - `0004`: PS5 code on the PS4's CPU. Every AVX2, FMA and BMI2 instruction is rewritten into SSE4.2/AVX/BMI1 code when a module loads; one that cannot be rewritten there is replaced the first time it runs. See [The CPU problem](#the-cpu-problem).
- **EmuFive** packs all of it into a small Linux system that boots straight into the emulator, full screen, with no desktop. It installs through PS4 Multiboot like any other system.

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
| EmuFive system image, installs through PS4 Multiboot | Done, PS4 Pro |
| A PS5 homebrew app without AVX2 runs and draws | Done: Snes9x PS5 2.11 rebuilt for btver2, PS4 Pro |
| Controller, `/data` and USB storage, loading a game in that app | Done on a PC test build (same patches); PS4 next |
| AVX2, BMI2 and FMA translation for game code | Done (`0004`), checked on a PC |
| A PS5 game runs on the PS4 | Done: God of War Sons of Sparta, about 40 FPS and more, PS4 Pro |
| Hollow Knight: Silksong runs on the PS4 | Done since 1.0.1 (patches `0006` and `0007`), PS4 Pro |
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

EmuFive installs through [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot), like any other Linux system.

You need:

- A jailbroken PS4 with **GoldHEN** (for its FTP server and payload loader).
- A PC on the same network with an FTP client (for example FileZilla).
- About 28 GB free on the PS4 (a 16 GB disk, and 10 GB always left free for the PS4), or a USB drive of 8 GB or more.
- A DualShock 4 (on a USB cable, or paired over Bluetooth later).

Steps:

1. From the [PS4 Multiboot releases](https://github.com/blue0x1/ps4-multiboot/releases), download `bzImage`, `initramfs.cpio.gz`, `bootargs.txt` and `linux-2048mb.bin`. (`ps4-mesa.tar.xz` is not needed: EmuFive has PS4 Mesa built in.)
2. From the [EmuFive releases](https://github.com/blue0x1/EmuFive/releases), download `ps5-ps4-rootfs.tar.xz` (or build it, see [Building](#building)). Keep its name: PS4 Multiboot finds systems by the `-ps4-rootfs` in it.
3. Turn on GoldHEN's FTP server and copy the files to the PS4 (port 2121):

   | File | Folder on the PS4 |
   |---|---|
   | `bzImage`, `initramfs.cpio.gz`, `bootargs.txt` | `/data/linux/boot/` |
   | `ps5-ps4-rootfs.tar.xz` | `/user/home/` |
   | `linux-2048mb.bin` | `/data/payloads/` |

4. Run `linux-2048mb.bin` from GoldHEN's payload menu.

   > **Be patient:** after the payload starts, the TV can show **"No signal" or a black screen for 1 to 2 minutes** while Linux starts. This is normal.

5. In the PS4 Multiboot menu, pick **EmuFive**, then **Install to PS4** or **Install to USB drive**. It takes a few minutes.
6. Put your games in one of the places below. A game is a folder with `eboot.bin` (and `sce_sys`), or a ZArchive (`.zar`) dump.

After that, run the payload to start EmuFive: with only EmuFive installed it starts straight away, with other systems too the PS4 Multiboot menu appears first. Turn off or restart from the home screen to go back to the PS4 system. To install EmuFive again, delete `/user/home/ps5-ps4.img` over FTP and run the payload.

Updates come from the EmuFive releases: Settings, System, Software update (no reinstall needed).

The system starts in the home screen and needs no keyboard:

- The games show up as tiles, each labeled with where it is: **USB**, **PS4** or **PC**. Pick one and press Play; when it quits, the home screen comes back.
- At the top: Wi-Fi (with an on-screen keyboard for the password) and Settings, and two tabs, **Games** and **Media** (L1 / R1). Media shows your screenshots; open one, and Square deletes it.
- OPTIONS on a game: favorite, hide, its own settings, its trophies and how long you played it.
- **Internet**, the tile after the games: a web browser used with the controller. The left stick (or the touchpad) moves the pointer and X clicks; the right stick scrolls; O or L1 goes back, R1 forward; L2 and R2 zoom. Triangle types an address or a search, and choosing a text box on a page opens the on-screen keyboard. OPTIONS opens the menu: bookmarks, start page, zoom, search engine (Google, DuckDuckGo or Bing), Mobile sites (lighter pages) and clearing the history and cookies. The PS button goes back to the home screen, and the same page opens next time. It is WebKitGTK showing one page at a time, about 450 MB of memory with a page of text and more with video sites; the home screen closes while it runs, and a paused game has to be closed first. Downloads, uploads, the camera, the microphone and the location are refused. Bookmarks are in `~/.config/ps5-on-ps4/browser.json`, cookies in `~/.local/share/ps5-browser`.
- The PS button during a game pauses it and opens the quick menu: Resume, **Home** (the home screen, with the game still paused: PS or Resume goes back to it; starting another game asks first, then closes it), Close the game, volume, power.
- Screenshots: PS + Square, or Share, also in a game. They go to `PS5-screenshots` on the USB drive (or `~/Screenshots` without one), with a small notice in the corner. To get one on your phone, open it in Media and press Triangle (Share): scan the QR code with the phone (on the same network) to open it there, then save or share it. The PS4 serves that one picture, at a random address, only while the code is on screen. QR codes come from `python3-segno`.
- Settings, Appearance: accent color, theme (dark, midnight, light), background (the game's art, a gradient, a solid color or your own picture from the USB drive), background dim, floating orbs, animations, tile size and shape, text size and font, clock, what the top bar shows (the battery is the controller's), menu sounds, rumble, button hints, screen edges (overscan) and a screensaver.
- Settings, Controllers: light bar color and brightness, vibration on or off and its strength, the controller's microphone on or off (with the controller on a USB cable; Linux has no controller sound over Bluetooth), swapping X and O, and a test page for every button and stick. Settings, Games: defaults for all games, game language, HDR and frame pacing. Settings, Date and time: set automatically from the internet (the default) or by hand. Settings, System: the menu language (English, Arabic, French, Turkish, Spanish, German, Italian or Portuguese of Brazil), temperature and CPU load, back up the settings to the USB drive, or reset them all.
- Profiles (Settings, Profile, and Switch profile in the quick menu): up to 8, each with its own name, avatar, saves, trophies and play time. With more than one, "Who's playing?" opens at the start. Each profile has its own KytyPS5 folder (`~/.kytyps5/users/<ID>`, the first profile keeps `~/.kytyps5`), with the shader cache shared.
- Notices in the top-left corner, also in a game: a screenshot was saved, a controller connected (with its connection and battery level), the controller battery is low (15%). The top bar battery is green, yellow or red by level, with a lightning bolt while charging.
- Running out of memory: a 4 GB swap file on the system disk (`ps5-swap.service`, made once when there is room) lets a big game slow down instead of freezing the PS4, and if memory and swap still run out, the game is closed before the PS4 freezes and the home screen says why.
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

Tested games:

| Game | Console | Result |
|---|---|---|
| God of War Sons of Sparta | PS4 Pro | Playable, about 40 FPS and more |
| Hollow Knight: Silksong | PS4 Pro | Playable, 50 to 60 FPS |
| Plants vs. Zombies: Replanted | PS4 Pro | Playable, locked 60 FPS |
| Vampire Survivors | PS4 Slim | Playable, stable 60 FPS |
| Spider-Man 2 | | Not tested yet |

Tested a game? Open an [issue](https://github.com/blue0x1/EmuFive/issues) with the game, your console model and how it ran.

## Changelog

### 1.0.6 (2026-11-14)

- Improved: the home screen uses much less CPU while nobody uses it (at 4K about a third of one core, it was a whole core), so the PS4 runs cooler and quieter.

To update from 1.0.3 or earlier, start the update once by hand, since the old Software update cannot: turn on SSH in Settings, connect with `ssh ps5@<PS4 address>` (password `ps5` unless you changed it) and run

```bash
sudo systemd-run --unit=emufive-update --collect /opt/ps5-on-ps4/bin/ps5-update install
```

It installs every update you are missing (from 1.0.0 or 1.0.1 that includes 1.0.2's browser packages, about 110 MB), then restart from the home screen. From 1.0.4 on, Software update in Settings works. New installs use the `ps5-ps4-rootfs.tar.xz` of the 1.0.6 release.

## Project layout

| Path | Contents |
|---|---|
| `scripts/build-kyty.sh` | Builds KytyPS5 (upstream plus `patches/kytyps5/`) for the PS4's CPU |
| `patches/kytyps5/` | This project's changes to KytyPS5 |
| `scripts/build-rootfs.sh` | Builds the system image for PS4 Multiboot |
| `scripts/make-release.sh` | Makes the update pack of a release (Settings, System, Software update installs it) |
| `scripts/updates/` | Scripts an update runs on the PS4 after its files are in (`--post`) |
| `docker/` | Build environments for both |
| `overlay/` | Files added to the system: session, home screen, settings, USB and PS4 drive mounts, controller pairing |
| `tools/` | Logo converter, controller test ROM, `extract-code.py` (the code of a PS5 SELF/ELF) |
| `tools/jaguar-test/` | Checks patch `0004`'s replacements against the real instructions |

## Special thanks

- [KytyPS5](https://github.com/KytyPS5/KytyPS5), the PS5 emulator EmuFive is based on (GPL-2.0)
- [Kyty](https://github.com/InoriRus/Kyty) by InoriRus, the emulator KytyPS5 is based on

## Credits

- [Mesa](https://mesa3d.org), and the PS4 GPU patches by fail0verflow, DionKill and striker91n
- The PS4 Linux kernel developers ([rmuxnet/linux](https://gitlab.com/rmuxnet/linux))
  
## License

Copyright (C) 2026 [Chokri Hammedi (blue0x1)](https://github.com/blue0x1).

GPL-2.0 (see `LICENSE`). KytyPS5, Mesa and the Linux kernel are under their own licenses. PlayStation is a trademark of Sony Interactive Entertainment; this project is not affiliated with Sony.
