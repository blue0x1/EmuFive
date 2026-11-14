<h1 align="center"><img src="assets/emufive-logo.png" alt="EmuFive" width="480"></h1>

<p align="center">
  <img src="https://img.shields.io/badge/platform-PS4-003791?logo=playstation&logoColor=white" alt="Platform: PS4">
  <img src="https://img.shields.io/badge/status-experimental-red" alt="Status: experimental">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--2.0-blue" alt="License: GPL-2.0"></a>
</p>

<p align="center">
  <a href="README.md">EN</a> · <a href="README.ar.md">AR</a> · <a href="README.zh-CN.md">ZH</a> · <a href="README.fr.md">FR</a> · <b>ES</b> · <a href="README.de.md">DE</a> · <a href="README.it.md">IT</a> · <a href="README.pt-BR.md">PT</a> · <a href="README.tr.md">TR</a>
</p>

Un emulador de PS5 para PS4.

Creado por **[Chokri Hammedi (blue0x1)](https://github.com/blue0x1)**. Basado en [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot).

> **Estado: investigación experimental.** En una PS4 Pro, "Sons of Sparta" funciona a unos 40 FPS o más. KytyPS5 reescribe las instrucciones de CPU exclusivas de PS5 en el código de los juegos (parche `0004`). Otros juegos aún se están probando, y muchos son lentos por ahora. Consulta [El problema de la CPU](#the-cpu-problem).

<p align="center"><img src="assets/home-screen.png" alt="La pantalla de inicio de EmuFive en una PS4 Pro, con God of War Sons of Sparta seleccionado" width="900"></p>

<p align="center">
  <b><a href="#installing">Instalación</a></b> · <b><a href="#games">Juegos</a></b> · <b><a href="#changelog">Registro de cambios</a></b> · <a href="#how-it-works">Cómo funciona</a> · <a href="#the-cpu-problem">El problema de la CPU</a> · <a href="#plan">Plan</a> · <a href="#building">Compilación</a> · <a href="#credits">Créditos</a>
</p>

<a id="how-it-works"></a>
## Cómo funciona

- **[PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot)** arranca Linux en la PS4 e instala sistemas Linux en su disco interno, con el mando.
- **PS4 Mesa**, parte de PS4 Multiboot, da Vulkan 1.3 a la GPU de la PS4 (Liverpool en la PS4 y la Slim, Gladius en la Pro). KytyPS5 necesita recursos dispersos (sparse resources), que RADV ofrece en esta GPU con `RADV_EXPERIMENTAL=sparse`.
- **KytyPS5**, el proyecto original en un commit fijado con los parches de este proyecto (`patches/kytyps5/`), compilado con `-march=btver2` para la CPU AMD Jaguar de la PS4. La versión oficial usa AVX2 y se detiene en la PS4 con "Illegal instruction".
  - `0001`: la opción de compilación `KYTY_HOST_ARCH` (la CPU para la que se compila el emulador).
  - `0002`: una biblioteca C para homebrew. El homebrew de PS5 hecho con ps5-native-app-boilerplate incluye un módulo sustituto `sce_module/libc.prx` cuyas funciones devuelven todas 0 (la consola usa su propia biblioteca C), así que su `malloc` fallaba en KytyPS5. El parche añade las funciones de la biblioteca C que importa ese homebrew y solo las usa para un módulo sustituto así.
  - `0003`: más para homebrew: archivos y carpetas, llamadas al sistema, el usuario en primer plano y puntos de montaje adicionales (`KYTY_MOUNTS`).
  - `0004`: código de PS5 en la CPU de la PS4. Cada instrucción AVX2, FMA y BMI2 se reescribe como código SSE4.2/AVX/BMI1 al cargar un módulo; la que no se puede reescribir en ese momento se reemplaza la primera vez que se ejecuta. Consulta [El problema de la CPU](#the-cpu-problem).
- **EmuFive** lo reúne todo en un pequeño sistema Linux que arranca directamente en el emulador, a pantalla completa, sin escritorio. Se instala con PS4 Multiboot como cualquier otro sistema.

<a id="the-cpu-problem"></a>

## El problema de la CPU

KytyPS5 no emula la CPU de la PS5: ejecuta directamente el código x86-64 del juego. Los juegos de PS5 están compilados para la CPU Zen 2 de la PS5 y usan instrucciones AVX2, BMI2 y FMA por todas partes. La CPU Jaguar de la PS4 no tiene ninguna, así que el código del juego se detiene en la primera de esas instrucciones.

El parche `0004` añade eso al parcheador de instrucciones invitadas de KytyPS5. Cuando a la CPU anfitriona le falta AVX2, FMA o BMI2, cada una de esas instrucciones se reemplaza por código con el mismo efecto: operaciones enteras de 256 bits como dos mitades de 128 bits, permutaciones entre mitades con movimientos y mezclas AVX, desplazamientos por elemento de uno en uno, FMA calculada en doble precisión, gathers de un elemento en uno, BMI2 con registros guardados. El salto al reemplazo se escribe donde estaba la instrucción; una instrucción demasiado corta para un salto, en un lugar que el parcheador no puede reorganizar, produce un fallo y se reemplaza en tiempo de ejecución.

`tools/jaguar-test/` comprueba cada reemplazo en un PC que tiene estas instrucciones: toma cada forma de instrucción encontrada en el código de un programa, ejecuta el original y el reemplazo desde el mismo estado aleatorio, y compara todos los registros, los indicadores y la memoria. Las formas encontradas en los programas probados hasta ahora coinciden: 287 en God of War Sons of Sparta (gathers y VFMADDSUB incluidos) y 227 en los programas probados antes. Las excepciones son raras diferencias en el último bit en FMA (la precisión simple se redondea dos veces, la doble es una multiplicación y una suma) y un caso límite de NaN para 0 por infinito.

La Jaguar sigue siendo mucho más lenta que la CPU de la PS5, y los reemplazos suman a eso, así que incluso un juego que funciona puede ir lento.

<a id="plan"></a>
## Plan

| Paso | Estado |
|---|---|
| Vulkan en la GPU de la PS4 cumple los requisitos de KytyPS5 | Hecho (`RADV_EXPERIMENTAL=sparse`) |
| KytyPS5 compilado para la CPU de la PS4 | Hecho (`KYTY_HOST_ARCH=btver2`) |
| KytyPS5 arranca en la PS4 e inicializa la GPU | Hecho, PS4 Pro |
| Imagen del sistema EmuFive, se instala con PS4 Multiboot | Hecho, PS4 Pro |
| Una app homebrew de PS5 sin AVX2 funciona y dibuja | Hecho: Snes9x PS5 2.11 recompilado para btver2, PS4 Pro |
| Mando, almacenamiento `/data` y USB, cargar un juego en esa app | Hecho en una versión de prueba para PC (mismos parches); PS4 después |
| Traducción de AVX2, BMI2 y FMA para el código de juegos | Hecho (`0004`), comprobado en un PC |
| Un juego de PS5 funciona en la PS4 | Hecho: God of War Sons of Sparta, unos 40 FPS o más, PS4 Pro |
| Hollow Knight: Silksong funciona en la PS4 | Hecho desde la 1.0.1 (parches `0006` y `0007`), PS4 Pro |
| Pantalla de inicio: elegir un juego con el mando; Wi-Fi; Ajustes | Hecho, comprobado en un PC |
| Juegos desde la unidad USB, el disco de la PS4 o una carpeta compartida de un PC | Hecho, comprobado en un PC; PS4 después |

<a id="building"></a>

## Compilación

Necesita Docker, git y el PS4 Mesa de PS4 Multiboot (`../PS4-Multiboot/out/ps4-mesa.tar.xz`, compilado allí con `make mesa`). `build-kyty.sh` clona KytyPS5 en `build/kytyps5` la primera vez, y en cada compilación lo devuelve al commit fijado y aplica los parches.

```bash
scripts/build-kyty.sh      # out/kytyps5-ps4.tar.xz
scripts/build-rootfs.sh    # out/ps5-ps4-rootfs.tar.xz
```

`PS4_MESA` y `KYTY` indican a `build-rootfs.sh` otras rutas.

<a id="installing"></a>

## Instalación

EmuFive se instala con [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot), como cualquier otro sistema Linux.

Necesitas:

- Una PS4 con jailbreak y **GoldHEN** (por su servidor FTP y su cargador de payloads).
- Un PC en la misma red con un cliente FTP (por ejemplo FileZilla).
- Unos 28 GB libres en la PS4 (un disco de 16 GB, y 10 GB siempre libres para la PS4), o una unidad USB de 8 GB o más.
- Un DualShock 4 (con un cable USB, o emparejado por Bluetooth más tarde).

Pasos:

1. Desde las [versiones de PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot/releases), descarga `bzImage`, `initramfs.cpio.gz`, `bootargs.txt` y `linux-2048mb.bin`. (`ps4-mesa.tar.xz` no hace falta: EmuFive ya incluye PS4 Mesa.)
2. Desde las [versiones de EmuFive](https://github.com/blue0x1/EmuFive/releases), descarga `ps5-ps4-rootfs.tar.xz` (o compílalo, consulta [Compilación](#building)). No le cambies el nombre: PS4 Multiboot encuentra los sistemas por el `-ps4-rootfs` que contiene.
3. Activa el servidor FTP de GoldHEN y copia los archivos a la PS4 (puerto 2121):

   | Archivo | Carpeta en la PS4 |
   |---|---|
   | `bzImage`, `initramfs.cpio.gz`, `bootargs.txt` | `/data/linux/boot/` |
   | `ps5-ps4-rootfs.tar.xz` | `/user/home/` |
   | `linux-2048mb.bin` | `/data/payloads/` |

4. Ejecuta `linux-2048mb.bin` desde el menú de payloads de GoldHEN.

   > **Ten paciencia:** después de iniciar el payload, la TV puede mostrar **"No signal" o una pantalla negra durante 1 o 2 minutos** mientras arranca Linux. Es normal.

5. En el menú de PS4 Multiboot, elige **EmuFive** y luego **Install to PS4** o **Install to USB drive**. Tarda unos minutos.
6. Pon tus juegos en uno de los lugares de abajo. Un juego es una carpeta con `eboot.bin` (y `sce_sys`), o un volcado ZArchive (`.zar`).

Después, ejecuta el payload para iniciar EmuFive: si solo está instalado EmuFive, arranca directamente; si hay otros sistemas, aparece primero el menú de PS4 Multiboot. Apaga o reinicia desde la pantalla de inicio para volver al sistema de la PS4. Para instalar EmuFive de nuevo, borra `/user/home/ps5-ps4.img` por FTP y ejecuta el payload.

Las actualizaciones vienen de las versiones de EmuFive: Ajustes, Sistema, Actualización de software (sin reinstalar).

El sistema arranca en la pantalla de inicio y no necesita teclado:

- Los juegos aparecen como mosaicos, cada uno con el lugar donde está: **USB**, **PS4** o **PC**. Elige uno y pulsa Jugar; al salir del juego, vuelve la pantalla de inicio.
- Arriba: el Wi-Fi (con un teclado en pantalla para la contraseña) y Ajustes, y dos pestañas, **Juegos** y **Multimedia** (L1 / R1). Multimedia muestra tus capturas de pantalla; abre una, y Cuadrado la borra.
- OPTIONS sobre un juego: favorito, ocultar, sus propios ajustes, sus trofeos y cuánto tiempo lo has jugado.
- **Internet**, el mosaico después de los juegos: un navegador web que se usa con el mando. El stick izquierdo (o el panel táctil) mueve el puntero y X hace clic; el stick derecho desplaza la página; O o L1 vuelve atrás, R1 adelante; L2 y R2 hacen zoom. Triángulo escribe una dirección o una búsqueda, y elegir un cuadro de texto en una página abre el teclado en pantalla. OPTIONS abre el menú: marcadores, página de inicio, zoom, buscador (Google, DuckDuckGo o Bing), sitios móviles (páginas más ligeras) y borrar el historial y las cookies. El botón PS vuelve a la pantalla de inicio, y la misma página se abre la próxima vez. Es WebKitGTK mostrando una página cada vez, unos 450 MB de memoria con una página de texto y más con sitios de vídeo; la pantalla de inicio se cierra mientras funciona, y un juego en pausa debe cerrarse antes. Las descargas, las subidas, la cámara, el micrófono y la ubicación se rechazan. Los marcadores están en `~/.config/ps5-on-ps4/browser.json`, las cookies en `~/.local/share/ps5-browser`.
- El botón PS durante un juego lo pausa y abre el menú rápido: Reanudar, **Inicio** (la pantalla de inicio, con el juego aún en pausa: PS o Reanudar vuelve a él; iniciar otro juego pregunta primero y luego lo cierra), cerrar el juego, volumen, energía.
- Capturas de pantalla: PS + Cuadrado, o Share, también dentro de un juego. Se guardan en `PS5-screenshots` en la unidad USB (o en `~/Screenshots` si no hay ninguna), con un pequeño aviso en la esquina. Para pasar una al móvil, ábrela en Multimedia y pulsa Triángulo (Compartir): escanea el código QR con el móvil (en la misma red) para abrirla allí, y luego guárdala o compártela. La PS4 sirve solo esa imagen, en una dirección aleatoria, y solo mientras el código está en pantalla. Los códigos QR vienen de `python3-segno`.
- Ajustes, Apariencia: color de acento, tema (oscuro, medianoche, claro), fondo (la imagen del juego, un degradado, un color sólido o tu propia imagen desde la unidad USB), atenuación del fondo, orbes flotantes, animaciones, tamaño y forma de los mosaicos, tamaño y fuente del texto, reloj, lo que muestra la barra superior (la batería es la del mando), sonidos del menú, vibración, ayudas de botones, bordes de la pantalla (overscan) y salvapantallas.
- Ajustes, Mandos: color y brillo de la barra de luz, vibración activada o no y su intensidad, el micrófono del mando activado o no (con el mando en un cable USB; Linux no tiene sonido del mando por Bluetooth), intercambiar X y O, y una página de prueba para cada botón y stick. Ajustes, Juegos: valores por defecto para todos los juegos, idioma de los juegos, HDR y ritmo de fotogramas. Ajustes, Fecha y hora: automática desde internet (por defecto) o a mano. Ajustes, Sistema: el idioma del menú (inglés, árabe, francés, turco, español, alemán, italiano o portugués de Brasil), temperatura y carga de la CPU, copia de seguridad de los ajustes en la unidad USB, o restablecerlos todos.
- Perfiles (Ajustes, Perfil, y Cambiar de perfil en el menú rápido): hasta 8, cada uno con su nombre, avatar, partidas guardadas, trofeos y tiempo de juego. Con más de uno, al arrancar se abre "¿Quién juega?". Cada perfil tiene su propia carpeta de KytyPS5 (`~/.kytyps5/users/<ID>`, el primer perfil conserva `~/.kytyps5`), con la caché de shaders compartida.
- Avisos en la esquina superior izquierda, también dentro de un juego: se guardó una captura, se conectó un mando (con su conexión y su nivel de batería), la batería del mando está baja (15 %). La batería de la barra superior es verde, amarilla o roja según el nivel, con un rayo mientras se carga.
- Falta de memoria: un archivo swap de 4 GB en el disco del sistema (`ps5-swap.service`, creado una vez cuando hay espacio) permite que un juego grande vaya más lento en vez de congelar la PS4, y si aun así se agotan la memoria y el swap, el juego se cierra antes de que la PS4 se congele y la pantalla de inicio explica por qué.
- Idiomas del menú: las traducciones están en `lib/ps5/translations.json`, una entrada por texto en inglés. El árabe se alinea a la derecha y se dibuja con DejaVu Sans; sus letras se unen en `lib/ps5/i18n.py`, ya que SDL_ttf aquí no las une.
- El programa ve la unidad USB como `/mnt/usb0` y una carpeta del sistema (`~/data`, que se conserva entre arranques) como `/data`. Para Snes9x PS5, las ROMs van en `snes9x/roms` en la unidad USB o en `~/data/snes9x/roms`.
- Si el emulador se detiene con un error, la pantalla de inicio muestra el motivo.
- `PS5_GAME` en `/etc/ps5-on-ps4.conf` ejecuta un juego directamente en lugar de la pantalla de inicio.
- Mandos: un DualShock 4 con cable, o por Bluetooth después de mantener SHARE + PS hasta que la barra de luz parpadee dos veces.
- El sonido va a la TV por HDMI, también cuando un mando con cable trae su propia tarjeta de sonido (`/etc/wireplumber/wireplumber.conf.d/51-ps5-hdmi.conf`).

### Dónde pueden estar los juegos

- **Unidad USB:** la carpeta `PS5` en la raíz de la unidad. exFAT es lo mejor (archivos de más de 4 GB); NTFS también funciona.
- **Disco de la PS4:** `/user/home/PS5` en la PS4, copiado ahí con el FTP de GoldHEN. El sistema lee el disco de la PS4 en solo lectura y nunca lo modifica. No disponible si el propio sistema está instalado en una unidad USB.
- **Un PC:** una carpeta compartida en Windows o Linux. En Ajustes, activa **Usar juegos del PC** e indica la dirección del PC, la carpeta compartida y, salvo que sea un recurso para invitados, un usuario y una contraseña; luego Conectar. Los juegos pueden estar en la raíz de la carpeta compartida o en una carpeta `PS5` dentro de ella. Un cable de red es más rápido que el Wi-Fi.
  - Windows: comparte la carpeta (Propiedades, Compartir). Para un recurso de invitados, compártela con Everyone y desactiva *Password protected sharing* en la configuración de uso compartido avanzado.
  - Linux (Samba): un recurso con `guest ok = yes` para invitados, o un usuario de Samba (`smbpasswd -a`).
  - El kernel de la PS4 no tiene cliente SMB, así que el sistema usa smbnetfs (FUSE). Los ajustes, contraseña incluida, se guardan en `~/.config/ps5-on-ps4/pc-share.json`, que solo puede leer el usuario `ps5`.

`tools/make-pad-test-rom.py` crea una pequeña ROM de SNES para probar un mando: azul, y verde mientras se mantiene un botón.

Inicio de sesión: `ps5` / `ps5` en tty2 o por SSH. La salida del emulador está en `~/kytyps5.log` (la ejecución anterior: `~/kytyps5.log.1`).

<a id="games"></a>
## Juegos

Este proyecto no contiene software de sistema de PS5 ni juegos. Usa solo juegos que tengas y que hayas volcado tú mismo.

Juegos probados:

| Juego | Consola | Resultado |
|---|---|---|
| God of War Sons of Sparta | PS4 Pro | Jugable, unos 40 FPS o más |
| Hollow Knight: Silksong | PS4 Pro | Jugable, de 50 a 60 FPS |
| Plants vs. Zombies: Replanted | PS4 Pro | Jugable, 60 FPS fijos |
| Vampire Survivors | PS4 Slim | Jugable, 60 FPS estables |
| Spider-Man 2 | | Aún no probado |

¿Probaste un juego? Abre un [issue](https://github.com/blue0x1/EmuFive/issues) con el juego, el modelo de tu consola y cómo funcionó.

<a id="changelog"></a>
## Registro de cambios

### 1.0.6 (2026-11-14)

- Mejorado: la pantalla de inicio usa mucha menos CPU mientras nadie la usa (en 4K, un tercio de un núcleo; antes, un núcleo entero), así que la PS4 se calienta menos y hace menos ruido.

Para actualizar desde la 1.0.3 o anteriores, inicia la actualización una vez a mano, porque la actualización de software antigua no puede: activa SSH en Ajustes, conéctate con `ssh ps5@<dirección de la PS4>` (contraseña `ps5` si no la cambiaste) y ejecuta

```bash
sudo systemd-run --unit=emufive-update --collect /opt/ps5-on-ps4/bin/ps5-update install
```

Instala todas las actualizaciones que faltan (desde la 1.0.0 o la 1.0.1 eso incluye los paquetes del navegador de la 1.0.2, unos 110 MB); después reinicia desde la pantalla de inicio. Desde la 1.0.4, la actualización de software en Ajustes funciona. Las instalaciones nuevas usan el `ps5-ps4-rootfs.tar.xz` de la versión 1.0.6.

## Estructura del proyecto

| Ruta | Contenido |
|---|---|
| `scripts/build-kyty.sh` | Compila KytyPS5 (el original más `patches/kytyps5/`) para la CPU de la PS4 |
| `patches/kytyps5/` | Los cambios de este proyecto a KytyPS5 |
| `scripts/build-rootfs.sh` | Construye la imagen del sistema para PS4 Multiboot |
| `scripts/make-release.sh` | Crea el paquete de actualización de una versión (lo instala Ajustes, Sistema, Actualización de software) |
| `scripts/updates/` | Scripts que una actualización ejecuta en la PS4 cuando sus archivos ya están copiados (`--post`) |
| `docker/` | Entornos de compilación para ambos |
| `overlay/` | Archivos añadidos al sistema: sesión, pantalla de inicio, ajustes, montaje de la unidad USB y del disco de la PS4, emparejamiento de mandos |
| `tools/` | Conversor del logo, ROM de prueba del mando, `extract-code.py` (el código de un SELF/ELF de PS5) |
| `tools/jaguar-test/` | Comprueba los reemplazos del parche `0004` contra las instrucciones reales |

## Agradecimientos especiales

- [KytyPS5](https://github.com/KytyPS5/KytyPS5), el emulador de PS5 en el que se basa EmuFive (GPL-2.0)
- [Kyty](https://github.com/InoriRus/Kyty) de InoriRus, el emulador en el que se basa KytyPS5

<a id="credits"></a>
## Créditos

- [Mesa](https://mesa3d.org), y los parches de GPU de PS4 de fail0verflow, DionKill y striker91n
- Los desarrolladores del kernel Linux para PS4 ([sony-jaguar-devs/ps4-linux](https://github.com/sony-jaguar-devs/ps4-linux))

## Licencia

Copyright (C) 2026 [Chokri Hammedi (blue0x1)](https://github.com/blue0x1).

GPL-2.0 (consulta `LICENSE`). KytyPS5, Mesa y el kernel Linux tienen sus propias licencias. PlayStation es una marca de Sony Interactive Entertainment; este proyecto no está afiliado a Sony.
