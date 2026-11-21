<h1 align="center"><img src="assets/emufive-logo.png" alt="EmuFive" width="480"></h1>

<p align="center">
  <img src="https://img.shields.io/badge/platform-PS4-003791?logo=playstation&logoColor=white" alt="Platform: PS4">
  <img src="https://img.shields.io/badge/status-experimental-red" alt="Status: experimental">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--2.0-blue" alt="License: GPL-2.0"></a>
  <a href="https://github.com/blue0x1/EmuFive/releases"><img src="https://img.shields.io/github/downloads/blue0x1/EmuFive/total?label=downloads" alt="Downloads"></a>
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

   > **Schermo nero dopo il menu di PS4 Multiboot?** Alcune TV preferiscono una modalità che la PS4 non può inviare. Aggiungi `emufive.mode=1920x1080@60` alla riga in `/data/linux/boot/bootargs.txt` (lascia anche `video=HDMI-A-1:1920x1080@60D`) ed esegui di nuovo il payload.

5. Nel menu di PS4 Multiboot, scegli **EmuFive**, poi **Install to PS4** o **Install to USB drive**. Ci vogliono alcuni minuti.
6. Metti i tuoi giochi in uno dei posti qui sotto. Un gioco è una cartella con `eboot.bin` (e `sce_sys`), oppure un dump ZArchive (`.zar`). I file pacchetto (`.pkg`, fpkg) non si possono installare né avviare: estrai prima il gioco.

Dopo, avvia il payload per far partire EmuFive (con altri sistemi installati, compare prima il menu di PS4 Multiboot). Per reinstallare, elimina `/user/home/ps5-ps4.img` via FTP e avvia il payload. Aggiornamenti: Impostazioni, Sistema, Aggiornamento software.

### Uso

- **Schermata Home:** i tuoi giochi come riquadri. Scegline uno e premi Gioca. OPTIONS su un gioco: preferito, nascondi, le sue impostazioni, trofei, tempo di gioco e info sul gioco.
- **Tasto PS in un gioco:** menu di pausa (Riprendi, Home, Chiudi il gioco, volume, spegnimento).
- **Screenshot:** PS + Quadrato, o Share. Guardali in Media; Triangolo mostra un codice QR per aprirne uno sul telefono.
- **Clip video:** PS + Triangolo avvia la registrazione, e PS + Triangolo di nuovo la ferma (fino a 60 minuti). Le clip si guardano in Media e si condividono sul telefono come gli screenshot. Dove salvarle (la PS4 o un'unità USB) e la qualità (720p o 1080p) sono in Impostazioni > Archiviazione.
- **Internet:** un riquadro con il browser web, usato con il controller.
- **Impostazioni:** Wi-Fi, aspetto, controller, profili (fino a 8), lingua del menu, data e ora, backup.
- **Controller:** un DualShock 4 via cavo, o via Bluetooth (tieni premuti SHARE + PS finché la barra luminosa lampeggia due volte).
- **Accesso:** `ps5` / `ps5` via SSH o su tty2. Il log dell'emulatore è `~/kytyps5.log`.

### Dove possono stare i giochi

- **Unità USB:** la cartella `PS5` nella radice dell'unità (exFAT è il migliore; va bene anche NTFS).
- **Disco della PS4:** `/user/home/PS5`, copiato con l'FTP di GoldHEN (non quando EmuFive stesso è su un'unità USB).
- **Un PC:** una cartella condivisa su Windows o Linux. In Impostazioni attiva **Usa giochi dal PC**, inserisci indirizzo, condivisione e credenziali, poi Connetti.

## Giochi

Questo progetto non contiene software di sistema PS5 né giochi. Usa solo giochi che possiedi e di cui hai fatto il dump tu stesso.

<details>
<summary><b>Giochi che funzionano</b></summary>

| Gioco | Console | EmuFive | Risultato |
|---|---|---|---|
| God of War Sons of Sparta | PS4 Pro | 1.0.0 | Giocabile, circa 40 FPS e più |
| Hollow Knight: Silksong | PS4 Pro | 1.0.1 | Giocabile, 60 FPS |
| Plants vs. Zombies: Replanted | PS4 Pro | 1.0.4 | Giocabile, 60 FPS fissi |
| Vampire Survivors | PS4 Slim | 1.0.4 | Giocabile, 60 FPS stabili |
| My Little Puppy | PS4 Slim | 1.0.6 | Funziona, 3–15 FPS (20–25 nelle zone vuote) |
| DREDGE | PS4 Pro | 1.0.8 | Giocabile |
| Animal Well | PS4 Pro | 1.0.9 | Giocabile, 42–44 FPS |
| Teardown | PS4 Pro | 1.0.9 | Funziona, 9–12 FPS in gioco (circa 20 nelle scene leggere) con la memoria condivisa con la GPU |
| Invincible VS | PS4 Pro | 1.0.9 | Si avvia, 4–5 FPS; non ancora giocabile |
| Blue Prince | PS4 Pro | 1.0.10 | Giocabile, circa 25 FPS |
| Wytchwood | PS4 Pro | 1.0.10 | Giocabile, 30 FPS stabili |
| Hades II | PS4 Slim | 1.0.10 | Funziona, 20–25 FPS in gioco (10–15 nei menu), scatti |
| Minecraft | PS4 Slim | 1.0.10 | Giocabile, 30–35 FPS in gioco (56–60 nei menu) con la memoria condivisa con la GPU disattivata |
| Crusader Kings III | PS4 Pro | 1.0.10 | Giocabile |
| Iron Lung | PS4 Pro | 1.0.12 | Giocabile, 60 FPS |
| The King is Watching | PS4 Pro | 1.0.12 | Giocabile, 55–60 FPS |
| Wizard with a Gun | PS4 Pro | 1.0.12 | Funziona, 20–30 FPS con scatti; il bagliore di un portale resta sullo schermo |
| Another Crab's Treasure | PS4 Pro | 1.0.12 | Funziona, 4–10 FPS; restano artefatti grafici sullo schermo |
| Minecraft Dungeons 2 | PS4 Slim | 1.0.12 | Funziona con internet scollegato, 20–30 FPS |

</details>

<details>
<summary><b>Giochi che non funzionano ancora (una versione più nuova può risolverli)</b></summary>

| Gioco | Console | EmuFive | Risultato |
|---|---|---|---|
| DRAGON BALL: Sparking! ZERO | PS4 Pro | 1.0.10 | Mostra l'EULA e le schermate online, poi la GPU si ferma |
| Hello Neighbor | PS4 Pro | 1.0.4 | Si ferma all'avvio (mesh shader) |
| Need for Speed Unbound | PS4 Slim | 1.0.6 | Va in crash all'avvio (copia di profondità non supportata) |
| V Rising | PS4 Pro | 1.0.8 | Va in crash all'avvio |
| Serious Sam 4 | PS4 Slim | 1.0.10 | Si chiude all'avvio (servizi online) |
| Serious Sam: Siberian Mayhem | PS4 Slim | 1.0.9 | Si chiude all'avvio (servizi online) |
| The Long Dark | PS4 Slim | 1.0.10 | Bloccato sul video introduttivo, nessun menu |

</details>

Hai provato un gioco? Apri una [issue](https://github.com/blue0x1/EmuFive/issues) con il gioco, il suo ID del titolo, il modello della tua console, la versione di EmuFive e come è andato. Anche i giochi che non funzionano sono utili (per esempio «non si avvia» o «va in crash nel menu»): finiscono nella tabella, così altri non provano lo stesso gioco.

<a id="changelog"></a>
## Registro delle modifiche

### 1.0.13 (2026-11-21)

- Novità: un gestore di trucchi. Attivalo in Impostazioni, Giochi, e sulla schermata Home compare il riquadro Trucchi. Scarica i trucchi PS5 della [HEN Cheats Collection](https://github.com/TeeKay87/HEN-Cheats-Collection) ed elenca i tuoi giochi che hanno trucchi per la loro versione; scegli quelli che vuoi e vengono applicati all'avvio del gioco. Il menu di un gioco mostra quanti sono attivi.
- Corretto: blocchi a scacchiera sulle pagine web in Internet (#61).
- Tastiera: R1 è Maiusc, L1 è Spazio, e Maiusc due volte è il blocco maiuscole (#61).
- I giochi `.zar` mostrano nome, icona e sfondo sulla schermata Home (#54).

Per aggiornare dalla 1.0.3 o precedenti, avvia l'aggiornamento una volta a mano, perché il vecchio aggiornamento software non ci riesce: attiva SSH nelle Impostazioni, collegati con `ssh ps5@<indirizzo della PS4>` (password `ps5` se non l'hai cambiata) ed esegui

```bash
sudo systemd-run --unit=emufive-update --collect /opt/ps5-on-ps4/bin/ps5-update install
```

Installa tutti gli aggiornamenti mancanti (dalla 1.0.0 o 1.0.1 include i pacchetti del browser della 1.0.2, circa 110 MB), poi riavvia dalla schermata Home. Dalla 1.0.4 l'aggiornamento software nelle Impostazioni funziona. Le nuove installazioni usano il `ps5-ps4-rootfs.tar.xz` della versione 1.0.13.

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

## Sostieni il progetto

Se EmuFive ti è utile, puoi sostenere il progetto con Bitcoin:

BTC: `bc1q7w5ns9vsguseppllpy609yhwrtq3v56g94mjde`

## Licenza

Copyright (C) 2026 [Chokri Hammedi (blue0x1)](https://github.com/blue0x1).

GPL-2.0 (vedi `LICENSE`). KytyPS5, Mesa e il kernel Linux hanno le proprie licenze. PlayStation è un marchio di Sony Interactive Entertainment; questo progetto non è affiliato a Sony.
