<h1 align="center"><img src="assets/emufive-logo.png" alt="EmuFive" width="480"></h1>

<p align="center">
  <img src="https://img.shields.io/badge/platform-PS4-003791?logo=playstation&logoColor=white" alt="Platform: PS4">
  <img src="https://img.shields.io/badge/status-experimental-red" alt="Status: experimental">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--2.0-blue" alt="License: GPL-2.0"></a>
</p>

<p align="center">
  <a href="README.md">EN</a> · <a href="README.ar.md">AR</a> · <a href="README.zh-CN.md">ZH</a> · <b>FR</b> · <a href="README.es.md">ES</a> · <a href="README.de.md">DE</a> · <a href="README.it.md">IT</a> · <a href="README.pt-BR.md">PT</a> · <a href="README.tr.md">TR</a>
</p>

Un émulateur PS5 pour la PS4.

Créé par **[Chokri Hammedi (blue0x1)](https://github.com/blue0x1)**. Basé sur [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot).

> **État : recherche expérimentale.** Sur une PS4 Pro, « Sons of Sparta » tourne à environ 40 FPS et plus. KytyPS5 réécrit les instructions processeur propres à la PS5 dans le code des jeux (patch `0004`). D'autres jeux sont encore en test, et beaucoup sont lents pour l'instant. Voir [Le problème du processeur](#the-cpu-problem).

<p align="center"><img src="assets/home-screen.png" alt="L'écran d'accueil d'EmuFive sur une PS4 Pro, avec God of War Sons of Sparta sélectionné" width="900"></p>

<p align="center">
  <b><a href="#installing">Installation</a></b> · <b><a href="#games">Jeux</a></b> · <b><a href="#changelog">Journal des modifications</a></b> · <a href="#how-it-works">Fonctionnement</a> · <a href="#the-cpu-problem">Le problème du processeur</a> · <a href="#plan">Feuille de route</a> · <a href="#building">Compilation</a> · <a href="#credits">Crédits</a>
</p>

<a id="how-it-works"></a>
## Fonctionnement

- **[PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot)** démarre Linux sur la PS4 et installe des systèmes Linux sur son disque interne, à la manette.
- **PS4 Mesa**, qui fait partie de PS4 Multiboot, donne Vulkan 1.3 au GPU de la PS4 (Liverpool sur la PS4 et la Slim, Gladius sur la Pro). KytyPS5 a besoin des ressources creuses (sparse resources), que RADV propose sur ce GPU avec `RADV_EXPERIMENTAL=sparse`.
- **KytyPS5**, le projet d'origine à un commit fixé avec les patchs de ce projet (`patches/kytyps5/`), compilé avec `-march=btver2` pour le processeur AMD Jaguar de la PS4. La version officielle utilise AVX2 et s'arrête sur la PS4 avec « Illegal instruction ».
  - `0001` : l'option de compilation `KYTY_HOST_ARCH` (le processeur pour lequel l'émulateur est compilé).
  - `0002` : une bibliothèque C pour le homebrew. Le homebrew PS5 construit avec ps5-native-app-boilerplate fournit un module de remplacement `sce_module/libc.prx` dont toutes les fonctions renvoient 0 (la console utilise sa propre bibliothèque C), si bien que son `malloc` échouait dans KytyPS5. Le patch ajoute les fonctions de la bibliothèque C qu'importe ce homebrew et ne les utilise que pour un tel module de remplacement.
  - `0003` : plus pour le homebrew : fichiers et dossiers, appels système, l'utilisateur au premier plan et des points de montage supplémentaires (`KYTY_MOUNTS`).
  - `0004` : le code PS5 sur le processeur de la PS4. Chaque instruction AVX2, FMA et BMI2 est réécrite en code SSE4.2/AVX/BMI1 au chargement d'un module ; celle qui ne peut pas être réécrite à ce moment-là est remplacée la première fois qu'elle s'exécute. Voir [Le problème du processeur](#the-cpu-problem).
- **EmuFive** réunit tout cela dans un petit système Linux qui démarre directement sur l'émulateur, en plein écran, sans bureau. Il s'installe par PS4 Multiboot comme n'importe quel autre système.

<a id="the-cpu-problem"></a>

## Le problème du processeur

KytyPS5 n'émule pas le processeur de la PS5 : il exécute directement le code x86-64 du jeu. Les jeux PS5 sont compilés pour le processeur Zen 2 de la PS5 et utilisent partout des instructions AVX2, BMI2 et FMA. Le processeur Jaguar de la PS4 n'en a aucune, donc le code du jeu s'arrête à la première de ces instructions.

Le patch `0004` ajoute cela au correcteur d'instructions invitées de KytyPS5. Quand le processeur hôte n'a pas AVX2, FMA ou BMI2, chacune de ces instructions est remplacée par du code ayant le même effet : les opérations entières sur 256 bits en deux moitiés de 128 bits, les permutations entre moitiés avec des déplacements et mélanges AVX, les décalages par élément un élément à la fois, FMA calculée en double précision, les gathers un élément à la fois, BMI2 avec des registres sauvegardés. Le saut vers un remplacement est écrit là où se trouvait l'instruction ; une instruction trop courte pour un saut, à un endroit que le correcteur ne peut pas réorganiser, provoque une faute et est remplacée à l'exécution.

`tools/jaguar-test/` vérifie chaque remplacement sur un PC qui possède ces instructions : il prend chaque forme d'instruction trouvée dans le code d'un programme, exécute l'original et le remplacement depuis le même état aléatoire, et compare tous les registres, les indicateurs et la mémoire. Les formes trouvées dans les programmes testés jusqu'ici concordent : 287 dans God of War Sons of Sparta (gathers et VFMADDSUB compris) et 227 dans les programmes testés avant. Les exceptions sont de rares différences sur le dernier bit en FMA (la simple précision est arrondie deux fois, la double précision est une multiplication puis une addition) et un cas particulier de NaN pour 0 fois l'infini.

Le Jaguar reste bien plus lent que le processeur de la PS5, et les remplacements s'y ajoutent, donc même un jeu qui fonctionne peut tourner lentement.

<a id="plan"></a>
## Feuille de route

| Étape | État |
|---|---|
| Vulkan sur le GPU de la PS4 répond aux besoins de KytyPS5 | Fait (`RADV_EXPERIMENTAL=sparse`) |
| KytyPS5 compilé pour le processeur de la PS4 | Fait (`KYTY_HOST_ARCH=btver2`) |
| KytyPS5 démarre sur la PS4 et initialise le GPU | Fait, PS4 Pro |
| Image système EmuFive, installée par PS4 Multiboot | Fait, PS4 Pro |
| Un homebrew PS5 sans AVX2 tourne et affiche | Fait : Snes9x PS5 2.11 recompilé pour btver2, PS4 Pro |
| Manette, stockage `/data` et USB, chargement d'un jeu dans cette application | Fait sur une version de test PC (mêmes patchs) ; PS4 ensuite |
| Traduction AVX2, BMI2 et FMA pour le code des jeux | Fait (`0004`), vérifié sur un PC |
| Un jeu PS5 tourne sur la PS4 | Fait : God of War Sons of Sparta, environ 40 FPS et plus, PS4 Pro |
| Hollow Knight: Silksong tourne sur la PS4 | Fait depuis la 1.0.1 (patchs `0006` et `0007`), PS4 Pro |
| Écran d'accueil : choisir un jeu à la manette ; Wi-Fi ; Paramètres | Fait, vérifié sur un PC |
| Jeux depuis la clé USB, le disque de la PS4 ou un partage PC | Fait, vérifié sur un PC ; PS4 ensuite |

<a id="building"></a>

## Compilation

Il faut Docker, git et le PS4 Mesa de PS4 Multiboot (`../PS4-Multiboot/out/ps4-mesa.tar.xz`, compilé là-bas avec `make mesa`). `build-kyty.sh` clone KytyPS5 dans `build/kytyps5` la première fois, puis à chaque compilation le remet au commit fixé et applique les patchs.

```bash
scripts/build-kyty.sh      # out/kytyps5-ps4.tar.xz
scripts/build-rootfs.sh    # out/ps5-ps4-rootfs.tar.xz
```

`PS4_MESA` et `KYTY` indiquent d'autres chemins à `build-rootfs.sh`.

<a id="installing"></a>

## Installation

EmuFive s'installe par [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot), comme n'importe quel autre système Linux.

Il vous faut :

- Une PS4 jailbreakée avec **GoldHEN** (pour son serveur FTP et son chargeur de payloads).
- Un PC sur le même réseau avec un client FTP (par exemple FileZilla).
- Environ 28 Go libres sur la PS4 (un disque de 16 Go, et 10 Go toujours laissés libres pour la PS4), ou une clé USB de 8 Go ou plus.
- Une DualShock 4 (avec un câble USB, ou appairée en Bluetooth plus tard).

Étapes :

1. Depuis les [versions de PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot/releases), téléchargez `bzImage`, `initramfs.cpio.gz`, `bootargs.txt` et `linux-2048mb.bin`. (`ps4-mesa.tar.xz` n'est pas nécessaire : EmuFive inclut PS4 Mesa.)
2. Depuis les [versions d'EmuFive](https://github.com/blue0x1/EmuFive/releases), téléchargez `ps5-ps4-rootfs.tar.xz` (ou compilez-le, voir [Compilation](#building)). Gardez son nom : PS4 Multiboot trouve les systèmes grâce au `-ps4-rootfs` qu'il contient.
3. Activez le serveur FTP de GoldHEN et copiez les fichiers sur la PS4 (port 2121) :

   | Fichier | Dossier sur la PS4 |
   |---|---|
   | `bzImage`, `initramfs.cpio.gz`, `bootargs.txt` | `/data/linux/boot/` |
   | `ps5-ps4-rootfs.tar.xz` | `/user/home/` |
   | `linux-2048mb.bin` | `/data/payloads/` |

4. Lancez `linux-2048mb.bin` depuis le menu des payloads de GoldHEN.

   > **Soyez patient :** après le lancement du payload, la TV peut afficher **« No signal » ou un écran noir pendant 1 à 2 minutes** pendant que Linux démarre. C'est normal.

5. Dans le menu de PS4 Multiboot, choisissez **EmuFive**, puis **Install to PS4** ou **Install to USB drive**. Cela prend quelques minutes.
6. Placez vos jeux à l'un des endroits ci-dessous. Un jeu est un dossier avec `eboot.bin` (et `sce_sys`), ou un dump ZArchive (`.zar`).

Ensuite, lancez le payload pour démarrer EmuFive : si seul EmuFive est installé, il démarre tout de suite ; avec d'autres systèmes, le menu de PS4 Multiboot apparaît d'abord. Éteignez ou redémarrez depuis l'écran d'accueil pour revenir au système de la PS4. Pour réinstaller EmuFive, supprimez `/user/home/ps5-ps4.img` par FTP et lancez le payload.

Les mises à jour viennent des versions d'EmuFive : Paramètres, Système, Mise à jour du logiciel (aucune réinstallation nécessaire).

Le système démarre sur l'écran d'accueil et n'a pas besoin de clavier :

- Les jeux s'affichent en tuiles, chacune indiquant où se trouve le jeu : **USB**, **PS4** ou **PC**. Choisissez-en un et appuyez sur Jouer ; quand il se ferme, l'écran d'accueil revient.
- En haut : le Wi-Fi (avec un clavier à l'écran pour le mot de passe) et les Paramètres, et deux onglets, **Jeux** et **Médias** (L1 / R1). Médias affiche vos captures d'écran ; ouvrez-en une, et Carré la supprime.
- OPTIONS sur un jeu : favori, masquer, ses propres réglages, ses trophées et votre temps de jeu.
- **Internet**, la tuile après les jeux : un navigateur web utilisé à la manette. Le stick gauche (ou le pavé tactile) déplace le pointeur et X clique ; le stick droit fait défiler ; O ou L1 revient en arrière, R1 en avant ; L2 et R2 zooment. Triangle saisit une adresse ou une recherche, et choisir une zone de texte sur une page ouvre le clavier à l'écran. OPTIONS ouvre le menu : favoris, page d'accueil, zoom, moteur de recherche (Google, DuckDuckGo ou Bing), sites mobiles (pages plus légères) et effacement de l'historique et des cookies. La touche PS revient à l'écran d'accueil, et la même page s'ouvre la fois suivante. C'est WebKitGTK, une page à la fois, environ 450 Mo de mémoire avec une page de texte et davantage avec les sites vidéo ; l'écran d'accueil se ferme pendant qu'il tourne, et un jeu en pause doit d'abord être fermé. Les téléchargements, les envois de fichiers, la caméra, le micro et la localisation sont refusés. Les favoris sont dans `~/.config/ps5-on-ps4/browser.json`, les cookies dans `~/.local/share/ps5-browser`.
- La touche PS pendant un jeu le met en pause et ouvre le menu rapide : Reprendre, **Accueil** (l'écran d'accueil, le jeu restant en pause : PS ou Reprendre y revient ; lancer un autre jeu demande d'abord, puis le ferme), fermer le jeu, volume, alimentation.
- Captures d'écran : PS + Carré, ou Share, aussi en jeu. Elles vont dans `PS5-screenshots` sur la clé USB (ou `~/Screenshots` sans clé), avec une petite notification dans le coin. Pour en récupérer une sur votre téléphone, ouvrez-la dans Médias et appuyez sur Triangle (Partager) : scannez le QR code avec le téléphone (sur le même réseau) pour l'ouvrir dessus, puis enregistrez-la ou partagez-la. La PS4 ne sert que cette image, à une adresse aléatoire, et seulement tant que le code est affiché. Les QR codes viennent de `python3-segno`.
- Paramètres, Apparence : couleur d'accent, thème (sombre, minuit, clair), fond (l'illustration du jeu, un dégradé, une couleur unie ou votre propre image depuis la clé USB), assombrissement du fond, orbes flottants, animations, taille et forme des tuiles, taille et police du texte, horloge, ce qu'affiche la barre du haut (la batterie est celle de la manette), sons du menu, vibrations, aides des boutons, bords de l'écran (overscan) et économiseur d'écran.
- Paramètres, Manettes : couleur et luminosité de la barre lumineuse, vibrations activées ou non et leur force, micro de la manette activé ou non (avec la manette sur un câble USB ; Linux n'a pas le son de la manette en Bluetooth), inversion de X et O, et une page de test pour chaque bouton et stick. Paramètres, Jeux : réglages par défaut de tous les jeux, langue des jeux, HDR et régulation des images. Paramètres, Date et heure : automatique depuis internet (par défaut) ou à la main. Paramètres, Système : la langue du menu (anglais, arabe, français, turc, espagnol, allemand, italien ou portugais du Brésil), température et charge du processeur, sauvegarde des réglages sur la clé USB, ou tout réinitialiser.
- Profils (Paramètres, Profil, et Changer de profil dans le menu rapide) : jusqu'à 8, chacun avec son nom, son avatar, ses sauvegardes, ses trophées et son temps de jeu. Avec plus d'un profil, « Qui joue ? » s'ouvre au démarrage. Chaque profil a son propre dossier KytyPS5 (`~/.kytyps5/users/<ID>`, le premier profil garde `~/.kytyps5`), avec le cache des shaders partagé.
- Notifications dans le coin supérieur gauche, aussi en jeu : capture d'écran enregistrée, manette connectée (avec sa connexion et son niveau de batterie), batterie de la manette faible (15 %). La batterie de la barre du haut est verte, jaune ou rouge selon le niveau, avec un éclair pendant la charge.
- Mémoire épuisée : un fichier d'échange (swap) de 4 Go sur le disque système (`ps5-swap.service`, créé une fois quand il y a la place) permet à un gros jeu de ralentir au lieu de figer la PS4, et si la mémoire et le swap s'épuisent quand même, le jeu est fermé avant que la PS4 se fige et l'écran d'accueil en indique la raison.
- Langues du menu : les traductions sont dans `lib/ps5/translations.json`, une entrée par texte anglais. L'arabe est aligné à droite et affiché avec DejaVu Sans ; ses lettres sont liées dans `lib/ps5/i18n.py`, car SDL_ttf ici ne les lie pas.
- Le programme voit la clé USB comme `/mnt/usb0` et un dossier du système (`~/data`, conservé entre les démarrages) comme `/data`. Pour Snes9x PS5, les ROMs vont dans `snes9x/roms` sur la clé USB ou dans `~/data/snes9x/roms`.
- Si l'émulateur s'arrête sur une erreur, l'écran d'accueil en affiche la raison.
- `PS5_GAME` dans `/etc/ps5-on-ps4.conf` lance directement un jeu au lieu de l'écran d'accueil.
- Manettes : une DualShock 4 avec câble, ou en Bluetooth après avoir maintenu SHARE + PS jusqu'à ce que la barre lumineuse clignote deux fois.
- Le son va à la TV en HDMI, même quand une manette sur câble apporte sa propre carte son (`/etc/wireplumber/wireplumber.conf.d/51-ps5-hdmi.conf`).

### Où mettre les jeux

- **Clé USB :** le dossier `PS5` à la racine de la clé. exFAT est le mieux (fichiers de plus de 4 Go) ; NTFS fonctionne aussi.
- **Disque de la PS4 :** `/user/home/PS5` sur la PS4, copié avec le FTP de GoldHEN. Le système lit le disque de la PS4 en lecture seule et ne le modifie jamais. Indisponible quand le système lui-même est installé sur une clé USB.
- **Un PC :** un dossier partagé sous Windows ou Linux. Dans les Paramètres, activez **Utiliser les jeux du PC** et indiquez l'adresse du PC, le dossier partagé et, sauf pour un partage invité, un nom d'utilisateur et un mot de passe ; puis Se connecter. Les jeux peuvent être à la racine du dossier partagé ou dans un dossier `PS5` à l'intérieur. Un câble réseau est plus rapide que le Wi-Fi.
  - Windows : partagez le dossier (Propriétés, Partage). Pour un partage invité, partagez-le avec Everyone et désactivez *Password protected sharing* dans les paramètres de partage avancés.
  - Linux (Samba) : un partage avec `guest ok = yes` pour un partage invité, ou un utilisateur Samba (`smbpasswd -a`).
  - Le noyau de la PS4 n'a pas de client SMB, donc le système utilise smbnetfs (FUSE). Les réglages, mot de passe compris, sont gardés dans `~/.config/ps5-on-ps4/pc-share.json`, lisible uniquement par l'utilisateur `ps5`.

`tools/make-pad-test-rom.py` écrit une petite ROM SNES pour tester une manette : bleue, verte tant qu'un bouton est appuyé.

Connexion : `ps5` / `ps5` sur tty2 ou en SSH. La sortie de l'émulateur est dans `~/kytyps5.log` (le lancement précédent : `~/kytyps5.log.1`).

<a id="games"></a>
## Jeux

Ce projet ne contient aucun logiciel système PS5 ni aucun jeu. N'utilisez que des jeux que vous possédez et que vous avez dumpés vous-même.

Jeux testés :

| Jeu | Console | Résultat |
|---|---|---|
| God of War Sons of Sparta | PS4 Pro | Jouable, environ 40 FPS et plus |
| Hollow Knight: Silksong | PS4 Pro | Jouable, de 50 à 60 FPS |
| Plants vs. Zombies: Replanted | PS4 Pro | Jouable, 60 FPS constants |
| Vampire Survivors | PS4 Slim | Jouable, 60 FPS stables |
| Spider-Man 2 | | Pas encore testé |

Vous avez testé un jeu ? Ouvrez une [issue](https://github.com/blue0x1/EmuFive/issues) avec le jeu, le modèle de votre console et comment il a tourné.

<a id="changelog"></a>
## Journal des modifications

### 1.0.6 (2026-11-14)

- Amélioré : l'écran d'accueil utilise beaucoup moins le processeur quand personne ne s'en sert (en 4K environ un tiers d'un cœur, contre un cœur entier avant), donc la PS4 chauffe moins et fait moins de bruit.

Pour mettre à jour depuis la 1.0.3 ou avant, lancez la mise à jour une fois à la main, car l'ancienne mise à jour du logiciel n'y arrive pas : activez SSH dans les Paramètres, connectez-vous avec `ssh ps5@<adresse de la PS4>` (mot de passe `ps5` si vous ne l'avez pas changé) et lancez

```bash
sudo systemd-run --unit=emufive-update --collect /opt/ps5-on-ps4/bin/ps5-update install
```

Elle installe toutes les mises à jour manquantes (depuis la 1.0.0 ou la 1.0.1, cela inclut les paquets du navigateur de la 1.0.2, environ 110 Mo), puis redémarrez depuis l'écran d'accueil. À partir de la 1.0.4, la mise à jour du logiciel dans les Paramètres fonctionne. Les nouvelles installations utilisent le `ps5-ps4-rootfs.tar.xz` de la version 1.0.6.

## Organisation du projet

| Chemin | Contenu |
|---|---|
| `scripts/build-kyty.sh` | Compile KytyPS5 (le projet d'origine plus `patches/kytyps5/`) pour le processeur de la PS4 |
| `patches/kytyps5/` | Les modifications de ce projet à KytyPS5 |
| `scripts/build-rootfs.sh` | Construit l'image système pour PS4 Multiboot |
| `scripts/make-release.sh` | Crée le paquet de mise à jour d'une version (installé par Paramètres, Système, Mise à jour du logiciel) |
| `scripts/updates/` | Scripts qu'une mise à jour lance sur la PS4 une fois ses fichiers en place (`--post`) |
| `docker/` | Environnements de compilation pour les deux |
| `overlay/` | Fichiers ajoutés au système : session, écran d'accueil, paramètres, montage de la clé USB et du disque de la PS4, appairage des manettes |
| `tools/` | Convertisseur de logo, ROM de test de manette, `extract-code.py` (le code d'un SELF/ELF PS5) |
| `tools/jaguar-test/` | Vérifie les remplacements du patch `0004` par rapport aux vraies instructions |

## Remerciements particuliers

- [KytyPS5](https://github.com/KytyPS5/KytyPS5), l'émulateur PS5 sur lequel EmuFive est basé (GPL-2.0)
- [Kyty](https://github.com/InoriRus/Kyty) par InoriRus, l'émulateur sur lequel KytyPS5 est basé

<a id="credits"></a>
## Crédits

- [Mesa](https://mesa3d.org), et les patchs GPU PS4 de fail0verflow, DionKill et striker91n
- Les développeurs du noyau Linux pour PS4 ([sony-jaguar-devs/ps4-linux](https://github.com/sony-jaguar-devs/ps4-linux))

## Licence

Copyright (C) 2026 [Chokri Hammedi (blue0x1)](https://github.com/blue0x1).

GPL-2.0 (voir `LICENSE`). KytyPS5, Mesa et le noyau Linux sont sous leurs propres licences. PlayStation est une marque de Sony Interactive Entertainment ; ce projet n'est pas affilié à Sony.
