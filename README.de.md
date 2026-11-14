<h1 align="center"><img src="assets/emufive-logo.png" alt="EmuFive" width="480"></h1>

<p align="center">
  <img src="https://img.shields.io/badge/platform-PS4-003791?logo=playstation&logoColor=white" alt="Platform: PS4">
  <img src="https://img.shields.io/badge/status-experimental-red" alt="Status: experimental">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--2.0-blue" alt="License: GPL-2.0"></a>
</p>

<p align="center">
  <a href="README.md">EN</a> · <a href="README.ar.md">AR</a> · <a href="README.zh-CN.md">ZH</a> · <a href="README.fr.md">FR</a> · <a href="README.es.md">ES</a> · <b>DE</b> · <a href="README.it.md">IT</a> · <a href="README.pt-BR.md">PT</a> · <a href="README.tr.md">TR</a>
</p>

Ein PS5-Emulator für die PS4.

Erstellt von **[Chokri Hammedi (blue0x1)](https://github.com/blue0x1)**. Basiert auf [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot).

> **Status: experimentelle Forschung.** Auf einer PS4 Pro läuft „Sons of Sparta“ mit etwa 40 FPS und mehr. KytyPS5 schreibt die PS5-eigenen CPU-Befehle im Spielcode um (Patch `0004`). Andere Spiele werden noch getestet, und viele sind vorerst langsam. Siehe [Das CPU-Problem](#the-cpu-problem).

<p align="center"><img src="assets/home-screen.png" alt="Der EmuFive-Startbildschirm auf einer PS4 Pro, mit God of War Sons of Sparta ausgewählt" width="900"></p>

<p align="center">
  <b><a href="#installing">Installation</a></b> · <b><a href="#games">Spiele</a></b> · <b><a href="#changelog">Änderungsprotokoll</a></b> · <a href="#how-it-works">So funktioniert es</a> · <a href="#the-cpu-problem">Das CPU-Problem</a> · <a href="#plan">Plan</a> · <a href="#building">Kompilieren</a> · <a href="#credits">Danksagungen</a>
</p>

<a id="how-it-works"></a>
## So funktioniert es

- **[PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot)** startet Linux auf der PS4 und installiert Linux-Systeme auf ihrer internen Festplatte, mit dem Controller.
- **PS4 Mesa**, Teil von PS4 Multiboot, gibt der GPU der PS4 (Liverpool in PS4 und Slim, Gladius in der Pro) Vulkan 1.3. KytyPS5 braucht Sparse Resources, die RADV auf dieser GPU mit `RADV_EXPERIMENTAL=sparse` anbietet.
- **KytyPS5**, das Originalprojekt bei einem festgelegten Commit mit den Patches dieses Projekts (`patches/kytyps5/`), kompiliert mit `-march=btver2` für die AMD-Jaguar-CPU der PS4. Der offizielle Build nutzt AVX2 und bricht auf der PS4 mit „Illegal instruction“ ab.
  - `0001`: die Build-Option `KYTY_HOST_ARCH` (die CPU, für die der Emulator kompiliert wird).
  - `0002`: eine C-Bibliothek für Homebrew. Mit ps5-native-app-boilerplate gebaute PS5-Homebrew bringt ein Ersatzmodul `sce_module/libc.prx` mit, dessen Funktionen alle 0 zurückgeben (die Konsole nutzt ihre eigene C-Bibliothek), daher schlug sein `malloc` in KytyPS5 fehl. Der Patch fügt die C-Bibliotheksfunktionen hinzu, die solche Homebrew importiert, und nutzt sie nur für ein solches Ersatzmodul.
  - `0003`: mehr für Homebrew: Dateien und Ordner, Systemaufrufe, der Benutzer im Vordergrund und zusätzliche Einhängepunkte (`KYTY_MOUNTS`).
  - `0004`: PS5-Code auf der CPU der PS4. Jeder AVX2-, FMA- und BMI2-Befehl wird beim Laden eines Moduls in SSE4.2/AVX/BMI1-Code umgeschrieben; einer, der dort nicht umgeschrieben werden kann, wird beim ersten Ausführen ersetzt. Siehe [Das CPU-Problem](#the-cpu-problem).
- **EmuFive** packt all das in ein kleines Linux-System, das direkt in den Emulator startet, im Vollbild, ohne Desktop. Es wird wie jedes andere System über PS4 Multiboot installiert.

<a id="the-cpu-problem"></a>

## Das CPU-Problem

KytyPS5 emuliert die CPU der PS5 nicht: Es führt den x86-64-Code des Spiels direkt aus. PS5-Spiele sind für die Zen-2-CPU der PS5 kompiliert und nutzen überall AVX2-, BMI2- und FMA-Befehle. Die Jaguar-CPU der PS4 hat keinen davon, also bleibt der Spielcode beim ersten solchen Befehl stehen.

Patch `0004` fügt das dem Gast-Befehlspatcher von KytyPS5 hinzu. Wenn der Host-CPU AVX2, FMA oder BMI2 fehlt, wird jeder solche Befehl durch Code mit derselben Wirkung ersetzt: 256-Bit-Ganzzahloperationen als zwei 128-Bit-Hälften, Permutationen über die Hälften hinweg mit AVX-Verschiebe- und Mischbefehlen, elementweise Shifts ein Element nach dem anderen, FMA in doppelter Genauigkeit berechnet, Gathers ein Element nach dem anderen, BMI2 mit gesicherten Registern. Der Sprung zum Ersatz steht dort, wo der Befehl war; ein Befehl, der für einen Sprung zu kurz ist, an einer Stelle, die der Patcher nicht umordnen kann, löst einen Fehler aus und wird zur Laufzeit ersetzt.

`tools/jaguar-test/` prüft jeden Ersatz auf einem PC, der diese Befehle hat: Es nimmt jede Befehlsform, die im Code eines Programms vorkommt, führt Original und Ersatz aus demselben zufälligen Zustand aus und vergleicht alle Register, Flags und den Speicher. Die Formen aus den bisher getesteten Programmen stimmen überein: 287 in God of War Sons of Sparta (Gathers und VFMADDSUB eingeschlossen) und 227 in den zuvor getesteten Programmen. Ausnahmen sind seltene Unterschiede im letzten Bit bei FMA (einfache Genauigkeit wird zweimal gerundet, doppelte ist eine Multiplikation und eine Addition) und ein NaN-Sonderfall bei 0 mal Unendlich.

Der Jaguar ist immer noch viel langsamer als die CPU der PS5, und die Ersetzungen kommen hinzu, daher kann selbst ein Spiel, das läuft, langsam laufen.

<a id="plan"></a>
## Plan

| Schritt | Status |
|---|---|
| Vulkan auf der PS4-GPU erfüllt die Anforderungen von KytyPS5 | Erledigt (`RADV_EXPERIMENTAL=sparse`) |
| KytyPS5 für die CPU der PS4 kompiliert | Erledigt (`KYTY_HOST_ARCH=btver2`) |
| KytyPS5 startet auf der PS4 und richtet die GPU ein | Erledigt, PS4 Pro |
| EmuFive-Systemabbild, wird über PS4 Multiboot installiert | Erledigt, PS4 Pro |
| Eine PS5-Homebrew-App ohne AVX2 läuft und zeichnet | Erledigt: Snes9x PS5 2.11 für btver2 neu kompiliert, PS4 Pro |
| Controller, `/data`- und USB-Speicher, ein Spiel in dieser App laden | Erledigt in einem PC-Testbuild (gleiche Patches); PS4 als Nächstes |
| AVX2-, BMI2- und FMA-Übersetzung für Spielcode | Erledigt (`0004`), auf einem PC geprüft |
| Ein PS5-Spiel läuft auf der PS4 | Erledigt: God of War Sons of Sparta, etwa 40 FPS und mehr, PS4 Pro |
| Hollow Knight: Silksong läuft auf der PS4 | Erledigt seit 1.0.1 (Patches `0006` und `0007`), PS4 Pro |
| Startbildschirm: ein Spiel mit dem Controller wählen; WLAN; Einstellungen | Erledigt, auf einem PC geprüft |
| Spiele vom USB-Laufwerk, der PS4-Festplatte oder einer PC-Freigabe | Erledigt, auf einem PC geprüft; PS4 als Nächstes |

<a id="building"></a>

## Kompilieren

Benötigt Docker, git und das PS4 Mesa aus PS4 Multiboot (`../PS4-Multiboot/out/ps4-mesa.tar.xz`, dort mit `make mesa` gebaut). `build-kyty.sh` klont KytyPS5 beim ersten Mal nach `build/kytyps5`, setzt es dann bei jedem Build auf den festgelegten Commit zurück und wendet die Patches an.

```bash
scripts/build-kyty.sh      # out/kytyps5-ps4.tar.xz
scripts/build-rootfs.sh    # out/ps5-ps4-rootfs.tar.xz
```

`PS4_MESA` und `KYTY` geben `build-rootfs.sh` andere Pfade an.

<a id="installing"></a>

## Installation

EmuFive wird über [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot) installiert, wie jedes andere Linux-System.

Du brauchst:

- Eine PS4 mit Jailbreak und **GoldHEN** (für den FTP-Server und den Payload-Loader).
- Einen PC im selben Netzwerk mit einem FTP-Client (zum Beispiel FileZilla).
- Etwa 28 GB frei auf der PS4 (eine 16-GB-Platte, und 10 GB bleiben immer frei für die PS4) oder ein USB-Laufwerk mit 8 GB oder mehr.
- Einen DualShock 4 (am USB-Kabel oder später über Bluetooth gekoppelt).

Schritte:

1. Lade aus den [PS4-Multiboot-Releases](https://github.com/blue0x1/ps4-multiboot/releases) `bzImage`, `initramfs.cpio.gz`, `bootargs.txt` und `linux-2048mb.bin` herunter. (`ps4-mesa.tar.xz` wird nicht gebraucht: EmuFive enthält PS4 Mesa bereits.)
2. Lade aus den [EmuFive-Releases](https://github.com/blue0x1/EmuFive/releases) `ps5-ps4-rootfs.tar.xz` herunter (oder baue es, siehe [Kompilieren](#building)). Behalte den Namen bei: PS4 Multiboot erkennt Systeme am `-ps4-rootfs` darin.
3. Schalte den FTP-Server von GoldHEN ein und kopiere die Dateien auf die PS4 (Port 2121):

   | Datei | Ordner auf der PS4 |
   |---|---|
   | `bzImage`, `initramfs.cpio.gz`, `bootargs.txt` | `/data/linux/boot/` |
   | `ps5-ps4-rootfs.tar.xz` | `/user/home/` |
   | `linux-2048mb.bin` | `/data/payloads/` |

4. Starte `linux-2048mb.bin` aus dem Payload-Menü von GoldHEN.

   > **Hab Geduld:** Nach dem Start des Payloads kann der Fernseher **1 bis 2 Minuten lang „No signal“ oder einen schwarzen Bildschirm** zeigen, während Linux startet. Das ist normal.

5. Wähle im PS4-Multiboot-Menü **EmuFive**, dann **Install to PS4** oder **Install to USB drive**. Das dauert ein paar Minuten.
6. Lege deine Spiele an einen der unten genannten Orte. Ein Spiel ist ein Ordner mit `eboot.bin` (und `sce_sys`) oder ein ZArchive-Dump (`.zar`).

Danach startest du EmuFive mit dem Payload: Ist nur EmuFive installiert, startet es sofort; mit anderen Systemen erscheint zuerst das PS4-Multiboot-Menü. Schalte über den Startbildschirm aus oder neu, um zum PS4-System zurückzukehren. Um EmuFive neu zu installieren, lösche `/user/home/ps5-ps4.img` per FTP und starte den Payload.

Updates kommen aus den EmuFive-Releases: Einstellungen, System, Softwareaktualisierung (keine Neuinstallation nötig).

Das System startet im Startbildschirm und braucht keine Tastatur:

- Die Spiele erscheinen als Kacheln, jede mit ihrem Speicherort: **USB**, **PS4** oder **PC**. Wähle eines und drücke Spielen; wenn es beendet wird, kommt der Startbildschirm zurück.
- Oben: WLAN (mit einer Bildschirmtastatur für das Passwort) und Einstellungen, sowie zwei Reiter, **Spiele** und **Medien** (L1 / R1). Medien zeigt deine Screenshots; öffne einen, und Quadrat löscht ihn.
- OPTIONS auf einem Spiel: Favorit, verbergen, eigene Einstellungen, seine Trophäen und wie lange du es gespielt hast.
- **Internet**, die Kachel nach den Spielen: ein Webbrowser, der mit dem Controller bedient wird. Der linke Stick (oder das Touchpad) bewegt den Zeiger und X klickt; der rechte Stick scrollt; O oder L1 geht zurück, R1 vorwärts; L2 und R2 zoomen. Dreieck tippt eine Adresse oder eine Suche, und die Auswahl eines Textfelds auf einer Seite öffnet die Bildschirmtastatur. OPTIONS öffnet das Menü: Lesezeichen, Startseite, Zoom, Suchmaschine (Google, DuckDuckGo oder Bing), mobile Seiten (leichtere Seiten) und das Löschen von Verlauf und Cookies. Die PS-Taste geht zurück zum Startbildschirm, und beim nächsten Mal öffnet sich dieselbe Seite. Es ist WebKitGTK mit einer Seite zur Zeit, etwa 450 MB Speicher bei einer Textseite und mehr bei Videoseiten; der Startbildschirm schließt sich, während er läuft, und ein pausiertes Spiel muss zuerst beendet werden. Downloads, Uploads, Kamera, Mikrofon und Standort werden abgelehnt. Lesezeichen liegen in `~/.config/ps5-on-ps4/browser.json`, Cookies in `~/.local/share/ps5-browser`.
- Die PS-Taste während eines Spiels pausiert es und öffnet das Schnellmenü: Fortsetzen, **Startbildschirm** (der Startbildschirm, das Spiel bleibt pausiert: PS oder Fortsetzen führt zurück; ein anderes Spiel zu starten fragt zuerst und beendet es dann), Spiel beenden, Lautstärke, Strom.
- Screenshots: PS + Quadrat oder Share, auch im Spiel. Sie landen in `PS5-screenshots` auf dem USB-Laufwerk (oder ohne eines in `~/Screenshots`), mit einem kleinen Hinweis in der Ecke. Um einen aufs Handy zu holen, öffne ihn in Medien und drücke Dreieck (Teilen): Scanne den QR-Code mit dem Handy (im selben Netzwerk), um ihn dort zu öffnen, und speichere oder teile ihn dann. Die PS4 stellt nur dieses eine Bild bereit, unter einer zufälligen Adresse, und nur solange der Code angezeigt wird. Die QR-Codes kommen von `python3-segno`.
- Einstellungen, Darstellung: Akzentfarbe, Design (dunkel, Mitternacht, hell), Hintergrund (das Bild des Spiels, ein Farbverlauf, eine einfarbige Fläche oder dein eigenes Bild vom USB-Laufwerk), Abdunkeln des Hintergrunds, schwebende Kugeln, Animationen, Größe und Form der Kacheln, Textgröße und Schriftart, Uhr, was die obere Leiste zeigt (der Akku ist der des Controllers), Menütöne, Vibration, Tastenhinweise, Bildschirmränder (Overscan) und ein Bildschirmschoner.
- Einstellungen, Controller: Farbe und Helligkeit der Lichtleiste, Vibration an oder aus und ihre Stärke, das Mikrofon des Controllers an oder aus (mit dem Controller am USB-Kabel; Linux hat keinen Controller-Ton über Bluetooth), X und O tauschen, und eine Testseite für jede Taste und jeden Stick. Einstellungen, Spiele: Standardwerte für alle Spiele, Spielsprache, HDR und Bildtaktung. Einstellungen, Datum und Uhrzeit: automatisch aus dem Internet (Standard) oder von Hand. Einstellungen, System: die Menüsprache (Englisch, Arabisch, Französisch, Türkisch, Spanisch, Deutsch, Italienisch oder brasilianisches Portugiesisch), Temperatur und CPU-Last, die Einstellungen auf dem USB-Laufwerk sichern oder alle zurücksetzen.
- Profile (Einstellungen, Profil, und Profil wechseln im Schnellmenü): bis zu 8, jedes mit eigenem Namen, Avatar, Spielständen, Trophäen und Spielzeit. Mit mehr als einem öffnet sich beim Start „Wer spielt?“. Jedes Profil hat seinen eigenen KytyPS5-Ordner (`~/.kytyps5/users/<ID>`, das erste Profil behält `~/.kytyps5`), der Shader-Cache wird geteilt.
- Hinweise in der oberen linken Ecke, auch im Spiel: ein Screenshot wurde gespeichert, ein Controller wurde verbunden (mit Verbindungsart und Akkustand), der Akku des Controllers ist schwach (15 %). Der Akku in der oberen Leiste ist je nach Stand grün, gelb oder rot, mit einem Blitz beim Laden.
- Speicher voll: Eine 4-GB-Swap-Datei auf der Systemplatte (`ps5-swap.service`, einmal angelegt, wenn Platz ist) lässt ein großes Spiel langsamer werden, statt die PS4 einfrieren zu lassen, und wenn Speicher und Swap trotzdem ausgehen, wird das Spiel beendet, bevor die PS4 einfriert, und der Startbildschirm nennt den Grund.
- Menüsprachen: Die Übersetzungen liegen in `lib/ps5/translations.json`, ein Eintrag pro englischem Text. Arabisch ist rechtsbündig und wird mit DejaVu Sans gezeichnet; seine Buchstaben werden in `lib/ps5/i18n.py` verbunden, da SDL_ttf sie hier nicht verbindet.
- Das Programm sieht das USB-Laufwerk als `/mnt/usb0` und einen Ordner des Systems (`~/data`, bleibt zwischen Starts erhalten) als `/data`. Für Snes9x PS5 kommen ROMs nach `snes9x/roms` auf dem USB-Laufwerk oder nach `~/data/snes9x/roms`.
- Wenn der Emulator mit einem Fehler stoppt, zeigt der Startbildschirm den Grund.
- `PS5_GAME` in `/etc/ps5-on-ps4.conf` startet ein Spiel direkt statt des Startbildschirms.
- Controller: ein DualShock 4 am Kabel oder über Bluetooth, nachdem SHARE + PS gehalten wurden, bis die Lichtleiste doppelt blinkt.
- Der Ton geht über HDMI an den Fernseher, auch wenn ein Controller am Kabel seine eigene Soundkarte mitbringt (`/etc/wireplumber/wireplumber.conf.d/51-ps5-hdmi.conf`).

### Wo Spiele liegen können

- **USB-Laufwerk:** der Ordner `PS5` oben auf dem Laufwerk. exFAT ist am besten (Dateien über 4 GB); NTFS geht auch.
- **PS4-Festplatte:** `/user/home/PS5` auf der PS4, per GoldHEN-FTP dorthin kopiert. Das System liest die PS4-Festplatte nur und ändert sie nie. Nicht verfügbar, wenn das System selbst auf einem USB-Laufwerk installiert ist.
- **Ein PC:** ein freigegebener Ordner unter Windows oder Linux. Schalte in den Einstellungen **Spiele vom PC nutzen** ein und gib die PC-Adresse, den freigegebenen Ordner und, außer bei einer Gastfreigabe, Benutzername und Passwort an; dann Verbinden. Die Spiele können oben im freigegebenen Ordner oder in einem Ordner `PS5` darin liegen. Ein Netzwerkkabel ist schneller als WLAN.
  - Windows: Gib den Ordner frei (Eigenschaften, Freigabe). Für eine Gastfreigabe gib ihn für Everyone frei und schalte *Password protected sharing* in den erweiterten Freigabeeinstellungen aus.
  - Linux (Samba): eine Freigabe mit `guest ok = yes` für Gäste oder ein Samba-Benutzer (`smbpasswd -a`).
  - Der PS4-Kernel hat keinen SMB-Client, daher nutzt das System smbnetfs (FUSE). Die Einstellungen, Passwort eingeschlossen, liegen in `~/.config/ps5-on-ps4/pc-share.json` und sind nur für den Benutzer `ps5` lesbar.

`tools/make-pad-test-rom.py` schreibt ein winziges SNES-ROM zum Prüfen eines Controllers: blau, grün solange eine Taste gedrückt ist.

Anmeldung: `ps5` / `ps5` auf tty2 oder per SSH. Die Ausgabe des Emulators steht in `~/kytyps5.log` (der Lauf davor: `~/kytyps5.log.1`).

<a id="games"></a>
## Spiele

Dieses Projekt enthält keine PS5-Systemsoftware und keine Spiele. Verwende nur Spiele, die du besitzt und selbst gedumpt hast.

Getestete Spiele:

| Spiel | Konsole | Ergebnis |
|---|---|---|
| God of War Sons of Sparta | PS4 Pro | Spielbar, etwa 40 FPS und mehr |
| Hollow Knight: Silksong | PS4 Pro | Spielbar, 50 bis 60 FPS |
| Plants vs. Zombies: Replanted | PS4 Pro | Spielbar, feste 60 FPS |
| Vampire Survivors | PS4 Slim | Spielbar, stabile 60 FPS |
| Spider-Man 2 | | Noch nicht getestet |

Ein Spiel getestet? Eröffne ein [Issue](https://github.com/blue0x1/EmuFive/issues) mit dem Spiel, deinem Konsolenmodell und wie es lief.

<a id="changelog"></a>
## Änderungsprotokoll

### 1.0.6 (2026-11-14)

- Verbessert: Der Startbildschirm braucht viel weniger CPU, solange ihn niemand bedient (in 4K etwa ein Drittel eines Kerns statt eines ganzen Kerns), daher bleibt die PS4 kühler und leiser.

Um von 1.0.3 oder älter zu aktualisieren, starte das Update einmal von Hand, da die alte Softwareaktualisierung es nicht kann: SSH in den Einstellungen einschalten, mit `ssh ps5@<Adresse der PS4>` verbinden (Passwort `ps5`, falls nicht geändert) und ausführen:

```bash
sudo systemd-run --unit=emufive-update --collect /opt/ps5-on-ps4/bin/ps5-update install
```

Es installiert alle fehlenden Updates (von 1.0.0 oder 1.0.1 aus gehören die Browser-Pakete von 1.0.2 dazu, etwa 110 MB); danach über den Startbildschirm neu starten. Ab 1.0.4 funktioniert die Softwareaktualisierung in den Einstellungen. Neuinstallationen verwenden die `ps5-ps4-rootfs.tar.xz` der Version 1.0.6.

## Projektaufbau

| Pfad | Inhalt |
|---|---|
| `scripts/build-kyty.sh` | Baut KytyPS5 (Original plus `patches/kytyps5/`) für die CPU der PS4 |
| `patches/kytyps5/` | Die Änderungen dieses Projekts an KytyPS5 |
| `scripts/build-rootfs.sh` | Baut das Systemabbild für PS4 Multiboot |
| `scripts/make-release.sh` | Erstellt das Update-Paket eines Releases (Einstellungen, System, Softwareaktualisierung installiert es) |
| `scripts/updates/` | Skripte, die ein Update auf der PS4 ausführt, nachdem seine Dateien kopiert sind (`--post`) |
| `docker/` | Build-Umgebungen für beides |
| `overlay/` | Dateien, die dem System hinzugefügt werden: Sitzung, Startbildschirm, Einstellungen, Einhängen von USB-Laufwerk und PS4-Festplatte, Controller-Kopplung |
| `tools/` | Logo-Konverter, Controller-Test-ROM, `extract-code.py` (der Code eines PS5-SELF/ELF) |
| `tools/jaguar-test/` | Prüft die Ersetzungen von Patch `0004` gegen die echten Befehle |

## Besonderer Dank

- [KytyPS5](https://github.com/KytyPS5/KytyPS5), der PS5-Emulator, auf dem EmuFive basiert (GPL-2.0)
- [Kyty](https://github.com/InoriRus/Kyty) von InoriRus, der Emulator, auf dem KytyPS5 basiert

<a id="credits"></a>
## Danksagungen

- [Mesa](https://mesa3d.org) und die PS4-GPU-Patches von fail0verflow, DionKill und striker91n
- Die Entwickler des PS4-Linux-Kernels ([sony-jaguar-devs/ps4-linux](https://github.com/sony-jaguar-devs/ps4-linux))

## Lizenz

Copyright (C) 2026 [Chokri Hammedi (blue0x1)](https://github.com/blue0x1).

GPL-2.0 (siehe `LICENSE`). KytyPS5, Mesa und der Linux-Kernel stehen unter ihren eigenen Lizenzen. PlayStation ist eine Marke von Sony Interactive Entertainment; dieses Projekt ist nicht mit Sony verbunden.
