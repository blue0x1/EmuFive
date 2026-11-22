# Fehlerbehebung

<p align="center">
  <a href="TROUBLESHOOTING.md">EN</a> · <a href="TROUBLESHOOTING.ar.md">AR</a> · <a href="TROUBLESHOOTING.zh-CN.md">ZH</a> · <a href="TROUBLESHOOTING.fr.md">FR</a> · <a href="TROUBLESHOOTING.es.md">ES</a> · <b>DE</b> · <a href="TROUBLESHOOTING.it.md">IT</a> · <a href="TROUBLESHOOTING.pt-BR.md">PT</a> · <a href="TROUBLESHOOTING.tr.md">TR</a>
</p>

Die Probleme, die in den [Issues](https://github.com/blue0x1/EmuFive/issues) gemeldet wurden, mit den Lösungen, die geholfen haben. Gehe die Schritte der Reihe nach durch. Klappt es immer noch nicht? Öffne ein Issue mit den Angaben aus [Was schicken](#what-to-send).

- [Zuerst die Dateien prüfen](#check-the-files-first)
- [Schwarzes Bild oder „Kein Signal“ nach dem Payload](#black-screen-or-no-signal-after-the-payload)
- [Schwarzes Bild nach dem Menü oder dem EmuFive-Logo](#black-screen-after-the-menu-or-the-emufive-logo)
- [Grünes Bild, falsche Farben oder Flackern](#green-screen-wrong-colors-or-flickering)
- [Die PS4 geht aus, oder das Licht bleibt weiß](#the-ps4-turns-off-or-the-light-stays-white)
- [„No Linux install or archive found“](#no-linux-install-or-archive-found)
- [Die Installation dauert sehr lange](#installing-takes-very-long)
- [EmuFive startet nach einer abgebrochenen Installation nicht](#emufive-doesnt-start-after-a-stopped-install)
- [Es geht nur mit eingestecktem USB-Laufwerk](#it-only-works-with-the-usb-drive-plugged-in)
- [Spiele werden nicht angezeigt](#games-dont-show-up)
- [Ein externes Laufwerk wird nicht gefunden](#an-external-drive-isnt-found)
- [Der Controller geht nicht](#the-controller-doesnt-work)
- [Ein Spiel schließt sich, hängt oder läuft langsam](#a-game-closes-freezes-or-runs-slowly)
- [Protokolle speichern](#how-to-save-the-logs)
- [Was schicken](#what-to-send)

<a id="check-the-files-first"></a>
## Zuerst die Dateien prüfen

Die meisten „es passiert nichts“-Meldungen hatten einen dieser Gründe:

- **Gleiche Version:** `bzImage`, `initramfs.cpio.gz`, `bootargs.txt` und `linux-2048mb.bin` müssen alle aus derselben [PS4-Multiboot-Version](https://github.com/blue0x1/ps4-multiboot/releases) stammen (am besten der neuesten). Gemischte Dateien starten nicht.
- **Ordnernamen klein geschrieben:** Die PS4 sieht `LINUX` und `linux` als verschiedene Ordner. Die Pfade müssen genau `/data/linux/boot/bzImage`, `/data/linux/boot/initramfs.cpio.gz` und `/data/linux/boot/bootargs.txt` sein.
- **Der genaue Archivname:** `/user/home/ps5-ps4-rootfs.tar.xz`. Ein Browser speichert ihn manchmal als `ps5-ps4-rootfs (1).tar.xz`, dann findet das Menü ihn nicht.
- **Binäre Übertragung:** In FileZilla vor dem Hochladen Übertragung → Übertragungsart → **Binär** wählen. Eine im Textmodus hochgeladene Datei ist beschädigt. Prüfe, ob jede Datei auf der PS4 dieselbe Größe hat wie in der Version.
- **Unser Payload:** Nimm `linux-2048mb.bin` aus PS4 Multiboot (auf Firmware 14.02: `linux-2048mb-14.02.bin`). Er läuft auf Firmware 5.05 bis 14.02. Andere Linux-Payloads werden nicht unterstützt.

<a id="black-screen-or-no-signal-after-the-payload"></a>
## Schwarzes Bild oder „Kein Signal“ nach dem Payload

Nach dem Start des Payloads zeigt der Fernseher **1 bis 2 Minuten** lang „Kein Signal“ oder ein schwarzes Bild, während Linux startet. Das ist normal. Dass Bild und Controller direkt nach dem Payload ausgehen, ist auch normal: Das PS4-System fährt herunter und Linux übernimmt.

**Drücke nicht die PS-Taste, solange das Bild schwarz ist**: Das schaltet die PS4 aus. Ist nur EmuFive auf der PS4, startet der Installer nach 60 Sekunden von selbst, er installiert also vielleicht schon.

Wenn nach 3 Minuten nichts kommt:

1. Schließe die PS4 **direkt** an den Fernseher an, ohne HDMI-Switch, AV-Receiver oder Capture-Karte.
2. Schalte auf der PS4 **Einstellungen → System → HDCP aktivieren** aus und starte den Payload erneut.
3. Probiere ein anderes HDMI-Kabel und einen anderen HDMI-Anschluss.
4. Probiere einmal einen anderen Fernseher oder Monitor. Manche Fernseher nehmen das Linux-Signal der PS4 nicht an, und ein anderer Bildschirm zeigt, ob es am Fernseher liegt.
5. Immer noch nichts? Speichere das [PS4BOOT-Protokoll](#the-ps4boot-stick-boot-problems) und öffne ein Issue. Schreib, ob der Fernseher **„Kein Signal“** zeigt oder an, aber schwarz ist.

<a id="black-screen-after-the-menu-or-the-emufive-logo"></a>
## Schwarzes Bild nach dem Menü oder dem EmuFive-Logo

Siehst du das PS4-Multiboot-Menü oder das EmuFive-Logo und danach wird es schwarz, dann hat EmuFive auf einen Modus gewechselt, den dein Fernseher bevorzugt, den die PS4 aber nicht senden kann.

1. Aktualisiere EmuFive (Einstellungen → System → Softwareaktualisierung).
2. Öffne per FTP `/data/linux/boot/bootargs.txt` und füge ` emufive.mode=1920x1080@60` am Ende der Zeile hinzu. Behalte auch `video=HDMI-A-1:1920x1080@60D`. Die Datei muss **eine Zeile** bleiben.
3. Starte den Payload erneut.

Kein Update möglich, weil das Bild schwarz ist? Schließe einmal einen anderen Fernseher oder Monitor an und aktualisiere, oder installiere EmuFive neu mit der neuesten `ps5-ps4-rootfs.tar.xz`.

<a id="green-screen-wrong-colors-or-flickering"></a>
## Grünes Bild, falsche Farben oder Flackern

Eine grüne Schicht, Schwarz als Grün oder Weiß als Cyan, oder Flackern: Der Fernseher liest das Signal der PS4 im falschen Farbformat.

1. Füge ` emufive.mode=1920x1080@60` zu `bootargs.txt` hinzu (siehe oben).
2. Probiere ein anderes HDMI-Kabel oder einen anderen Anschluss. Schalte in den Einstellungen des Fernsehers für diesen Anschluss Optionen wie **HDMI UHD Color**, **Erweitertes Format**, **Deep Colour** oder **Input Signal Plus** um (an nach aus oder umgekehrt), und schalte HDMI-CEC aus (**Anynet+**, **Bravia Sync**...).
3. Probiere einen anderen Fernseher oder Monitor.

<a id="the-ps4-turns-off-or-the-light-stays-white"></a>
## Die PS4 geht aus, oder das Licht bleibt weiß

- **Auf 14.02** schaltet der erste Start des Payloads die PS4 manchmal aus. Starte ihn noch einmal: Der zweite Versuch klappt meistens.
- **Das Licht bleibt weiß** und 5 Minuten passiert nichts: Halte die Einschalttaste gedrückt, um die PS4 auszuschalten, schalte sie wieder ein und starte den Payload erneut.
- **Ein violettes Licht** nach der Installation ist normal.
- **Die PS4 geht aus, wenn du die PS-Taste** bei schwarzem Bild drückst: Nicht drücken, warten (siehe oben).

<a id="no-linux-install-or-archive-found"></a>
## „No Linux install or archive found“

Das Menü hat weder ein installiertes EmuFive noch `ps5-ps4-rootfs.tar.xz` gefunden.

1. Prüfe Name und Ort des Archivs: genau `/user/home/ps5-ps4-rootfs.tar.xz`.
2. Auf einer **PS4 Fat** (CUH-10xx, 11xx oder 12xx) fand PS4 Multiboot v1.5.0-beta.3 bis beta.7 die interne Festplatte nicht. Nimm `bzImage` und `initramfs.cpio.gz` aus [v1.5.0-beta.8](https://github.com/blue0x1/ps4-multiboot/releases/tag/v1.5.0-beta.8) oder neuer.

<a id="installing-takes-very-long"></a>
## Die Installation dauert sehr lange

- **Das Anlegen der Disk** sind die ersten 25 % des Balkens, und das ist der langsame Teil: Alles, was auf die Festplatte der PS4 geschrieben wird, läuft durch die Verschlüsselung der PS4. Baikal-Konsolen sind dabei langsamer. Eine große Disk dauert länger, also nimm für den ersten Versuch eine kleinere (16 GB reichen). Der Teil nach 25 % geht schneller.
- **Schalte die PS4 nicht aus**, solange der Prozentwert noch steigt. Bewegt er sich 30 Minuten lang nicht, öffne ein Issue und schreib, wo er stehen blieb.
- **Schwarzes Bild am Ende:** Hat der Fernseher noch ein Signal, ist die Installation höchstwahrscheinlich fertig und EmuFive startet. Lässt sich die PS4 mit der Einschalttaste normal ausschalten, läuft EmuFive und nur das Bild ist schwarz: siehe [Schwarzes Bild nach dem Menü](#black-screen-after-the-menu-or-the-emufive-logo).

<a id="emufive-doesnt-start-after-a-stopped-install"></a>
## EmuFive startet nach einer abgebrochenen Installation nicht

Wurde die PS4 während einer Installation ausgeschaltet, kann eine halb angelegte Disk übrig bleiben. Der Fehlerbildschirm zeigt **„The EmuFive disk is incomplete“**, oder im Protokoll steht `is a hole`.

1. Lösche `/user/home/ps5-ps4.img` per FTP. Behalte `ps5-ps4-rootfs.tar.xz`.
2. Starte den Payload und installiere neu. Lass es fertig laufen, ohne die PS4 auszuschalten.

<a id="it-only-works-with-the-usb-drive-plugged-in"></a>
## Es geht nur mit eingestecktem USB-Laufwerk

Du hast **Install to USB drive** gewählt, also liegt EmuFive auf diesem Laufwerk und braucht es. Um es stattdessen auf der PS4 zu haben: Laufwerk abziehen, Payload starten und **Install to PS4** wählen.

<a id="games-dont-show-up"></a>
## Spiele werden nicht angezeigt

Ein Spiel ist ein **Ordner** mit `eboot.bin` und `sce_sys` darin, oder eine einzelne `.zar`-Datei. `.pkg`- und fpkg-Dateien gehen nicht: Entpacke das Spiel zuerst. Nutze Dumps von Spielen, die dir gehören.

Auf einem USB-Laufwerk muss es so aussehen:

```
USB-Laufwerk (exFAT, eine Partition; NTFS geht auch)
└── PS5/                      <- genau "PS5", groß geschrieben, oben auf dem Laufwerk
    ├── PPSA01234/            <- ein Ordner pro Spiel (beliebiger Name)
    │   ├── eboot.bin         <- direkt im Spielordner
    │   ├── sce_sys/
    │   │   └── param.json    <- gibt Name und Bild des Spiels
    │   └── ...
    └── MeinSpiel.zar         <- ein .zar-Dump, als einzelne Datei
```

Häufige Fehler:

- `ps5/` oder `Ps5/`: Der Name muss genau `PS5` sein.
- `Spiele/PS5/...`: Der Ordner `PS5` muss ganz oben auf dem Laufwerk liegen.
- `PS5/PPSA01234/PPSA01234/eboot.bin`: eine Ordnerebene zu viel (häufig nach dem Entpacken). Schiebe den inneren Ordner nach oben.
- `PS5/eboot.bin`: die Spieldateien lose in `PS5`, ohne eigenen Ordner.
- Zwei Spiele in einem Ordner: Nur eins wird angezeigt. Der Name auf der Kachel kommt aus `sce_sys/param.json`, nicht vom Ordnernamen, also gib jedem Spiel einen eigenen Ordner.

Auf der Festplatte der PS4 ist der Ordner `/user/home/PS5`, und er geht nur, wenn EmuFive auf der PS4 installiert ist (nicht auf einem USB-Laufwerk). Kopiere Spiele mit GoldHEN-FTP aus dem PS4-System und starte dann EmuFive: Es liest diesen Ordner beim Start.

Lass nur das Spiele-Laufwerk eingesteckt. Zieh den `PS4BOOT`-Protokollstick beim Spielen ab.

<a id="an-external-drive-isnt-found"></a>
## Ein externes Laufwerk wird nicht gefunden

- Externe SSDs und Festplatten gehen ab EmuFive 1.0.5. Aktualisiere zuerst.
- Ein Laufwerk, auf dem früher Linux war, erscheint nach einer normalen Formatierung manchmal immer noch nicht. Lösche alle Partitionen (Windows: Datenträgerverwaltung) und lege eine einzige **exFAT**-Partition an.
- Ist EmuFive auf einem USB-Laufwerk installiert, kommen die Spiele auf ein zweites USB-Laufwerk (ab EmuFive 1.0.4).

<a id="the-controller-doesnt-work"></a>
## Der Controller geht nicht

- **Im PS4-Multiboot-Menü und auf den Installations- und Fehlerbildschirmen** geht der Controller nur **per USB-Kabel**. Bluetooth startet erst später, in EmuFive.
- **Per Bluetooth** muss er einmal mit EmuFive gekoppelt werden, denn die Kopplung des PS4-Systems gilt nicht. Zieh das Kabel ab, halte **SHARE + PS**, bis die Lichtleiste doppelt blinkt, und warte ein paar Sekunden. Verbindet er sich nicht, nimm Einstellungen → Controller → Neuen Controller koppeln.
- Nimm ein Kabel, das Daten überträgt. Manche Kabel laden nur.
- Auf **Baikal**-Konsolen (viele Pro CUH-71xx/72xx und neuere Slims; siehe Einstellungen → System → Systeminformationen) braucht USB PS4 Multiboot v1.5.0-beta.7 oder neuer.

<a id="a-game-closes-freezes-or-runs-slowly"></a>
## Ein Spiel schließt sich, hängt oder läuft langsam

- **„Das Spiel wurde beendet (Fehlercode 65)“ mit `ErrorDeviceLost`:** Die GPU der PS4 ist beim Zeichnen des Spiels hängen geblieben. Das passiert oft bei schweren Unreal-Engine-Spielen, die noch nicht spielbar sind. Schick das [Spielprotokoll](#game-logs), wenn wir es uns ansehen sollen.
- **Kein Speicher mehr:** Ein PS5-Spiel kann bis etwa 12,5 GB nutzen, Linux auf der PS4 hat etwa 6 GB. EmuFive beendet das Spiel, bevor die PS4 einfriert. Schalte Einstellungen → Spiele → **Mit der GPU geteilter Spielspeicher** aus und versuche es erneut. EmuFive legt eine 4-GB-Auslagerungsdatei nur an, wenn seine Disk 8 GB frei hat, also schaffe Platz, wenn die Disk voll ist.
- **Ein Spiel hängt oder stürzt ab:** Probiere es einmal mit ausgeschaltetem **Mit der GPU geteilter Spielspeicher**. Er beschleunigt große 3D-Spiele, passt aber nicht zu jedem Spiel (Minecraft hängt damit).
- **Ruckeln beim ersten Mal:** Beim ersten Durchlauf einer Szene werden Shader kompiliert. Beim zweiten Mal läuft es flüssiger.
- **Tearing:** Einstellungen → Spiele → Bildtakt → **Flüssig (kein Tearing)**.
- **Wenig FPS:** CPU und GPU der PS4 sind viel langsamer als die der PS5. 2D- und leichtere Spiele laufen gut; schwere 3D-Spiele laden oft und zeigen ihre Menüs, laufen dann aber sehr langsam oder bleiben im Spiel schwarz. Eine PS4 Pro ist etwa doppelt so schnell wie eine Slim. Sieh dir die [Spiele](README.de.md#games)-Tabelle an, bevor du ein großes Spiel probierst.

<a id="how-to-save-the-logs"></a>
## Protokolle speichern

<a id="the-ps4boot-stick-boot-problems"></a>
### Der PS4BOOT-Stick (Startprobleme)

1. Formatiere einen USB-Stick als **FAT32** mit der Bezeichnung **`PS4BOOT`** (groß geschrieben). Windows kann Sticks über 32 GB nicht als FAT32 formatieren: Nimm einen kleineren Stick oder [Rufus](https://rufus.ie) (Startart: *Nicht bootfähig*, Dateisystem: *Large FAT32*, Laufwerksbezeichnung: `PS4BOOT`). NTFS und exFAT gehen dafür nicht.
2. Steck ihn **vor** dem Start des Payloads in die PS4 und lass ihn stecken.
3. Starte den Payload und warte **5 Minuten**, auch wenn das Bild schwarz bleibt. Erscheint ein Fehlerbildschirm, speichert er die Details selbst auf dem Stick.
4. Halte die Einschalttaste gedrückt, um die PS4 auszuschalten. Steck den Stick in einen PC und hänge die `.log`-Dateien an dein Issue an (`ps4-linux-boot.log`, `ps4-linux-late.log`, `ps4-linux-error.log` oder `ps4-linux-rescue.log`).

Bleibt der Stick leer, schreib das: Dann ist Linux nicht so weit gekommen, und das hilft auch.

<a id="game-logs"></a>
### Spielprotokolle

Direkt nachdem das Spiel beendet wurde: Einstellungen → System → **Protokolle auf USB kopieren**, dann die Dateien aus dem Ordner `PS5-logs` auf dem USB-Laufwerk anhängen (`kytyps5.log` ist die wichtigste). Häng die echte Datei an, keine Zusammenfassung.

<a id="what-to-send"></a>
## Was schicken

- PS4-Modell (CUH-xxxx, auf dem Aufkleber hinten), Firmware und Southbridge (Einstellungen → System → Systeminformationen, z. B. Belize, Baikal, Aeolia).
- Die PS4-Multiboot-Version und die Payload-Datei, die du startest.
- Deine `bootargs.txt`-Zeile.
- Deine EmuFive-Version (Einstellungen → System), und ob es auf der PS4 oder einem USB-Laufwerk installiert ist.
- Das Modell deines Fernsehers oder Monitors, und was er zeigt: „Kein Signal“ oder an, aber schwarz.
- Das Licht der PS4: weiß, blau, violett oder aus.
- Die Protokolle von oben.
