# Risoluzione dei problemi

<p align="center">
  <a href="TROUBLESHOOTING.md">EN</a> · <a href="TROUBLESHOOTING.ar.md">AR</a> · <a href="TROUBLESHOOTING.zh-CN.md">ZH</a> · <a href="TROUBLESHOOTING.fr.md">FR</a> · <a href="TROUBLESHOOTING.es.md">ES</a> · <a href="TROUBLESHOOTING.de.md">DE</a> · <b>IT</b> · <a href="TROUBLESHOOTING.pt-BR.md">PT</a> · <a href="TROUBLESHOOTING.tr.md">TR</a>
</p>

I problemi segnalati nelle [issue](https://github.com/blue0x1/EmuFive/issues), con le soluzioni che hanno funzionato. Prova i passi in ordine. Ancora bloccato? Apri una issue con quanto indicato in [Cosa inviare](#what-to-send).

- [Controlla prima i file](#check-the-files-first)
- [Schermo nero o «Nessun segnale» dopo il payload](#black-screen-or-no-signal-after-the-payload)
- [Schermo nero dopo il menu o il logo di EmuFive](#black-screen-after-the-menu-or-the-emufive-logo)
- [Schermo verde, colori sbagliati o sfarfallio](#green-screen-wrong-colors-or-flickering)
- [La PS4 si spegne, o la luce resta bianca](#the-ps4-turns-off-or-the-light-stays-white)
- [«No Linux install or archive found»](#no-linux-install-or-archive-found)
- [L'installazione dura moltissimo](#installing-takes-very-long)
- [EmuFive non parte dopo un'installazione interrotta](#emufive-doesnt-start-after-a-stopped-install)
- [Funziona solo con l'unità USB collegata](#it-only-works-with-the-usb-drive-plugged-in)
- [I giochi non compaiono](#games-dont-show-up)
- [Un disco esterno non viene trovato](#an-external-drive-isnt-found)
- [Il controller non funziona](#the-controller-doesnt-work)
- [Un gioco si chiude, si blocca o è lento](#a-game-closes-freezes-or-runs-slowly)
- [Come salvare i registri](#how-to-save-the-logs)
- [Cosa inviare](#what-to-send)

<a id="check-the-files-first"></a>
## Controlla prima i file

La maggior parte dei casi «non succede niente» dipendeva da uno di questi punti:

- **Stessa versione:** `bzImage`, `initramfs.cpio.gz`, `bootargs.txt` e `linux-2048mb.bin` devono venire tutti dalla stessa [versione di PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot/releases) (meglio la più recente). Con file mescolati non parte.
- **Nomi delle cartelle in minuscolo:** la PS4 vede `LINUX` e `linux` come cartelle diverse. I percorsi devono essere esattamente `/data/linux/boot/bzImage`, `/data/linux/boot/initramfs.cpio.gz` e `/data/linux/boot/bootargs.txt`.
- **Il nome esatto dell'archivio:** `/user/home/ps5-ps4-rootfs.tar.xz`. A volte il browser lo salva come `ps5-ps4-rootfs (1).tar.xz`, e il menu non lo trova più.
- **Trasferimento binario:** in FileZilla scegli Trasferimento → Tipo di trasferimento → **Binario** prima di caricare. Un file caricato in modalità testo si rovina. Controlla che ogni file sulla PS4 abbia la stessa dimensione che nella versione.
- **Il nostro payload:** usa `linux-2048mb.bin` di PS4 Multiboot (sul firmware 14.02: `linux-2048mb-14.02.bin`). Funziona dal firmware 5.05 al 14.02. Altri payload Linux non sono supportati.

<a id="black-screen-or-no-signal-after-the-payload"></a>
## Schermo nero o «Nessun segnale» dopo il payload

Dopo l'avvio del payload, la TV mostra «Nessun segnale» o uno schermo nero per **1 o 2 minuti**, mentre Linux si avvia. È normale. Anche lo schermo e il controller che si spengono subito dopo il payload sono normali: il sistema della PS4 si chiude e Linux prende il controllo.

**Non premere il tasto PS mentre lo schermo è nero**: spegne la PS4. Con solo EmuFive sulla PS4, l'installazione parte da sola dopo 60 secondi, quindi potrebbe già essere in corso.

Se dopo 3 minuti non compare niente:

1. Collega la PS4 **direttamente** alla TV, senza switch HDMI, ricevitore AV o scheda di acquisizione.
2. Sulla PS4 disattiva **Impostazioni → Sistema → Abilita HDCP**, poi riavvia il payload.
3. Prova un altro cavo HDMI e un'altra porta HDMI.
4. Prova una volta un'altra TV o un altro monitor. Alcune TV non accettano il segnale Linux della PS4, e un altro schermo mostra se il problema è la TV.
5. Ancora niente? Salva il [registro PS4BOOT](#the-ps4boot-stick-boot-problems) e apri una issue. Dicci se la TV dice **«Nessun segnale»** o è accesa ma nera.

<a id="black-screen-after-the-menu-or-the-emufive-logo"></a>
## Schermo nero dopo il menu o il logo di EmuFive

Se vedi il menu di PS4 Multiboot o il logo di EmuFive e poi diventa nero, EmuFive è passato a una modalità che la tua TV preferisce ma che la PS4 non può inviare.

1. Aggiorna EmuFive (Impostazioni → Sistema → Aggiornamento software).
2. Via FTP apri `/data/linux/boot/bootargs.txt` e aggiungi ` emufive.mode=1920x1080@60` alla fine della riga. Tieni anche `video=HDMI-A-1:1920x1080@60D`. Il file deve restare **una sola riga**.
3. Riavvia il payload.

Non riesci ad aggiornare perché lo schermo è nero? Collega una volta un'altra TV o un altro monitor e aggiorna, oppure reinstalla EmuFive con il `ps5-ps4-rootfs.tar.xz` più recente.

<a id="green-screen-wrong-colors-or-flickering"></a>
## Schermo verde, colori sbagliati o sfarfallio

Un velo verde, il nero mostrato verde o il bianco ciano, o uno sfarfallio: la TV legge il segnale della PS4 nel formato colore sbagliato.

1. Aggiungi ` emufive.mode=1920x1080@60` a `bootargs.txt` (vedi sopra).
2. Prova un altro cavo o porta HDMI. Nelle impostazioni della TV per quella porta cambia opzioni come **HDMI UHD Color**, **Formato avanzato**, **Deep Colour** o **Input Signal Plus** (da attivo a disattivo, o viceversa), e disattiva HDMI-CEC (**Anynet+**, **Bravia Sync**...).
3. Prova un'altra TV o un altro monitor.

<a id="the-ps4-turns-off-or-the-light-stays-white"></a>
## La PS4 si spegne, o la luce resta bianca

- **Sul 14.02**, il primo avvio del payload a volte spegne la PS4. Riavvialo: il secondo tentativo di solito funziona.
- **La luce resta bianca** e per 5 minuti non succede niente: tieni premuto il tasto di accensione per spegnere la PS4, riaccendila e riavvia il payload.
- **Una luce viola** dopo l'installazione è normale.
- **La PS4 si spegne quando premi il tasto PS** a schermo nero: non premerlo, aspetta (vedi sopra).

<a id="no-linux-install-or-archive-found"></a>
## «No Linux install or archive found»

Il menu non ha trovato né un EmuFive installato né `ps5-ps4-rootfs.tar.xz`.

1. Controlla nome e posizione dell'archivio: esattamente `/user/home/ps5-ps4-rootfs.tar.xz`.
2. Su una **PS4 fat** (CUH-10xx, 11xx o 12xx), PS4 Multiboot da v1.5.0-beta.3 a beta.7 non trovava il disco interno. Usa `bzImage` e `initramfs.cpio.gz` di [v1.5.0-beta.8](https://github.com/blue0x1/ps4-multiboot/releases/tag/v1.5.0-beta.8) o più recente.

<a id="installing-takes-very-long"></a>
## L'installazione dura moltissimo

- **La creazione del disco** è il primo 25% della barra, ed è la parte lenta: tutto ciò che viene scritto sul disco della PS4 passa per la sua cifratura. Le console Baikal sono più lente. Un disco grande richiede più tempo, quindi per una prima prova scegline uno più piccolo (16 GB vanno bene). La parte dopo il 25% è più veloce.
- **Non spegnere la PS4** finché la percentuale avanza. Se non si muove per 30 minuti, apri una issue e dì dove si è fermata.
- **Schermo nero alla fine:** se la TV riceve ancora il segnale, l'installazione è molto probabilmente finita ed EmuFive si sta avviando. Se il tasto di accensione della PS4 la spegne normalmente, EmuFive è in funzione e solo l'immagine è nera: vedi [Schermo nero dopo il menu](#black-screen-after-the-menu-or-the-emufive-logo).

<a id="emufive-doesnt-start-after-a-stopped-install"></a>
## EmuFive non parte dopo un'installazione interrotta

Se la PS4 è stata spenta durante un'installazione, può restare il disco creato a metà. La schermata di errore dice **«The EmuFive disk is incomplete»**, o il registro dice `is a hole`.

1. Elimina `/user/home/ps5-ps4.img` via FTP. Tieni `ps5-ps4-rootfs.tar.xz`.
2. Avvia il payload e reinstalla. Lascialo finire senza spegnere la PS4.

<a id="it-only-works-with-the-usb-drive-plugged-in"></a>
## Funziona solo con l'unità USB collegata

Hai scelto **Install to USB drive**, quindi EmuFive si trova su quell'unità e ne ha bisogno. Per averlo sulla PS4: scollega l'unità, avvia il payload e scegli **Install to PS4**.

<a id="games-dont-show-up"></a>
## I giochi non compaiono

Un gioco è una **cartella** con `eboot.bin` e `sce_sys` dentro, o un singolo file `.zar`. I file `.pkg` e fpkg non si possono usare: estrai prima il gioco. Usa dump di giochi che possiedi.

Su un'unità USB deve essere così:

```
Unità USB (exFAT, una partizione; anche NTFS funziona)
└── PS5/                      <- esattamente "PS5", in maiuscolo, nella radice dell'unità
    ├── PPSA01234/            <- una cartella per gioco (nome qualsiasi)
    │   ├── eboot.bin         <- direttamente nella cartella del gioco
    │   ├── sce_sys/
    │   │   └── param.json    <- dà il nome e l'immagine del gioco
    │   └── ...
    └── MioGioco.zar          <- un dump .zar, come singolo file
```

Errori comuni:

- `ps5/` o `Ps5/`: il nome deve essere esattamente `PS5`.
- `Giochi/PS5/...`: la cartella `PS5` deve stare nella radice dell'unità.
- `PS5/PPSA01234/PPSA01234/eboot.bin`: un livello di cartella in più (capita spesso dopo aver decompresso). Sposta su la cartella interna.
- `PS5/eboot.bin`: i file del gioco sparsi in `PS5`, senza una cartella propria.
- Due giochi nella stessa cartella: ne compare solo uno. Il nome sul riquadro viene da `sce_sys/param.json`, non dal nome della cartella, quindi dai a ogni gioco una cartella propria.

Sul disco della PS4 la cartella è `/user/home/PS5`, e funziona solo se EmuFive è installato sulla PS4 (non su un'unità USB). Copia i giochi con l'FTP di GoldHEN dal sistema della PS4, poi avvia EmuFive: legge quella cartella all'avvio.

Tieni collegata solo l'unità dei giochi. Scollega la chiavetta dei registri `PS4BOOT` mentre giochi.

<a id="an-external-drive-isnt-found"></a>
## Un disco esterno non viene trovato

- SSD e dischi rigidi esterni funzionano da EmuFive 1.0.5. Aggiorna prima.
- Un disco che prima aveva Linux può non comparire nemmeno dopo una formattazione normale. Elimina tutte le sue partizioni (Windows: Gestione disco), poi crea una sola partizione **exFAT**.
- Se EmuFive è installato su un'unità USB, i giochi vanno su una seconda unità USB (da EmuFive 1.0.4).

<a id="the-controller-doesnt-work"></a>
## Il controller non funziona

- **Nel menu di PS4 Multiboot e nelle schermate di installazione e di errore**, il controller funziona solo **con un cavo USB**. Il Bluetooth parte più tardi, in EmuFive.
- **Via Bluetooth** va associato una volta con EmuFive, perché l'associazione del sistema PS4 non vale. Scollega il cavo, tieni premuti **SHARE + PS** finché la barra luminosa lampeggia due volte, e aspetta qualche secondo. Se non si collega, usa Impostazioni → Controller → Associa un nuovo controller.
- Usa un cavo che trasmette dati. Alcuni cavi caricano soltanto.
- Sulle console **Baikal** (molte Pro CUH-71xx/72xx e Slim recenti; vedi Impostazioni → Sistema → Informazioni di sistema), l'USB richiede PS4 Multiboot v1.5.0-beta.7 o più recente.

<a id="a-game-closes-freezes-or-runs-slowly"></a>
## Un gioco si chiude, si blocca o è lento

- **«Il gioco si è fermato (codice di errore 65)» con `ErrorDeviceLost`:** la GPU della PS4 si è bloccata sul disegno del gioco. Capita spesso con i giochi pesanti in Unreal Engine, che non sono ancora giocabili. Invia il [registro del gioco](#game-logs) se vuoi che ci guardiamo.
- **Memoria esaurita:** un gioco PS5 può usare fino a circa 12,5 GB, e Linux sulla PS4 ne ha circa 6. EmuFive chiude il gioco prima che la PS4 si blocchi. Disattiva Impostazioni → Giochi → **Memoria di gioco condivisa con la GPU** e riprova. EmuFive crea un file di swap da 4 GB solo se il suo disco ha 8 GB liberi, quindi libera spazio se il disco è pieno.
- **Un gioco si blocca o va in crash:** prova una volta con la **Memoria di gioco condivisa con la GPU** disattivata. Accelera i grandi giochi 3D, ma non va bene per tutti (Minecraft si blocca con essa).
- **Scatti la prima volta:** la prima volta che si vede una scena vengono compilati gli shader. La seconda volta è più fluida.
- **Tearing:** Impostazioni → Giochi → Cadenza dei fotogrammi → **Fluido (senza tearing)**.
- **FPS bassi:** CPU e GPU della PS4 sono molto più lente di quelle della PS5. I giochi 2D e leggeri girano bene; i giochi 3D pesanti spesso caricano e mostrano i menu, poi vanno molto lenti o restano neri in gioco. Una PS4 Pro è circa due volte più veloce di una Slim. Guarda la tabella dei [Giochi](README.it.md#games) prima di provare un gioco grande.

<a id="how-to-save-the-logs"></a>
## Come salvare i registri

<a id="the-ps4boot-stick-boot-problems"></a>
### La chiavetta PS4BOOT (problemi di avvio)

1. Formatta una chiavetta USB in **FAT32** con l'etichetta **`PS4BOOT`** (in maiuscolo). Windows non sa formattare in FAT32 chiavette oltre i 32 GB: usa una chiavetta più piccola, o [Rufus](https://rufus.ie) (Selezione boot: *Non avviabile*, File system: *Large FAT32*, Etichetta volume: `PS4BOOT`). NTFS ed exFAT non vanno bene per questo.
2. Collegala alla PS4 **prima** di avviare il payload, e lasciala inserita.
3. Avvia il payload e aspetta **5 minuti**, anche se lo schermo resta nero. Se compare una schermata di errore, salva da sola i dettagli sulla chiavetta.
4. Tieni premuto il tasto di accensione per spegnere la PS4. Collega la chiavetta a un PC e allega i file `.log` alla tua issue (`ps4-linux-boot.log`, `ps4-linux-late.log`, `ps4-linux-error.log` o `ps4-linux-rescue.log`).

Se la chiavetta resta vuota, dillo: vuol dire che Linux non è arrivato fin lì, e anche questo aiuta.

<a id="game-logs"></a>
### Registri dei giochi

Subito dopo che il gioco si è fermato, vai in Impostazioni → Sistema → **Copia i registri su USB**, poi allega i file della cartella `PS5-logs` sull'unità USB (`kytyps5.log` è il principale). Allega il file vero, non un riassunto.

<a id="what-to-send"></a>
## Cosa inviare

- Il modello di PS4 (CUH-xxxx, sull'etichetta dietro), il firmware e il southbridge (Impostazioni → Sistema → Informazioni di sistema, ad es. Belize, Baikal, Aeolia).
- La versione di PS4 Multiboot e il file payload che avvii.
- La tua riga di `bootargs.txt`.
- La tua versione di EmuFive (Impostazioni → Sistema), e se è installato sulla PS4 o su un'unità USB.
- Il modello della tua TV o monitor, e cosa mostra: «Nessun segnale», o acceso ma nero.
- La luce della PS4: bianca, blu, viola o spenta.
- I registri qui sopra.
