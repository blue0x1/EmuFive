# Dépannage

<p align="center">
  <a href="TROUBLESHOOTING.md">EN</a> · <a href="TROUBLESHOOTING.ar.md">AR</a> · <a href="TROUBLESHOOTING.zh-CN.md">ZH</a> · <b>FR</b> · <a href="TROUBLESHOOTING.es.md">ES</a> · <a href="TROUBLESHOOTING.de.md">DE</a> · <a href="TROUBLESHOOTING.it.md">IT</a> · <a href="TROUBLESHOOTING.pt-BR.md">PT</a> · <a href="TROUBLESHOOTING.tr.md">TR</a>
</p>

Les problèmes signalés dans les [issues](https://github.com/blue0x1/EmuFive/issues), avec les solutions qui ont marché. Essayez les étapes dans l'ordre. Toujours bloqué ? Ouvrez une issue avec ce qui est listé dans [Quoi envoyer](#what-to-send).

- [Vérifiez d'abord les fichiers](#check-the-files-first)
- [Écran noir ou « Aucun signal » après le payload](#black-screen-or-no-signal-after-the-payload)
- [Écran noir après le menu ou le logo EmuFive](#black-screen-after-the-menu-or-the-emufive-logo)
- [Écran vert, mauvaises couleurs ou scintillement](#green-screen-wrong-colors-or-flickering)
- [La PS4 s'éteint, ou le voyant reste blanc](#the-ps4-turns-off-or-the-light-stays-white)
- [« No Linux install or archive found »](#no-linux-install-or-archive-found)
- [L'installation est très longue](#installing-takes-very-long)
- [EmuFive ne démarre pas après une installation interrompue](#emufive-doesnt-start-after-a-stopped-install)
- [Ça ne marche qu'avec le disque USB branché](#it-only-works-with-the-usb-drive-plugged-in)
- [Les jeux n'apparaissent pas](#games-dont-show-up)
- [Un disque externe n'est pas trouvé](#an-external-drive-isnt-found)
- [La manette ne marche pas](#the-controller-doesnt-work)
- [Un jeu se ferme, se fige ou est lent](#a-game-closes-freezes-or-runs-slowly)
- [Enregistrer les journaux](#how-to-save-the-logs)
- [Quoi envoyer](#what-to-send)

<a id="check-the-files-first"></a>
## Vérifiez d'abord les fichiers

La plupart des « il ne se passe rien » venaient de l'un de ces points :

- **Même version :** `bzImage`, `initramfs.cpio.gz`, `bootargs.txt` et `linux-2048mb.bin` doivent tous venir de la même [version de PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot/releases) (la plus récente de préférence). Des fichiers mélangés ne démarrent pas.
- **Noms de dossiers en minuscules :** la PS4 voit `LINUX` et `linux` comme deux dossiers différents. Les chemins doivent être exactement `/data/linux/boot/bzImage`, `/data/linux/boot/initramfs.cpio.gz` et `/data/linux/boot/bootargs.txt`.
- **Le nom exact de l'archive :** `/user/home/ps5-ps4-rootfs.tar.xz`. Un navigateur l'enregistre parfois sous `ps5-ps4-rootfs (1).tar.xz`, et le menu ne la trouve plus.
- **Transfert binaire :** dans FileZilla, choisissez Transfert → Type de transfert → **Binaire** avant d'envoyer. Un fichier envoyé en mode texte est abîmé. Vérifiez que chaque fichier sur la PS4 a la même taille que dans la version.
- **Notre payload :** utilisez `linux-2048mb.bin` de PS4 Multiboot (en firmware 14.02 : `linux-2048mb-14.02.bin`). Il marche du firmware 5.05 au 14.02. Les autres payloads Linux ne sont pas pris en charge.

<a id="black-screen-or-no-signal-after-the-payload"></a>
## Écran noir ou « Aucun signal » après le payload

Après le lancement du payload, la TV affiche « Aucun signal » ou un écran noir pendant **1 à 2 minutes**, le temps que Linux démarre. C'est normal. Que l'écran et la manette s'éteignent juste après le payload est normal aussi : le système de la PS4 s'arrête et Linux prend le relais.

**N'appuyez pas sur le bouton PS tant que l'écran est noir** : cela éteint la PS4. Avec seulement EmuFive sur la PS4, l'installation démarre seule après 60 secondes, elle est peut-être déjà en cours.

Si rien n'apparaît après 3 minutes :

1. Branchez la PS4 **directement** sur la TV, sans switch HDMI, ampli AV ni carte d'acquisition.
2. Sur la PS4, désactivez **Paramètres → Système → Activer HDCP**, puis relancez le payload.
3. Essayez un autre câble HDMI et un autre port HDMI.
4. Essayez une fois une autre TV ou un autre moniteur. Certaines TV n'acceptent pas le signal Linux de la PS4, et un autre écran montre si le problème vient de la TV.
5. Toujours rien ? Enregistrez le [journal PS4BOOT](#the-ps4boot-stick-boot-problems) et ouvrez une issue. Dites-nous si la TV indique **« Aucun signal »** ou si elle est allumée mais noire.

<a id="black-screen-after-the-menu-or-the-emufive-logo"></a>
## Écran noir après le menu ou le logo EmuFive

Si vous voyez le menu PS4 Multiboot ou le logo d'EmuFive, puis que l'écran devient noir, EmuFive est passé à un mode que votre TV préfère mais que la PS4 ne sait pas envoyer.

1. Mettez EmuFive à jour (Paramètres → Système → Mise à jour du logiciel).
2. Par FTP, ouvrez `/data/linux/boot/bootargs.txt` et ajoutez ` emufive.mode=1920x1080@60` à la fin de la ligne. Gardez aussi `video=HDMI-A-1:1920x1080@60D`. Le fichier doit rester sur **une seule ligne**.
3. Relancez le payload.

Impossible de mettre à jour parce que l'écran est noir ? Branchez une fois une autre TV ou un autre moniteur pour faire la mise à jour, ou réinstallez EmuFive avec le `ps5-ps4-rootfs.tar.xz` le plus récent.

<a id="green-screen-wrong-colors-or-flickering"></a>
## Écran vert, mauvaises couleurs ou scintillement

Un voile vert, le noir affiché en vert ou le blanc en cyan, ou un scintillement : la TV lit le signal de la PS4 dans le mauvais format de couleurs.

1. Ajoutez ` emufive.mode=1920x1080@60` à `bootargs.txt` (voir plus haut).
2. Essayez un autre câble ou port HDMI. Dans les réglages de la TV pour ce port, changez des options comme **HDMI UHD Color**, **Format amélioré**, **Deep Colour** ou **Input Signal Plus** (activé vers désactivé, ou l'inverse), et désactivez HDMI-CEC (**Anynet+**, **Bravia Sync**...).
3. Essayez une autre TV ou un autre moniteur.

<a id="the-ps4-turns-off-or-the-light-stays-white"></a>
## La PS4 s'éteint, ou le voyant reste blanc

- **En 14.02**, le premier lancement du payload éteint parfois la PS4. Relancez-le : un deuxième essai marche en général.
- **Le voyant reste blanc** et rien ne se passe pendant 5 minutes : maintenez le bouton d'alimentation pour éteindre la PS4, rallumez-la et relancez le payload.
- **Un voyant violet** après l'installation est normal.
- **La PS4 s'éteint quand vous appuyez sur le bouton PS** sur un écran noir : n'appuyez pas, attendez (voir plus haut).

<a id="no-linux-install-or-archive-found"></a>
## « No Linux install or archive found »

Le menu n'a trouvé ni EmuFive installé, ni `ps5-ps4-rootfs.tar.xz`.

1. Vérifiez le nom et l'emplacement de l'archive : exactement `/user/home/ps5-ps4-rootfs.tar.xz`.
2. Sur une **PS4 fat** (CUH-10xx, 11xx ou 12xx), PS4 Multiboot v1.5.0-beta.3 à beta.7 ne trouvait pas le disque interne. Utilisez le `bzImage` et le `initramfs.cpio.gz` de [v1.5.0-beta.8](https://github.com/blue0x1/ps4-multiboot/releases/tag/v1.5.0-beta.8) ou plus récente.

<a id="installing-takes-very-long"></a>
## L'installation est très longue

- **La création du disque** correspond aux premiers 25 % de la barre, et c'est la partie lente : tout ce qui est écrit sur le disque de la PS4 passe par le chiffrement de la PS4. Les consoles Baikal sont plus lentes. Un gros disque prend plus de temps, alors pour un premier essai choisissez-en un plus petit (16 Go suffisent). La suite après 25 % va plus vite.
- **N'éteignez pas la PS4** tant que le pourcentage avance. S'il ne bouge plus pendant 30 minutes, ouvrez une issue et dites où il s'est arrêté.
- **Écran noir à la fin :** si la TV reçoit toujours un signal, l'installation est très probablement finie et EmuFive démarre. Si le bouton d'alimentation de la PS4 l'éteint normalement, EmuFive tourne et seule l'image est noire : voir [Écran noir après le menu](#black-screen-after-the-menu-or-the-emufive-logo).

<a id="emufive-doesnt-start-after-a-stopped-install"></a>
## EmuFive ne démarre pas après une installation interrompue

Si la PS4 a été éteinte pendant une installation, le disque à moitié créé peut rester. L'écran d'erreur indique **« The EmuFive disk is incomplete »**, ou le journal indique `is a hole`.

1. Supprimez `/user/home/ps5-ps4.img` par FTP. Gardez `ps5-ps4-rootfs.tar.xz`.
2. Lancez le payload et réinstallez. Laissez-le finir sans éteindre la PS4.

<a id="it-only-works-with-the-usb-drive-plugged-in"></a>
## Ça ne marche qu'avec le disque USB branché

Vous avez choisi **Install to USB drive** : EmuFive est sur ce disque et en a besoin. Pour l'avoir sur la PS4 : débranchez le disque, lancez le payload et choisissez **Install to PS4**.

<a id="games-dont-show-up"></a>
## Les jeux n'apparaissent pas

Un jeu est un **dossier** contenant `eboot.bin` et `sce_sys`, ou un seul fichier `.zar`. Les fichiers `.pkg` et fpkg ne peuvent pas être utilisés : extrayez d'abord le jeu. Utilisez des dumps de jeux que vous possédez.

Sur un disque USB, cela doit ressembler à ceci :

```
Disque USB (exFAT, une partition ; NTFS marche aussi)
└── PS5/                      <- exactement "PS5", en majuscules, à la racine du disque
    ├── PPSA01234/            <- un dossier par jeu (n'importe quel nom)
    │   ├── eboot.bin         <- directement dans le dossier du jeu
    │   ├── sce_sys/
    │   │   └── param.json    <- donne le nom et l'image du jeu
    │   └── ...
    └── MonJeu.zar            <- un dump .zar, en un seul fichier
```

Erreurs fréquentes :

- `ps5/` ou `Ps5/` : le nom doit être exactement `PS5`.
- `Jeux/PS5/...` : le dossier `PS5` doit être à la racine du disque.
- `PS5/PPSA01234/PPSA01234/eboot.bin` : un niveau de dossier en trop (fréquent après une décompression). Remontez le dossier intérieur.
- `PS5/eboot.bin` : les fichiers du jeu en vrac dans `PS5`, sans leur propre dossier.
- Deux jeux dans un même dossier : un seul apparaît. Le nom sur la tuile vient de `sce_sys/param.json`, pas du nom du dossier : donnez à chaque jeu son propre dossier.

Sur le disque de la PS4, le dossier est `/user/home/PS5`, et il ne marche que si EmuFive est installé sur la PS4 (pas sur un disque USB). Copiez les jeux avec le FTP de GoldHEN depuis le système de la PS4, puis démarrez EmuFive : il lit ce dossier au démarrage.

Ne gardez que le disque des jeux branché. Débranchez la clé de journaux `PS4BOOT` pendant que vous jouez.

<a id="an-external-drive-isnt-found"></a>
## Un disque externe n'est pas trouvé

- Les SSD et disques durs externes marchent depuis EmuFive 1.0.5. Mettez d'abord à jour.
- Un disque qui a déjà contenu Linux peut ne pas apparaître même après un formatage normal. Supprimez toutes ses partitions (Windows : Gestion des disques), puis créez une seule partition **exFAT**.
- Si EmuFive est installé sur un disque USB, les jeux vont sur un deuxième disque USB (depuis EmuFive 1.0.4).

<a id="the-controller-doesnt-work"></a>
## La manette ne marche pas

- **Dans le menu PS4 Multiboot et sur les écrans d'installation et d'erreur**, la manette ne marche qu'**avec un câble USB**. Le Bluetooth démarre plus tard, dans EmuFive.
- **En Bluetooth**, il faut l'appairer une fois avec EmuFive, car l'appairage du système PS4 n'est pas repris. Débranchez le câble, maintenez **SHARE + PS** jusqu'à ce que la barre lumineuse clignote deux fois, et attendez quelques secondes. Si elle ne se connecte pas, utilisez Paramètres → Manettes → Associer une nouvelle manette.
- Utilisez un câble qui transmet les données. Certains câbles ne font que charger.
- Sur les consoles **Baikal** (beaucoup de Pro CUH-71xx/72xx et de Slim récentes ; voir Paramètres → Système → Informations système), l'USB demande PS4 Multiboot v1.5.0-beta.7 ou plus récente.

<a id="a-game-closes-freezes-or-runs-slowly"></a>
## Un jeu se ferme, se fige ou est lent

- **« Le jeu s'est arrêté (code d'erreur 65) » avec `ErrorDeviceLost` :** le GPU de la PS4 a bloqué sur le rendu du jeu. C'est fréquent avec les gros jeux Unreal Engine, qui ne sont pas encore jouables. Envoyez le [journal du jeu](#game-logs) si vous voulez qu'on regarde.
- **Mémoire insuffisante :** un jeu PS5 peut utiliser jusqu'à environ 12,5 Go, et Linux sur la PS4 en a environ 6. EmuFive ferme le jeu avant que la PS4 se fige. Désactivez Paramètres → Jeux → **Mémoire de jeu partagée avec le GPU** et réessayez. EmuFive ne crée un fichier d'échange de 4 Go que si son disque a 8 Go libres : faites de la place si le disque est plein.
- **Un jeu se fige ou plante :** essayez une fois avec la **mémoire de jeu partagée avec le GPU** désactivée. Elle accélère les gros jeux 3D, mais ne convient pas à tous (Minecraft se fige avec).
- **Saccades la première fois :** la première fois qu'une scène s'affiche, les shaders sont compilés. La deuxième fois est plus fluide.
- **Déchirement de l'image :** Paramètres → Jeux → Cadence d'images → **Fluide (sans déchirure)**.
- **FPS faibles :** le processeur et le GPU de la PS4 sont bien plus lents que ceux de la PS5. Les jeux 2D et légers tournent bien ; les gros jeux 3D chargent souvent et affichent leurs menus, puis tournent très lentement ou restent noirs en jeu. Une PS4 Pro est environ deux fois plus rapide qu'une Slim. Consultez le tableau des [Jeux](README.fr.md#games) avant d'essayer un gros jeu.

<a id="how-to-save-the-logs"></a>
## Enregistrer les journaux

<a id="the-ps4boot-stick-boot-problems"></a>
### La clé PS4BOOT (problèmes de démarrage)

1. Formatez une clé USB en **FAT32** avec le nom de volume **`PS4BOOT`** (en majuscules). Windows ne sait pas formater en FAT32 une clé de plus de 32 Go : prenez une clé plus petite, ou [Rufus](https://rufus.ie) (Type de démarrage : *Non amorçable*, Système de fichiers : *Large FAT32*, Nom de volume : `PS4BOOT`). NTFS et exFAT ne marchent pas pour cela.
2. Branchez-la sur la PS4 **avant** de lancer le payload, et laissez-la.
3. Lancez le payload et attendez **5 minutes**, même si l'écran reste noir. Si un écran d'erreur apparaît, il enregistre lui-même les détails sur la clé.
4. Maintenez le bouton d'alimentation pour éteindre la PS4. Branchez la clé sur un PC et joignez les fichiers `.log` à votre issue (`ps4-linux-boot.log`, `ps4-linux-late.log`, `ps4-linux-error.log` ou `ps4-linux-rescue.log`).

Si la clé reste vide, dites-le : cela veut dire que Linux n'est pas allé jusque-là, et cela aide aussi.

<a id="game-logs"></a>
### Journaux des jeux

Juste après l'arrêt du jeu, allez dans Paramètres → Système → **Copier les journaux sur la clé USB**, puis joignez les fichiers du dossier `PS5-logs` de la clé USB (`kytyps5.log` est le principal). Joignez le vrai fichier, pas un résumé.

<a id="what-to-send"></a>
## Quoi envoyer

- Le modèle de PS4 (CUH-xxxx, sur l'étiquette à l'arrière), le firmware et le southbridge (Paramètres → Système → Informations système, par ex. Belize, Baikal, Aeolia).
- La version de PS4 Multiboot et le fichier payload que vous lancez.
- Votre ligne `bootargs.txt`.
- Votre version d'EmuFive (Paramètres → Système), et s'il est installé sur la PS4 ou sur un disque USB.
- Le modèle de votre TV ou moniteur, et ce qu'il affiche : « Aucun signal », ou allumé mais noir.
- Le voyant de la PS4 : blanc, bleu, violet ou éteint.
- Les journaux ci-dessus.
