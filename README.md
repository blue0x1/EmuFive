<h1 align="center">PS5 on PS4</h1>

<p align="center">
  <img src="https://img.shields.io/badge/platform-PS4-003791?logo=playstation&logoColor=white" alt="Platform: PS4">
  <img src="https://img.shields.io/badge/status-experimental-red" alt="Status: experimental">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--2.0-blue" alt="License: GPL-2.0"></a>
</p>

The [KytyPS5](https://github.com/KytyPS5/KytyPS5) PS5 emulator on a jailbroken PlayStation 4: Linux, the PS4's own GPU through Vulkan, and an emulator build made for the PS4's CPU.

Created by **[Chokri Hammedi (blue0x1)](https://github.com/blue0x1)**. Built on [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot).

> **Status: experimental research.** On a PS4 Pro, a native PS5 homebrew app (Snes9x PS5, rebuilt for the PS4's CPU) runs in KytyPS5 and draws its screen. PS5 games do not run, and may never run at a playable speed; see [The CPU problem](#the-cpu-problem).

## How it works

- **[PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot)** starts Linux on the PS4 and installs Linux systems on its internal drive, from the controller.
- **PS4 Mesa**, part of PS4 Multiboot, gives the PS4 GPU (Liverpool on the PS4 and Slim, Gladius on the Pro) Vulkan 1.3. KytyPS5 needs sparse resources, which RADV offers on this GPU with `RADV_EXPERIMENTAL=sparse`.
- **KytyPS5**, upstream at a pinned commit with this project's patches (`patches/kytyps5/`), built with `-march=btver2` for the PS4's AMD Jaguar CPU. The official build uses AVX2 and stops with "Illegal instruction" on the PS4.
  - `0001`: the `KYTY_HOST_ARCH` build option (the CPU the emulator is compiled for).
  - `0002`: a C library for homebrew. PS5 homebrew built with the ps5-native-app-boilerplate ships a stand-in `sce_module/libc.prx` whose functions all return 0 (the console uses its own C library), so in KytyPS5 its `malloc` failed. The patch adds the C library functions such homebrew imports and uses them only for such a stand-in module.
- **PS5 on PS4** packs all of it into a small Linux system that boots straight into the emulator, full screen, with no desktop. It installs through PS4 Multiboot like any other system.

## The CPU problem

KytyPS5 does not emulate the PS5's CPU: it runs the game's own x86-64 code directly. PS5 games are built for the PS5's Zen 2 CPU and use AVX2, BMI2 and FMA instructions throughout. The PS4's Jaguar CPU has none of them, so game code stops at the first such instruction.

Running real games needs a translator in KytyPS5's guest patcher that rewrites those instructions into ones the Jaguar has. That is months of work, and the Jaguar is far slower than the PS5's CPU, so expect a few frames per second at best.

## Plan

| Step | Status |
|---|---|
| Vulkan on the PS4 GPU meets KytyPS5's requirements | Done (`RADV_EXPERIMENTAL=sparse`) |
| KytyPS5 built for the PS4's CPU | Done (`KYTY_HOST_ARCH=btver2`) |
| KytyPS5 starts on the PS4 and sets up the GPU | Done, PS4 Pro |
| PS5 on PS4 system image, installs through PS4 Multiboot | Done, PS4 Pro |
| A PS5 homebrew app without AVX2 runs and draws | Done: Snes9x PS5 2.11 rebuilt for btver2, PS4 Pro |
| Controller, `/data` and USB storage, loading a game in that app | Done on a PC test build (same patches); PS4 next |
| AVX2, BMI2 and FMA translation for game code | Research |
| Game picker with the controller | Later |

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
3. Put the PS5 program in the `PS5` folder of a USB drive: a folder with `eboot.bin`, or a ZArchive (`.zar`) dump. The first one found runs; set `PS5_GAME` in `/etc/ps5-on-ps4.conf` to choose another.

The system needs no keyboard:

- With no program on the USB drive it waits, and starts the program as soon as a drive with one is plugged in.
- The program sees the USB drive as `/mnt/usb0` and a folder of the system (`~/data`, kept between starts) as `/data`. For Snes9x PS5, ROMs go in `snes9x/roms` on the USB drive or in `~/data/snes9x/roms`.
- When the program quits, the PS4 turns off (`PS5_POWEROFF_ON_EXIT`).
- If the emulator stops with an error, the reason is shown and it starts again; after 3 errors in a row the PS4 turns off.
- Controllers: a DualShock 4 on a cable, or over Bluetooth after holding SHARE + PS until the light bar double-blinks.

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
| `overlay/` | Files added to the system: session, settings, USB mount, controller pairing |
| `tools/` | Logo converter, controller test ROM |

## Credits

- [KytyPS5](https://github.com/KytyPS5/KytyPS5), the PS5 emulator (GPL-2.0)
- [Mesa](https://mesa3d.org), and the PS4 GPU patches by fail0verflow, DionKill and striker91n
- The PS4 Linux kernel developers ([sony-jaguar-devs/ps4-linux](https://github.com/sony-jaguar-devs/ps4-linux))

## License

Copyright (C) 2026 [Chokri Hammedi (blue0x1)](https://github.com/blue0x1).

GPL-2.0 (see `LICENSE`). KytyPS5, Mesa and the Linux kernel are under their own licenses. PlayStation is a trademark of Sony Interactive Entertainment; this project is not affiliated with Sony.
