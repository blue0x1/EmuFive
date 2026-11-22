# Troubleshooting

<p align="center">
  <b>EN</b> · <a href="TROUBLESHOOTING.ar.md">AR</a> · <a href="TROUBLESHOOTING.zh-CN.md">ZH</a> · <a href="TROUBLESHOOTING.fr.md">FR</a> · <a href="TROUBLESHOOTING.es.md">ES</a> · <a href="TROUBLESHOOTING.de.md">DE</a> · <a href="TROUBLESHOOTING.it.md">IT</a> · <a href="TROUBLESHOOTING.pt-BR.md">PT</a> · <a href="TROUBLESHOOTING.tr.md">TR</a>
</p>

The problems people reported in the [issues](https://github.com/blue0x1/EmuFive/issues), with the fixes that worked for them. Try the steps in order. Still stuck? Open an issue with what's listed in [What to send](#what-to-send).

- [Check the files first](#check-the-files-first)
- [Black screen or "No signal" after the payload](#black-screen-or-no-signal-after-the-payload)
- [Black screen after the menu or the EmuFive logo](#black-screen-after-the-menu-or-the-emufive-logo)
- [Green screen, wrong colors or flickering](#green-screen-wrong-colors-or-flickering)
- [The PS4 turns off, or the light stays white](#the-ps4-turns-off-or-the-light-stays-white)
- ["No Linux install or archive found"](#no-linux-install-or-archive-found)
- [Installing takes very long](#installing-takes-very-long)
- [EmuFive doesn't start after a stopped install](#emufive-doesnt-start-after-a-stopped-install)
- [It only works with the USB drive plugged in](#it-only-works-with-the-usb-drive-plugged-in)
- [Games don't show up](#games-dont-show-up)
- [An external drive isn't found](#an-external-drive-isnt-found)
- [The controller doesn't work](#the-controller-doesnt-work)
- [A game closes, freezes or runs slowly](#a-game-closes-freezes-or-runs-slowly)
- [How to save the logs](#how-to-save-the-logs)
- [What to send](#what-to-send)

## Check the files first

Most "nothing happens" reports came from one of these:

- **Same release:** `bzImage`, `initramfs.cpio.gz`, `bootargs.txt` and `linux-2048mb.bin` must all come from the same [PS4 Multiboot release](https://github.com/blue0x1/ps4-multiboot/releases) (the newest one is best). Mixed files don't start.
- **Lowercase folder names:** the PS4 sees `LINUX` and `linux` as different folders. The paths must be exactly `/data/linux/boot/bzImage`, `/data/linux/boot/initramfs.cpio.gz` and `/data/linux/boot/bootargs.txt`.
- **The exact archive name:** `/user/home/ps5-ps4-rootfs.tar.xz`. A browser sometimes saves it as `ps5-ps4-rootfs (1).tar.xz`, and then the menu doesn't find it.
- **Binary transfer:** in FileZilla, set Transfer → Transfer type → **Binary** before uploading. A file uploaded in text mode is damaged. Check that each file on the PS4 has the same size as in the release.
- **Our payload:** use `linux-2048mb.bin` from PS4 Multiboot (on firmware 14.02: `linux-2048mb-14.02.bin`). It works on firmware 5.05 to 14.02. Other Linux payloads are not supported.

## Black screen or "No signal" after the payload

After the payload starts, the TV shows "No signal" or a black screen for **1 to 2 minutes** while Linux starts. This is normal. The screen and the controller going off right after the payload is normal too: the PS4 system shuts down and Linux takes over.

**Don't press the PS button while the screen is dark**: it turns the PS4 off. With only EmuFive on the PS4, the installer starts by itself after 60 seconds, so it may already be installing.

If nothing shows after 3 minutes:

1. Connect the PS4 **directly** to the TV, with no HDMI switch, AV receiver or capture card.
2. On the PS4, turn off **Settings → System → Enable HDCP**, then run the payload again.
3. Try another HDMI cable and another HDMI port.
4. Try another TV or monitor once. Some TVs don't take the PS4's Linux signal, and another screen shows whether the problem is the TV.
5. Still nothing? Save the [PS4BOOT log](#the-ps4boot-stick-boot-problems) and open an issue. Tell us if the TV says **"No signal"** or is on but black.

## Black screen after the menu or the EmuFive logo

If you see the PS4 Multiboot menu or EmuFive's logo, and then it goes black, EmuFive switched to a mode your TV prefers but the PS4 can't send.

1. Update EmuFive (Settings → System → Software update).
2. Over FTP, open `/data/linux/boot/bootargs.txt` and add ` emufive.mode=1920x1080@60` at the end of the line. Keep `video=HDMI-A-1:1920x1080@60D` too. The file must stay **one line**.
3. Run the payload again.

Can't update because the screen is black? Connect another TV or monitor once and update, or install EmuFive again with the newest `ps5-ps4-rootfs.tar.xz`.

## Green screen, wrong colors or flickering

A green layer, black shown as green or white as cyan, or flicker: the TV is reading the PS4's signal in the wrong color format.

1. Add ` emufive.mode=1920x1080@60` to `bootargs.txt` (see above).
2. Try another HDMI cable or port. In the TV's settings for that port, switch options like **HDMI UHD Color**, **Enhanced format**, **Deep Colour** or **Input Signal Plus** (on to off, or off to on), and turn off HDMI-CEC (**Anynet+**, **Bravia Sync**...).
3. Try another TV or monitor.

## The PS4 turns off, or the light stays white

- **On 14.02**, the first run of the payload sometimes turns the PS4 off. Run it again: a second run usually works.
- **The light stays white** and nothing happens for 5 minutes: hold the power button to turn the PS4 off, start it again, and run the payload again.
- **A purple light** after installing is normal.
- **The PS4 turns off when you press the PS button** on a black screen: don't press it, wait instead (see above).

## "No Linux install or archive found"

The menu found neither an installed EmuFive nor `ps5-ps4-rootfs.tar.xz`.

1. Check the archive name and place: `/user/home/ps5-ps4-rootfs.tar.xz`, exactly.
2. On a **fat PS4** (CUH-10xx, 11xx or 12xx), PS4 Multiboot v1.5.0-beta.3 to beta.7 didn't find the internal drive. Use the `bzImage` and `initramfs.cpio.gz` from [v1.5.0-beta.8](https://github.com/blue0x1/ps4-multiboot/releases/tag/v1.5.0-beta.8) or newer.

## Installing takes very long

- **Creating the disk** is the first 25% of the bar, and it's the slow part: everything written to the PS4's drive goes through the PS4's disk encryption. Baikal consoles are slower at it. A big disk takes longer, so for a first try pick a smaller one (16 GB is fine). The part after 25% goes faster.
- **Don't turn the PS4 off** while the percentage still moves. If it doesn't move for 30 minutes, open an issue and say where it stopped.
- **Black screen at the end:** if the TV still has a signal, the install most likely finished and EmuFive is starting. If the PS4's power button turns it off normally, EmuFive is running and only the picture is black: see [Black screen after the menu](#black-screen-after-the-menu-or-the-emufive-logo).

## EmuFive doesn't start after a stopped install

If the PS4 was turned off during an install, the half-made disk can stay behind. The error screen says **"The EmuFive disk is incomplete"**, or the log says `is a hole`.

1. Delete `/user/home/ps5-ps4.img` over FTP. Keep `ps5-ps4-rootfs.tar.xz`.
2. Run the payload and install again. Let it finish without turning the PS4 off.

## It only works with the USB drive plugged in

You picked **Install to USB drive**, so EmuFive lives on that drive and needs it. To have it on the PS4 instead: unplug the drive, run the payload, and pick **Install to PS4**.

## Games don't show up

A game is a **folder** with `eboot.bin` and `sce_sys` inside, or a single `.zar` file. `.pkg` and fpkg files can't be used: extract the game first. Use dumps of games you own.

On a USB drive, it has to look like this:

```
USB drive (exFAT, one partition; NTFS works too)
└── PS5/                      <- exactly "PS5", in capitals, at the top of the drive
    ├── PPSA01234/            <- one folder per game (any name)
    │   ├── eboot.bin         <- directly in the game folder
    │   ├── sce_sys/
    │   │   └── param.json    <- gives the game's name and picture
    │   └── ...
    └── MyGame.zar            <- a .zar dump, as a single file
```

Common mistakes:

- `ps5/` or `Ps5/`: the name must be `PS5` exactly.
- `Games/PS5/...`: the `PS5` folder must be at the top of the drive.
- `PS5/PPSA01234/PPSA01234/eboot.bin`: an extra folder level (common after unzipping). Move the inner folder up.
- `PS5/eboot.bin`: the game files loose in `PS5` without their own folder.
- Two games in one folder: only one shows. The name on the tile comes from `sce_sys/param.json`, not from the folder name, so give each game its own folder.

On the PS4 drive, the folder is `/user/home/PS5`, and it only works when EmuFive is installed on the PS4 (not on a USB drive). Copy games with GoldHEN FTP from the PS4 system, then start EmuFive: it reads that folder when it starts.

Keep only the game drive plugged in. Unplug the `PS4BOOT` log stick while you play.

## An external drive isn't found

- External SSDs and hard drives work from EmuFive 1.0.5. Update first.
- A drive that had Linux on it before may still not show after a normal format. Delete all its partitions (Windows: Disk Management), then make one **exFAT** partition.
- If EmuFive is installed on one USB drive, games go on a second USB drive (from EmuFive 1.0.4).

## The controller doesn't work

- **In the PS4 Multiboot menu and on the install and error screens**, the controller works only **on a USB cable**. Bluetooth starts later, in EmuFive.
- **Bluetooth** must be paired once with EmuFive, since the PS4 system's pairing doesn't carry over. Unplug the cable, hold **SHARE + PS** until the light bar double-blinks, and wait a few seconds. If it doesn't connect, use Settings → Controllers → Pair a new controller.
- Use a cable that carries data. Some cables only charge.
- On **Baikal** consoles (many CUH-71xx/72xx Pros and newer Slims; see Settings → System → System Information), USB needs PS4 Multiboot v1.5.0-beta.7 or newer.

## A game closes, freezes or runs slowly

- **"The game stopped (error code 65)" with `ErrorDeviceLost`:** the PS4's GPU hung on the game's drawing. It's common with heavy Unreal Engine games, which aren't playable yet. Send the [game log](#game-logs) if you'd like us to look.
- **Out of memory:** a PS5 game can use up to about 12.5 GB, and Linux on the PS4 has about 6 GB. EmuFive closes the game before the PS4 freezes. Turn off Settings → Games → **GPU-shared game memory** and try again. EmuFive makes a 4 GB swap file only when its disk has 8 GB free, so free up room if the disk is full.
- **Freezes or a crash in a game:** try once with **GPU-shared game memory** off. It speeds up big 3D games, but it doesn't suit every game (Minecraft freezes with it).
- **Stutter the first time:** the first run of a scene compiles shaders. The second run is smoother.
- **Tearing:** Settings → Games → Frame pacing → **Smooth (no tearing)**.
- **Low FPS:** the PS4's CPU and GPU are much slower than the PS5's. 2D and lighter games run well; heavy 3D games often load and show menus, then run very slowly or stay black in game. A PS4 Pro is about twice as fast as a Slim. See the [Games](README.md#games) table before you try a big game.

## How to save the logs

### The PS4BOOT stick (boot problems)

1. Format a USB stick as **FAT32** with the label **`PS4BOOT`** (all caps). Windows can't make FAT32 on sticks bigger than 32 GB: use a smaller stick, or [Rufus](https://rufus.ie) (Boot selection: *Non bootable*, File system: *Large FAT32*, Volume label: `PS4BOOT`). NTFS and exFAT don't work for this.
2. Plug it into the PS4 **before** you run the payload, and leave it in.
3. Run the payload and wait **5 minutes**, even if the screen stays black. If an error screen shows, it saves the details to the stick by itself.
4. Hold the power button to turn the PS4 off. Put the stick in a PC and attach the `.log` files to your issue (`ps4-linux-boot.log`, `ps4-linux-late.log`, `ps4-linux-error.log` or `ps4-linux-rescue.log`).

If the stick stays empty, say so: it means Linux didn't get that far, which helps too.

### Game logs

Right after the game stops, go to Settings → System → **Copy logs to USB**, then attach the files from the `PS5-logs` folder on the USB drive (`kytyps5.log` is the main one). Attach the real file, not a summary.

## What to send

- PS4 model (CUH-xxxx, on the label at the back), firmware, and the southbridge (Settings → System → System Information, e.g. Belize, Baikal, Aeolia).
- The PS4 Multiboot release and the payload file you run.
- Your `bootargs.txt` line.
- Your EmuFive version (Settings → System), and whether it's installed on the PS4 or a USB drive.
- Your TV or monitor model, and what it shows: "No signal", or on but black.
- The PS4's light: white, blue, purple or off.
- The logs from above.
