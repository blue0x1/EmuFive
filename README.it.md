<h1 align="center"><img src="assets/emufive-logo.png" alt="EmuFive" width="480"></h1>

<p align="center">
  <img src="https://img.shields.io/badge/platform-PS4-003791?logo=playstation&logoColor=white" alt="Platform: PS4">
  <img src="https://img.shields.io/badge/status-experimental-red" alt="Status: experimental">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--2.0-blue" alt="License: GPL-2.0"></a>
</p>

<p align="center">
  <a href="README.md">EN</a> · <a href="README.ar.md">AR</a> · <a href="README.zh-CN.md">ZH</a> · <a href="README.fr.md">FR</a> · <a href="README.es.md">ES</a> · <a href="README.de.md">DE</a> · <b>IT</b> · <a href="README.pt-BR.md">PT</a> · <a href="README.tr.md">TR</a>
</p>

Un emulatore PS5 per PS4.

Creato da **[Chokri Hammedi (blue0x1)](https://github.com/blue0x1)**. Basato su [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot).

> **Stato: ricerca sperimentale.** Su una PS4 Pro, "Sons of Sparta" gira a circa 40 FPS e oltre. KytyPS5 riscrive le istruzioni della CPU proprie della PS5 nel codice dei giochi (patch `0004`). Altri giochi sono ancora in prova, e molti per ora sono lenti. Vedi [Il problema della CPU](#the-cpu-problem).

<p align="center"><img src="assets/home-screen.png" alt="La schermata Home di EmuFive su una PS4 Pro, con God of War Sons of Sparta selezionato" width="900"></p>

<p align="center">
  <b><a href="#installing">Installazione</a></b> · <b><a href="#games">Giochi</a></b> · <b><a href="#changelog">Registro delle modifiche</a></b> · <a href="#how-it-works">Come funziona</a> · <a href="#the-cpu-problem">Il problema della CPU</a> · <a href="#plan">Piano</a> · <a href="#building">Compilazione</a> · <a href="#credits">Riconoscimenti</a>
</p>

<a id="how-it-works"></a>
## Come funziona

- **[PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot)** avvia Linux sulla PS4 e installa sistemi Linux sul suo disco interno, con il controller.
- **PS4 Mesa**, parte di PS4 Multiboot, dà Vulkan 1.3 alla GPU della PS4 (Liverpool su PS4 e Slim, Gladius sulla Pro). KytyPS5 ha bisogno delle risorse sparse (sparse resources), che RADV offre su questa GPU con `RADV_EXPERIMENTAL=sparse`.
- **KytyPS5**, il progetto originale a un commit fissato con le patch di questo progetto (`patches/kytyps5/`), compilato con `-march=btver2` per la CPU AMD Jaguar della PS4. La versione ufficiale usa AVX2 e sulla PS4 si ferma con "Illegal instruction".
  - `0001`: l'opzione di compilazione `KYTY_HOST_ARCH` (la CPU per cui viene compilato l'emulatore).
  - `0002`: una libreria C per l'homebrew. L'homebrew PS5 creato con ps5-native-app-boilerplate include un modulo sostitutivo `sce_module/libc.prx` le cui funzioni restituiscono tutte 0 (la console usa la propria libreria C), quindi in KytyPS5 il suo `malloc` falliva. La patch aggiunge le funzioni della libreria C che quell'homebrew importa e le usa solo per un modulo sostitutivo di quel tipo.
  - `0003`: altro per l'homebrew: file e cartelle, chiamate di sistema, l'utente in primo piano e punti di montaggio aggiuntivi (`KYTY_MOUNTS`).
  - `0004`: codice PS5 sulla CPU della PS4. Ogni istruzione AVX2, FMA e BMI2 viene riscritta in codice SSE4.2/AVX/BMI1 al caricamento di un modulo; quella che non si può riscrivere in quel momento viene sostituita la prima volta che viene eseguita. Vedi [Il problema della CPU](#the-cpu-problem).
- **EmuFive** mette tutto questo in un piccolo sistema Linux che si avvia direttamente nell'emulatore, a schermo intero, senza desktop. Si installa con PS4 Multiboot come qualsiasi altro sistema.

<a id="the-cpu-problem"></a>

## Il problema della CPU

KytyPS5 non emula la CPU della PS5: esegue direttamente il codice x86-64 del gioco. I giochi PS5 sono compilati per la CPU Zen 2 della PS5 e usano ovunque istruzioni AVX2, BMI2 e FMA. La CPU Jaguar della PS4 non ne ha nessuna, quindi il codice del gioco si ferma alla prima di queste istruzioni.

La patch `0004` aggiunge questo al patcher delle istruzioni guest di KytyPS5. Quando alla CPU host mancano AVX2, FMA o BMI2, ogni istruzione del genere viene sostituita da codice con lo stesso effetto: operazioni intere a 256 bit come due metà da 128 bit, permutazioni tra le metà con spostamenti e miscelazioni AVX, shift per elemento un elemento alla volta, FMA calcolata in doppia precisione, gather un elemento alla volta, BMI2 con registri salvati. Il salto alla sostituzione viene scritto dove si trovava l'istruzione; un'istruzione troppo corta per un salto, in un punto che il patcher non può riorganizzare, genera un errore e viene sostituita durante l'esecuzione.

`tools/jaguar-test/` verifica ogni sostituzione su un PC che ha queste istruzioni: prende ogni forma di istruzione trovata nel codice di un programma, esegue l'originale e la sostituzione dallo stesso stato casuale, e confronta tutti i registri, i flag e la memoria. Le forme trovate nei programmi provati finora coincidono: 287 in God of War Sons of Sparta (gather e VFMADDSUB inclusi) e 227 nei programmi provati prima. Le eccezioni sono rare differenze nell'ultimo bit in FMA (la precisione singola viene arrotondata due volte, la doppia è una moltiplicazione e un'addizione) e un caso limite di NaN per 0 per infinito.

Il Jaguar resta molto più lento della CPU della PS5, e le sostituzioni si aggiungono a questo, quindi anche un gioco che funziona può girare lentamente.

<a id="plan"></a>
## Piano

| Passo | Stato |
|---|---|
| Vulkan sulla GPU della PS4 soddisfa i requisiti di KytyPS5 | Fatto (`RADV_EXPERIMENTAL=sparse`) |
| KytyPS5 compilato per la CPU della PS4 | Fatto (`KYTY_HOST_ARCH=btver2`) |
| KytyPS5 si avvia sulla PS4 e inizializza la GPU | Fatto, PS4 Pro |
| Immagine di sistema EmuFive, si installa con PS4 Multiboot | Fatto, PS4 Pro |
| Un'app homebrew PS5 senza AVX2 funziona e disegna | Fatto: Snes9x PS5 2.11 ricompilato per btver2, PS4 Pro |
| Controller, archiviazione `/data` e USB, caricare un gioco in quell'app | Fatto su una build di prova per PC (stesse patch); PS4 in seguito |
| Traduzione di AVX2, BMI2 e FMA per il codice dei giochi | Fatto (`0004`), verificato su un PC |
| Un gioco PS5 funziona sulla PS4 | Fatto: God of War Sons of Sparta, circa 40 FPS e oltre, PS4 Pro |
| Hollow Knight: Silksong funziona sulla PS4 | Fatto dalla 1.0.1 (patch `0006` e `0007`), PS4 Pro |
| Schermata Home: scegliere un gioco con il controller; Wi-Fi; Impostazioni | Fatto, verificato su un PC |
| Giochi dall'unità USB, dal disco della PS4 o da una cartella condivisa di un PC | Fatto, verificato su un PC; PS4 in seguito |

<a id="building"></a>

## Compilazione

Servono Docker, git e il PS4 Mesa di PS4 Multiboot (`../PS4-Multiboot/out/ps4-mesa.tar.xz`, compilato lì con `make mesa`). `build-kyty.sh` clona KytyPS5 in `build/kytyps5` la prima volta, poi a ogni compilazione lo riporta al commit fissato e applica le patch.

```bash
scripts/build-kyty.sh      # out/kytyps5-ps4.tar.xz
scripts/build-rootfs.sh    # out/ps5-ps4-rootfs.tar.xz
```

`PS4_MESA` e `KYTY` indicano a `build-rootfs.sh` altri percorsi.

<a id="installing"></a>

## Installazione

EmuFive si installa con [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot), come qualsiasi altro sistema Linux.

Ti servono:

- Una PS4 con jailbreak e **GoldHEN** (per il suo server FTP e il suo caricatore di payload).
- Un PC sulla stessa rete con un client FTP (per esempio FileZilla).
- Circa 28 GB liberi sulla PS4 (un disco da 16 GB, e 10 GB sempre lasciati liberi per la PS4), oppure un'unità USB da 8 GB o più.
- Un DualShock 4 (con un cavo USB, o associato via Bluetooth in seguito).

Passi:

1. Dalle [release di PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot/releases), scarica `bzImage`, `initramfs.cpio.gz`, `bootargs.txt` e `linux-2048mb.bin`. (`ps4-mesa.tar.xz` non serve: EmuFive include già PS4 Mesa.)
2. Dalle [release di EmuFive](https://github.com/blue0x1/EmuFive/releases), scarica `ps5-ps4-rootfs.tar.xz` (o compilalo, vedi [Compilazione](#building)). Non cambiargli nome: PS4 Multiboot trova i sistemi grazie al `-ps4-rootfs` che contiene.
3. Attiva il server FTP di GoldHEN e copia i file sulla PS4 (porta 2121):

   | File | Cartella sulla PS4 |
   |---|---|
   | `bzImage`, `initramfs.cpio.gz`, `bootargs.txt` | `/data/linux/boot/` |
   | `ps5-ps4-rootfs.tar.xz` | `/user/home/` |
   | `linux-2048mb.bin` | `/data/payloads/` |

4. Avvia `linux-2048mb.bin` dal menu dei payload di GoldHEN.

   > **Abbi pazienza:** dopo l'avvio del payload, la TV può mostrare **"No signal" o uno schermo nero per 1 o 2 minuti** mentre Linux si avvia. È normale.

5. Nel menu di PS4 Multiboot, scegli **EmuFive**, poi **Install to PS4** o **Install to USB drive**. Ci vogliono alcuni minuti.
6. Metti i tuoi giochi in uno dei posti qui sotto. Un gioco è una cartella con `eboot.bin` (e `sce_sys`), oppure un dump ZArchive (`.zar`).

Dopo, avvia il payload per far partire EmuFive: se è installato solo EmuFive parte subito, con altri sistemi appare prima il menu di PS4 Multiboot. Spegni o riavvia dalla schermata Home per tornare al sistema della PS4. Per reinstallare EmuFive, elimina `/user/home/ps5-ps4.img` via FTP e avvia il payload.

Gli aggiornamenti arrivano dalle release di EmuFive: Impostazioni, Sistema, Aggiornamento software (non serve reinstallare).

Il sistema si avvia nella schermata Home e non ha bisogno di una tastiera:

- I giochi appaiono come riquadri, ognuno con il posto in cui si trova: **USB**, **PS4** o **PC**. Scegline uno e premi Gioca; quando si chiude, torna la schermata Home.
- In alto: il Wi-Fi (con una tastiera su schermo per la password) e le Impostazioni, e due schede, **Giochi** e **Media** (L1 / R1). Media mostra i tuoi screenshot; aprine uno, e Quadrato lo elimina.
- OPTIONS su un gioco: preferito, nascondi, le sue impostazioni, i suoi trofei e quanto ci hai giocato.
- **Internet**, il riquadro dopo i giochi: un browser web usato con il controller. La levetta sinistra (o il touchpad) muove il puntatore e X fa clic; la levetta destra scorre; O o L1 torna indietro, R1 avanti; L2 e R2 fanno lo zoom. Triangolo digita un indirizzo o una ricerca, e scegliere una casella di testo in una pagina apre la tastiera su schermo. OPTIONS apre il menu: segnalibri, pagina iniziale, zoom, motore di ricerca (Google, DuckDuckGo o Bing), siti mobili (pagine più leggere) e cancellazione della cronologia e dei cookie. Il tasto PS torna alla schermata Home, e la volta dopo si apre la stessa pagina. È WebKitGTK con una pagina alla volta, circa 450 MB di memoria con una pagina di testo e di più con i siti video; la schermata Home si chiude mentre è in uso, e un gioco in pausa va chiuso prima. Download, upload, fotocamera, microfono e posizione vengono rifiutati. I segnalibri sono in `~/.config/ps5-on-ps4/browser.json`, i cookie in `~/.local/share/ps5-browser`.
- Il tasto PS durante un gioco lo mette in pausa e apre il menu rapido: Riprendi, **Home** (la schermata Home, con il gioco ancora in pausa: PS o Riprendi ci torna; avviare un altro gioco chiede prima e poi lo chiude), chiudi il gioco, volume, alimentazione.
- Screenshot: PS + Quadrato, o Share, anche in gioco. Vanno in `PS5-screenshots` sull'unità USB (o in `~/Screenshots` se non c'è), con un piccolo avviso nell'angolo. Per averne uno sul telefono, aprilo in Media e premi Triangolo (Condividi): inquadra il codice QR con il telefono (sulla stessa rete) per aprirlo lì, poi salvalo o condividilo. La PS4 serve solo quell'immagine, a un indirizzo casuale, e solo finché il codice è sullo schermo. I codici QR vengono da `python3-segno`.
- Impostazioni, Aspetto: colore principale, tema (scuro, mezzanotte, chiaro), sfondo (l'immagine del gioco, una sfumatura, un colore pieno o una tua immagine dall'unità USB), oscuramento dello sfondo, sfere fluttuanti, animazioni, dimensione e forma dei riquadri, dimensione e carattere del testo, orologio, cosa mostra la barra in alto (la batteria è quella del controller), suoni del menu, vibrazione, suggerimenti dei tasti, bordi dello schermo (overscan) e salvaschermo.
- Impostazioni, Controller: colore e luminosità della barra luminosa, vibrazione attiva o no e la sua intensità, il microfono del controller attivo o no (con il controller su un cavo USB; Linux non ha l'audio del controller via Bluetooth), scambio di X e O, e una pagina di prova per ogni tasto e levetta. Impostazioni, Giochi: valori predefiniti per tutti i giochi, lingua dei giochi, HDR e cadenza dei fotogrammi. Impostazioni, Data e ora: automatiche da internet (predefinito) o a mano. Impostazioni, Sistema: la lingua del menu (inglese, arabo, francese, turco, spagnolo, tedesco, italiano o portoghese del Brasile), temperatura e carico della CPU, backup delle impostazioni sull'unità USB, o ripristinarle tutte.
- Profili (Impostazioni, Profilo, e Cambia profilo nel menu rapido): fino a 8, ognuno con il proprio nome, avatar, salvataggi, trofei e tempo di gioco. Con più di uno, all'avvio si apre "Chi gioca?". Ogni profilo ha la propria cartella KytyPS5 (`~/.kytyps5/users/<ID>`, il primo profilo mantiene `~/.kytyps5`), con la cache degli shader condivisa.
- Avvisi nell'angolo in alto a sinistra, anche in gioco: è stato salvato uno screenshot, si è collegato un controller (con il tipo di collegamento e il livello della batteria), la batteria del controller è scarica (15%). La batteria della barra in alto è verde, gialla o rossa in base al livello, con un fulmine durante la ricarica.
- Memoria esaurita: un file di swap da 4 GB sul disco di sistema (`ps5-swap.service`, creato una volta quando c'è spazio) fa rallentare un gioco grande invece di bloccare la PS4, e se memoria e swap finiscono comunque, il gioco viene chiuso prima che la PS4 si blocchi e la schermata Home ne spiega il motivo.
- Lingue del menu: le traduzioni sono in `lib/ps5/translations.json`, una voce per ogni testo inglese. L'arabo è allineato a destra e disegnato con DejaVu Sans; le sue lettere vengono unite in `lib/ps5/i18n.py`, dato che qui SDL_ttf non le unisce.
- Il programma vede l'unità USB come `/mnt/usb0` e una cartella del sistema (`~/data`, conservata tra un avvio e l'altro) come `/data`. Per Snes9x PS5, le ROM vanno in `snes9x/roms` sull'unità USB o in `~/data/snes9x/roms`.
- Se l'emulatore si ferma con un errore, la schermata Home ne mostra il motivo.
- `PS5_GAME` in `/etc/ps5-on-ps4.conf` avvia subito un gioco invece della schermata Home.
- Controller: un DualShock 4 con il cavo, o via Bluetooth dopo aver tenuto premuti SHARE + PS finché la barra luminosa lampeggia due volte.
- L'audio va alla TV via HDMI, anche quando un controller con il cavo porta la propria scheda audio (`/etc/wireplumber/wireplumber.conf.d/51-ps5-hdmi.conf`).

### Dove possono stare i giochi

- **Unità USB:** la cartella `PS5` nella radice dell'unità. exFAT è la scelta migliore (file oltre 4 GB); funziona anche NTFS.
- **Disco della PS4:** `/user/home/PS5` sulla PS4, copiato lì con l'FTP di GoldHEN. Il sistema legge il disco della PS4 in sola lettura e non lo modifica mai. Non disponibile quando il sistema stesso è installato su un'unità USB.
- **Un PC:** una cartella condivisa su Windows o Linux. Nelle Impostazioni, attiva **Usa i giochi dal PC** e imposta l'indirizzo del PC, la cartella condivisa e, salvo per una condivisione ospite, un nome utente e una password; poi Connetti. I giochi possono stare nella radice della cartella condivisa o in una cartella `PS5` al suo interno. Un cavo di rete è più veloce del Wi-Fi.
  - Windows: condividi la cartella (Proprietà, Condivisione). Per una condivisione ospite, condividila con Everyone e disattiva *Password protected sharing* nelle impostazioni di condivisione avanzate.
  - Linux (Samba): una condivisione con `guest ok = yes` per gli ospiti, o un utente Samba (`smbpasswd -a`).
  - Il kernel della PS4 non ha un client SMB, quindi il sistema usa smbnetfs (FUSE). Le impostazioni, password compresa, sono salvate in `~/.config/ps5-on-ps4/pc-share.json`, leggibile solo dall'utente `ps5`.

`tools/make-pad-test-rom.py` crea una piccola ROM SNES per provare un controller: blu, verde mentre si tiene premuto un tasto.

Accesso: `ps5` / `ps5` su tty2 o via SSH. L'output dell'emulatore è in `~/kytyps5.log` (l'esecuzione precedente: `~/kytyps5.log.1`).

<a id="games"></a>
## Giochi

Questo progetto non contiene software di sistema PS5 né giochi. Usa solo giochi che possiedi e di cui hai fatto il dump tu stesso.

Giochi provati:

| Gioco | Console | Risultato |
|---|---|---|
| God of War Sons of Sparta | PS4 Pro | Giocabile, circa 40 FPS e oltre |
| Hollow Knight: Silksong | PS4 Pro | Giocabile, da 50 a 60 FPS |
| Plants vs. Zombies: Replanted | PS4 Pro | Giocabile, 60 FPS fissi |
| Vampire Survivors | PS4 Slim | Giocabile, 60 FPS stabili |
| Spider-Man 2 | | Non ancora provato |

Hai provato un gioco? Apri una [issue](https://github.com/blue0x1/EmuFive/issues) con il gioco, il modello della tua console e come è andato.

<a id="changelog"></a>
## Registro delle modifiche

### 1.0.6 (2026-11-14)

- Migliorato: la schermata Home usa molta meno CPU quando nessuno la usa (in 4K circa un terzo di un core, prima un core intero), quindi la PS4 resta più fresca e silenziosa.

Per aggiornare dalla 1.0.3 o precedenti, avvia l'aggiornamento una volta a mano, perché il vecchio aggiornamento software non ci riesce: attiva SSH nelle Impostazioni, collegati con `ssh ps5@<indirizzo della PS4>` (password `ps5` se non l'hai cambiata) ed esegui

```bash
sudo systemd-run --unit=emufive-update --collect /opt/ps5-on-ps4/bin/ps5-update install
```

Installa tutti gli aggiornamenti mancanti (dalla 1.0.0 o 1.0.1 include i pacchetti del browser della 1.0.2, circa 110 MB), poi riavvia dalla schermata Home. Dalla 1.0.4 l'aggiornamento software nelle Impostazioni funziona. Le nuove installazioni usano il `ps5-ps4-rootfs.tar.xz` della versione 1.0.6.

## Struttura del progetto

| Percorso | Contenuto |
|---|---|
| `scripts/build-kyty.sh` | Compila KytyPS5 (l'originale più `patches/kytyps5/`) per la CPU della PS4 |
| `patches/kytyps5/` | Le modifiche di questo progetto a KytyPS5 |
| `scripts/build-rootfs.sh` | Crea l'immagine di sistema per PS4 Multiboot |
| `scripts/make-release.sh` | Crea il pacchetto di aggiornamento di una release (lo installa Impostazioni, Sistema, Aggiornamento software) |
| `scripts/updates/` | Script che un aggiornamento esegue sulla PS4 dopo aver copiato i suoi file (`--post`) |
| `docker/` | Ambienti di compilazione per entrambi |
| `overlay/` | File aggiunti al sistema: sessione, schermata Home, impostazioni, montaggio dell'unità USB e del disco della PS4, associazione dei controller |
| `tools/` | Convertitore del logo, ROM di prova del controller, `extract-code.py` (il codice di un SELF/ELF PS5) |
| `tools/jaguar-test/` | Verifica le sostituzioni della patch `0004` rispetto alle istruzioni reali |

## Ringraziamenti speciali

- [KytyPS5](https://github.com/KytyPS5/KytyPS5), l'emulatore PS5 su cui si basa EmuFive (GPL-2.0)
- [Kyty](https://github.com/InoriRus/Kyty) di InoriRus, l'emulatore su cui si basa KytyPS5

<a id="credits"></a>
## Riconoscimenti

- [Mesa](https://mesa3d.org), e le patch per la GPU della PS4 di fail0verflow, DionKill e striker91n
- Gli sviluppatori del kernel Linux per PS4 ([sony-jaguar-devs/ps4-linux](https://github.com/sony-jaguar-devs/ps4-linux))

## Licenza

Copyright (C) 2026 [Chokri Hammedi (blue0x1)](https://github.com/blue0x1).

GPL-2.0 (vedi `LICENSE`). KytyPS5, Mesa e il kernel Linux hanno le proprie licenze. PlayStation è un marchio di Sony Interactive Entertainment; questo progetto non è affiliato a Sony.
