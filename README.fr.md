<h1 align="center"><img src="assets/emufive-logo.png" alt="EmuFive" width="480"></h1>

<p align="center">
  <img src="https://img.shields.io/badge/platform-PS4-003791?logo=playstation&logoColor=white" alt="Platform: PS4">
  <img src="https://img.shields.io/badge/status-experimental-red" alt="Status: experimental">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--2.0-blue" alt="License: GPL-2.0"></a>
  <a href="https://github.com/blue0x1/EmuFive/releases"><img src="https://img.shields.io/github/downloads/blue0x1/EmuFive/total?label=downloads" alt="Downloads"></a>
</p>

<p align="center">
  <a href="README.md">EN</a> · <a href="README.ar.md">AR</a> · <a href="README.zh-CN.md">ZH</a> · <b>FR</b> · <a href="README.es.md">ES</a> · <a href="README.de.md">DE</a> · <a href="README.it.md">IT</a> · <a href="README.pt-BR.md">PT</a> · <a href="README.tr.md">TR</a>
</p>

Un émulateur PS5 pour la PS4.

Créé par **[Chokri Hammedi (blue0x1)](https://github.com/blue0x1)**. Basé sur [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot).

> **État : recherche expérimentale.** Sur une PS4 Pro, « Sons of Sparta » tourne à environ 40 FPS et plus. KytyPS5 réécrit les instructions processeur propres à la PS5 dans le code des jeux (patch `0004`). D'autres jeux sont encore en test, et beaucoup sont lents pour l'instant. Voir [Le problème du processeur](#the-cpu-problem).

<p align="center"><img src="assets/home-screen.png" alt="L'écran d'accueil d'EmuFive sur une PS4 Pro, avec God of War Sons of Sparta sélectionné" width="900"></p>

<p align="center">
  <b><a href="#installing">Installation</a></b> · <b><a href="#games">Jeux</a></b> · <b><a href="#changelog">Journal des modifications</a></b> · <b><a href="TROUBLESHOOTING.fr.md">Dépannage</a></b> · <a href="#how-it-works">Fonctionnement</a> · <a href="#the-cpu-problem">Le problème du processeur</a> · <a href="#plan">Feuille de route</a> · <a href="#building">Compilation</a> · <a href="#credits">Crédits</a>
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

   > **Écran noir après le menu PS4 Multiboot ?** Certaines TV préfèrent un mode que la PS4 ne peut pas envoyer. Ajoutez `emufive.mode=1920x1080@60` à la ligne de `/data/linux/boot/bootargs.txt` (gardez aussi `video=HDMI-A-1:1920x1080@60D`) et relancez le payload.

5. Dans le menu de PS4 Multiboot, choisissez **EmuFive**, puis **Install to PS4** ou **Install to USB drive**. Cela prend quelques minutes.
6. Placez vos jeux à l'un des endroits ci-dessous. Un jeu est un dossier avec `eboot.bin` (et `sce_sys`), ou un dump ZArchive (`.zar`). Les fichiers paquet (`.pkg`, fpkg) ne peuvent pas être installés ni lancés : extrayez d'abord le jeu.

Ensuite, lancez le payload pour démarrer EmuFive (si d'autres systèmes sont installés, le menu de PS4 Multiboot apparaît d'abord). Pour réinstaller, supprimez `/user/home/ps5-ps4.img` par FTP et lancez le payload. Mises à jour : Paramètres, Système, Mise à jour logicielle.

Quelque chose ne marche pas ? Voir [Dépannage](TROUBLESHOOTING.fr.md) : les solutions aux problèmes signalés, et comment enregistrer les journaux.

### Utilisation

- **Écran d'accueil :** vos jeux en tuiles. Choisissez-en un et appuyez sur Jouer. OPTIONS sur un jeu : favori, masquer, ses paramètres, trophées, temps de jeu et infos sur le jeu.
- **Touche PS en jeu :** menu de pause (Reprendre, Accueil, Fermer le jeu, volume, alimentation).
- **Captures d'écran :** PS + Carré, ou Share. Voyez-les dans Médias ; Triangle affiche un QR code pour en ouvrir une sur votre téléphone.
- **Clips vidéo :** PS + Triangle lance l'enregistrement, et PS + Triangle à nouveau l'arrête (jusqu'à 60 minutes). Les clips se lisent dans Médias et se partagent vers votre téléphone comme les captures. L'emplacement (la PS4 ou une clé USB) et la qualité (720p ou 1080p) se règlent dans Paramètres > Stockage.
- **Internet :** une tuile de navigateur web, utilisée à la manette.
- **Paramètres :** Wi-Fi, apparence, manettes, profils (jusqu'à 8), langue du menu, date et heure, sauvegarde.
- **Manettes :** une DualShock 4 par câble, ou en Bluetooth (maintenez SHARE + PS jusqu'à ce que la barre lumineuse clignote deux fois).
- **Connexion :** `ps5` / `ps5` en SSH ou sur tty2. Le journal de l'émulateur est `~/kytyps5.log`.

### Où mettre les jeux

- **Clé ou disque USB :** le dossier `PS5` à la racine (exFAT de préférence ; NTFS fonctionne aussi).
- **Disque de la PS4 :** `/user/home/PS5`, copié avec le FTP de GoldHEN (pas quand EmuFive lui-même est sur un disque USB).
- **Un PC :** un dossier partagé sous Windows ou Linux. Dans Paramètres, activez **Utiliser les jeux du PC**, indiquez l'adresse, le partage et l'identifiant, puis Connecter.

<a id="games"></a>
## Jeux

Ce projet ne contient aucun logiciel système PS5 ni aucun jeu. N'utilisez que des jeux que vous possédez et que vous avez dumpés vous-même.

<details>
<summary><b>Jeux qui fonctionnent</b></summary>

| Jeu | Console | EmuFive | Résultat |
|---|---|---|---|
| God of War Sons of Sparta | PS4 Pro | 1.0.0 | Jouable, environ 40 IPS et plus |
| Hollow Knight: Silksong | PS4 Pro | 1.0.1 | Jouable, 60 IPS |
| Plants vs. Zombies: Replanted | PS4 Pro | 1.0.4 | Jouable, 60 IPS verrouillés |
| Vampire Survivors | PS4 Slim | 1.0.4 | Jouable, 60 IPS stables |
| My Little Puppy | PS4 Slim | 1.0.6 | Tourne, 3–15 IPS (20–25 dans les zones vides) |
| DREDGE | PS4 Pro | 1.0.8 | Jouable |
| Animal Well | PS4 Pro | 1.0.9 | Jouable, 42–44 IPS |
| Teardown | PS4 Pro | 1.0.9 | Tourne, 9–12 IPS en jeu (environ 20 dans les scènes légères) avec la mémoire partagée avec le GPU |
| Invincible VS | PS4 Pro | 1.0.9 | Démarre, 4–5 IPS ; pas encore jouable |
| Blue Prince | PS4 Pro | 1.0.10 | Jouable, environ 25 IPS |
| Wytchwood | PS4 Pro | 1.0.10 | Jouable, 30 IPS stables |
| Hades II | PS4 Slim | 1.0.10 | Tourne, 20–25 IPS en jeu (10–15 dans les menus), saccades |
| Minecraft | PS4 Slim | 1.0.10 | Jouable, 30–35 IPS en jeu (56–60 dans les menus) avec la mémoire partagée avec le GPU désactivée |
| Crusader Kings III | PS4 Pro | 1.0.10 | Jouable |
| Iron Lung | PS4 Pro | 1.0.12 | Jouable, 60 IPS |
| The King is Watching | PS4 Pro | 1.0.12 | Jouable, 55–60 IPS |
| Wizard with a Gun | PS4 Pro | 1.0.12 | Tourne, 20–30 IPS, saccades ; la lueur d'un portail reste à l'écran |
| Another Crab's Treasure | PS4 Pro | 1.0.15 | Tourne, 12–17 IPS ; des artefacts restent à l'écran |
| Minecraft Dungeons 2 | PS4 Slim | 1.0.12 | Tourne avec internet coupé, 20–30 IPS |

</details>

<details>
<summary><b>Jeux qui ne fonctionnent pas encore (une version plus récente peut les corriger)</b></summary>

| Jeu | Console | EmuFive | Résultat |
|---|---|---|---|
| DRAGON BALL: Sparking! ZERO | PS4 Pro | 1.0.10 | Affiche le CLUF et les écrans en ligne, puis le GPU s'arrête |
| Hello Neighbor | PS4 Pro | 1.0.4 | S'arrête au démarrage (mesh shaders) |
| Need for Speed Unbound | PS4 Slim | 1.0.6 | Plante au démarrage (copie de profondeur non prise en charge) |
| V Rising | PS4 Pro | 1.0.8 | Plante au démarrage |
| Serious Sam 4 | PS4 Slim | 1.0.10 | Se ferme au démarrage (services en ligne) |
| Serious Sam: Siberian Mayhem | PS4 Slim | 1.0.9 | Se ferme au démarrage (services en ligne) |
| The Long Dark | PS4 Slim | 1.0.10 | Bloqué sur la vidéo d'introduction, pas de menu |

</details>

Vous avez testé un jeu ? Ouvrez une [issue](https://github.com/blue0x1/EmuFive/issues) avec le jeu, son ID de titre, le modèle de votre console, la version d'EmuFive et comment il a tourné. Les jeux qui ne fonctionnent pas sont utiles aussi (par exemple « ne démarre pas » ou « plante dans le menu ») : ils vont dans le tableau, pour que d'autres n'essaient pas le même jeu.

<a id="changelog"></a>
## Journal des modifications

### 1.0.15 (2026-11-23)

- Jeux 3D plus rapides : deux nouveaux réglages de vitesse, Thread d'envoi GPU et Moins de pièges mémoire, sont activés pour tous les jeux (Paramètres, Jeux). Another Crab's Treasure est passé de 4–10 à 12–17 IPS. Chacun peut être désactivé pour un seul jeu dans son menu OPTIONS ; Teardown démarre avec les deux désactivés, car il tourne plus vite sans eux.
- Signaler un test, dans le menu d'un jeu : une carte avec les IPS, la console et les réglages, et un QR code qui ouvre sur votre téléphone un ticket GitHub prêt.
- Un jeu qui s'arrête sur une erreur enregistre un rapport de plantage avec son journal (dans `~/PS5-reports`, et `PS5-logs` sur la clé USB).
- Un avis vous demande de sauvegarder quand la mémoire est presque pleine.
- Un jeu sur USB peut être copié sur le disque EmuFive, puis en être supprimé, depuis son menu.
- Nouveaux réglages de jeu : Dire au jeu que la TV est en 1080p, mise à l'échelle FSR 1 et connexion PSN simulée.
- Badges de compatibilité (Fonctionne, Lent, Ne fonctionne pas) sur les jeux, désactivés par défaut (Paramètres, Apparence).
- Corrigé : la liste du temps de jeu dans Paramètres, Jeux était inaccessible ; une PS4 Pro ou Slim s'affichait sous le mauvais modèle.

Pour mettre à jour depuis la 1.0.3 ou avant, lancez la mise à jour une fois à la main, car l'ancienne mise à jour du logiciel n'y arrive pas : activez SSH dans les Paramètres, connectez-vous avec `ssh ps5@<adresse de la PS4>` (mot de passe `ps5` si vous ne l'avez pas changé) et lancez

```bash
sudo systemd-run --unit=emufive-update --collect /opt/ps5-on-ps4/bin/ps5-update install
```

Elle installe toutes les mises à jour manquantes (depuis la 1.0.0 ou la 1.0.1, cela inclut les paquets du navigateur de la 1.0.2, environ 110 Mo), puis redémarrez depuis l'écran d'accueil. À partir de la 1.0.4, la mise à jour du logiciel dans les Paramètres fonctionne. Les nouvelles installations utilisent le `ps5-ps4-rootfs.tar.xz` de la version 1.0.15.

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

## Soutenir le projet

Si EmuFive vous est utile, vous pouvez soutenir le projet en Bitcoin :

BTC: `bc1q7w5ns9vsguseppllpy609yhwrtq3v56g94mjde`

## Licence

Copyright (C) 2026 [Chokri Hammedi (blue0x1)](https://github.com/blue0x1).

GPL-2.0 (voir `LICENSE`). KytyPS5, Mesa et le noyau Linux sont sous leurs propres licences. PlayStation est une marque de Sony Interactive Entertainment ; ce projet n'est pas affilié à Sony.
