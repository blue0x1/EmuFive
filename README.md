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
6. Put your games in one of the places below. A game is a folder with `eboot.bin` (and `sce_sys`), or a ZArchive (`.zar`) dump. Package files (`.pkg`, fpkg) can't be installed or run: extract the game first.

After installing, run the payload to start EmuFive (with other systems installed, the PS4 Multiboot menu comes first). To reinstall, delete `/user/home/ps5-ps4.img` over FTP and run the payload. Updates: Settings, System, Software update.

### Using it

- **Home screen:** your games as tiles. Pick one and press Play. OPTIONS on a game: favorite, hide, its settings, trophies and play time.
- **PS button in a game:** pause menu (Resume, Home, Close the game, volume, power).
- **Screenshots:** PS + Square, or Share. See them in Media; Triangle shows a QR code to open one on your phone.
- **Internet:** a web browser tile, used with the controller.
- **Settings:** Wi-Fi, appearance, controllers, profiles (up to 8), menu language, date and time, backup.
- **Controllers:** a DualShock 4 on a cable, or over Bluetooth (hold SHARE + PS until the light bar double-blinks).
- **Login:** `ps5` / `ps5` over SSH or on tty2. The emulator log is `~/kytyps5.log`.

### Where games can be

- **USB drive:** the `PS5` folder at the top of the drive (exFAT is best; NTFS works too).
- **PS4 drive:** `/user/home/PS5`, copied with GoldHEN FTP (not when EmuFive itself is on a USB drive).
- **A PC:** a shared folder on Windows or Linux. In Settings, turn on **Use games from PC**, set the address, share and login, then Connect.

## Games

This project contains no PS5 system software and no games. Use only games you own and dumped yourself.

Games that work:

| Game | Console | EmuFive | Result |
|---|---|---|---|
| God of War Sons of Sparta | PS4 Pro | 1.0.0 | Playable, about 40 FPS and more |
| Hollow Knight: Silksong | PS4 Pro | 1.0.1 | Playable, 60 FPS |
| Plants vs. Zombies: Replanted | PS4 Pro | 1.0.4 | Playable, locked 60 FPS |
| Vampire Survivors | PS4 Slim | 1.0.4 | Playable, stable 60 FPS |
| My Little Puppy | PS4 Slim | 1.0.6 | Runs, 3–15 FPS (20–25 in empty areas) |
| DREDGE | PS4 Pro | 1.0.8 | Playable |
| Teardown | PS4 Pro | 1.0.9 | Runs, 9–12 FPS in game (about 20 in light scenes) with GPU-shared memory |
| Invincible VS | PS4 Pro | 1.0.9 | Starts, 4–5 FPS; not playable yet |

Games that don't work yet (a newer version may fix them):

| Game | Console | EmuFive | Result |
|---|---|---|---|
| DRAGON BALL: Sparking! ZERO | PS4 Pro | 1.0.4 | Stops after the first splash screen (mesh shaders) |
| Hello Neighbor | PS4 Pro | 1.0.4 | Stops at start (mesh shaders) |
| Need for Speed Unbound | PS4 Slim | 1.0.6 | Crashes at start (unsupported depth copy) |
| V Rising | PS4 Pro | 1.0.8 | Crashes at start |

Tested a game? Open an [issue](https://github.com/blue0x1/EmuFive/issues) with the game, its title ID, your console model, the EmuFive version and how it ran. Games that don't work are useful too (for example "doesn't start" or "crashes in the menu"): they go in the table, so others don't try the same game.

## Changelog

### Next (test build)

- New, on by default: GPU-shared guest memory (Settings > Games > GPU-shared game memory). Game memory is put in memory the PS4's GPU reads and writes in place, so buffers are no longer copied, tracked page by page, or read back. Teardown on a PS4 Pro: menu scene from 2.1 to 7 FPS, in game 9–12 FPS.
- Video clips: PS + Triangle starts and stops recording, in a game too (720p or 1080p at 30 FPS, with sound). They are saved on the PS4 (`~/Videos`) or, if set in Settings > Storage, in `PS5-videos` on the USB drive. Media shows and plays them, and Share sends them to a phone like screenshots. The PS4's video encoder can't be used under Linux, so the CPU encodes: about one core for 720p.
- A game's menu (OPTIONS on the home screen) has Game info: title ID, content ID, region, version, age rating, required system software, SDK, size on the drive and more.

### 1.0.8 (2026-11-16)

- Improved: games with very large buffers run much faster. Only small buffers are now uploaded whole each frame; large ones are tracked by page again. Teardown on a PS4 Pro went from under 1 FPS to about 2.4 FPS. Teardown also needs 5 GB of GPU memory: use the `bootargs.txt` of PS4 Multiboot v1.5.0-beta-5.

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
  
## Support the project

If EmuFive is useful to you, you can support the project with Bitcoin:

BTC: `bc1q7w5ns9vsguseppllpy609yhwrtq3v56g94mjde`

## License

Copyright (C) 2026 [Chokri Hammedi (blue0x1)](https://github.com/blue0x1).

GPL-2.0 (see `LICENSE`). KytyPS5, Mesa and the Linux kernel are under their own licenses. PlayStation is a trademark of Sony Interactive Entertainment; this project is not affiliated with Sony.
