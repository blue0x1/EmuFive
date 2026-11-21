<h1 align="center"><img src="assets/emufive-logo.png" alt="EmuFive" width="480"></h1>

<p align="center">
  <img src="https://img.shields.io/badge/platform-PS4-003791?logo=playstation&logoColor=white" alt="Platform: PS4">
  <img src="https://img.shields.io/badge/status-experimental-red" alt="Status: experimental">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--2.0-blue" alt="License: GPL-2.0"></a>
  <a href="https://github.com/blue0x1/EmuFive/releases"><img src="https://img.shields.io/github/downloads/blue0x1/EmuFive/total?label=downloads" alt="Downloads"></a>
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

   > **¿Pantalla negra después del menú de PS4 Multiboot?** Algunas TV prefieren un modo que la PS4 no puede enviar. Añade `emufive.mode=1920x1080@60` a la línea de `/data/linux/boot/bootargs.txt` (deja también `video=HDMI-A-1:1920x1080@60D`) y vuelve a ejecutar el payload.

5. En el menú de PS4 Multiboot, elige **EmuFive** y luego **Install to PS4** o **Install to USB drive**. Tarda unos minutos.
6. Pon tus juegos en uno de los lugares de abajo. Un juego es una carpeta con `eboot.bin` (y `sce_sys`), o un volcado ZArchive (`.zar`). Los archivos de paquete (`.pkg`, fpkg) no se pueden instalar ni ejecutar: primero extrae el juego.

Después, ejecuta el payload para iniciar EmuFive (con otros sistemas instalados, primero aparece el menú de PS4 Multiboot). Para reinstalar, borra `/user/home/ps5-ps4.img` por FTP y ejecuta el payload. Actualizaciones: Ajustes, Sistema, Actualización de software.

### Uso

- **Pantalla de inicio:** tus juegos como mosaicos. Elige uno y pulsa Jugar. OPTIONS sobre un juego: favorito, ocultar, sus ajustes, trofeos, tiempo de juego e información del juego.
- **Botón PS en un juego:** menú de pausa (Reanudar, Inicio, Cerrar el juego, volumen, apagado).
- **Capturas:** PS + Cuadrado, o Share. Míralas en Multimedia; Triángulo muestra un código QR para abrir una en el móvil.
- **Clips de vídeo:** PS + Triángulo empieza a grabar, y PS + Triángulo otra vez lo detiene (hasta 60 minutos). Los clips se reproducen en Multimedia y se comparten al móvil como las capturas. Dónde se guardan (la PS4 o una unidad USB) y su calidad (720p o 1080p) están en Ajustes > Almacenamiento.
- **Internet:** un mosaico de navegador web, usado con el mando.
- **Ajustes:** Wi-Fi, apariencia, mandos, perfiles (hasta 8), idioma del menú, fecha y hora, copia de seguridad.
- **Mandos:** un DualShock 4 con cable, o por Bluetooth (mantén SHARE + PS hasta que la barra de luz parpadee dos veces).
- **Inicio de sesión:** `ps5` / `ps5` por SSH o en tty2. El registro del emulador es `~/kytyps5.log`.

### Dónde pueden estar los juegos

- **Unidad USB:** la carpeta `PS5` en la raíz de la unidad (exFAT es lo mejor; NTFS también sirve).
- **Disco de la PS4:** `/user/home/PS5`, copiado con el FTP de GoldHEN (no si EmuFive está instalado en una unidad USB).
- **Un PC:** una carpeta compartida en Windows o Linux. En Ajustes, activa **Usar juegos del PC**, pon la dirección, la carpeta compartida y el usuario, y luego Conectar.

## Juegos

Este proyecto no contiene software de sistema de PS5 ni juegos. Usa solo juegos que tengas y que hayas volcado tú mismo.

<details>
<summary><b>Juegos que funcionan</b></summary>

| Juego | Consola | EmuFive | Resultado |
|---|---|---|---|
| God of War Sons of Sparta | PS4 Pro | 1.0.0 | Jugable, unos 40 FPS o más |
| Hollow Knight: Silksong | PS4 Pro | 1.0.1 | Jugable, 60 FPS |
| Plants vs. Zombies: Replanted | PS4 Pro | 1.0.4 | Jugable, 60 FPS fijos |
| Vampire Survivors | PS4 Slim | 1.0.4 | Jugable, 60 FPS estables |
| My Little Puppy | PS4 Slim | 1.0.6 | Funciona, 3–15 FPS (20–25 en zonas vacías) |
| DREDGE | PS4 Pro | 1.0.8 | Jugable |
| Animal Well | PS4 Pro | 1.0.9 | Jugable, 42–44 FPS |
| Teardown | PS4 Pro | 1.0.9 | Funciona, 9–12 FPS en el juego (unos 20 en escenas ligeras) con memoria compartida con la GPU |
| Invincible VS | PS4 Pro | 1.0.9 | Arranca, 4–5 FPS; aún no es jugable |
| Blue Prince | PS4 Pro | 1.0.10 | Jugable, unos 25 FPS |
| Wytchwood | PS4 Pro | 1.0.10 | Jugable, 30 FPS estables |
| Hades II | PS4 Slim | 1.0.10 | Funciona, 20–25 FPS en el juego (10–15 en los menús), con tirones |
| Minecraft | PS4 Slim | 1.0.10 | Jugable, 30–35 FPS en el juego (56–60 en los menús) con la memoria compartida con la GPU desactivada |
| Crusader Kings III | PS4 Pro | 1.0.10 | Jugable |
| Iron Lung | PS4 Pro | 1.0.12 | Jugable, 60 FPS |
| The King is Watching | PS4 Pro | 1.0.12 | Jugable, 55–60 FPS |
| Wizard with a Gun | PS4 Pro | 1.0.12 | Funciona, 20–30 FPS con tirones; el brillo de un portal se queda en pantalla |
| Another Crab's Treasure | PS4 Pro | 1.0.12 | Funciona, 4–10 FPS; quedan artefactos gráficos en pantalla |
| Minecraft Dungeons 2 | PS4 Slim | 1.0.12 | Funciona con internet desconectado, 20–30 FPS |

</details>

<details>
<summary><b>Juegos que aún no funcionan (una versión más nueva puede arreglarlos)</b></summary>

| Juego | Consola | EmuFive | Resultado |
|---|---|---|---|
| DRAGON BALL: Sparking! ZERO | PS4 Pro | 1.0.10 | Muestra el EULA y las pantallas en línea, y luego la GPU se detiene |
| Hello Neighbor | PS4 Pro | 1.0.4 | Se detiene al arrancar (mesh shaders) |
| Need for Speed Unbound | PS4 Slim | 1.0.6 | Se cierra al arrancar (copia de profundidad no soportada) |
| V Rising | PS4 Pro | 1.0.8 | Se cierra al arrancar |
| Serious Sam 4 | PS4 Slim | 1.0.10 | Se cierra al arrancar (servicios en línea) |
| Serious Sam: Siberian Mayhem | PS4 Slim | 1.0.9 | Se cierra al arrancar (servicios en línea) |
| The Long Dark | PS4 Slim | 1.0.10 | Se queda en el vídeo de introducción, sin menú |

</details>

¿Probaste un juego? Abre un [issue](https://github.com/blue0x1/EmuFive/issues) con el juego, su ID de título, el modelo de tu consola, la versión de EmuFive y cómo funcionó. Los juegos que no funcionan también sirven (por ejemplo «no arranca» o «se cierra en el menú»): van a la tabla, para que otros no prueben el mismo juego.

<a id="changelog"></a>
## Registro de cambios

### 1.0.13 (2026-11-21)

- Nuevo: un gestor de trucos. Actívalo en Ajustes, Juegos, y aparece un mosaico Trucos en la pantalla de inicio. Descarga los trucos de PS5 de la [HEN Cheats Collection](https://github.com/TeeKay87/HEN-Cheats-Collection) y muestra tus juegos que tienen trucos para su versión; elige los que quieras y se aplican al iniciar el juego. El menú de un juego indica cuántos están activados.
- Corregido: bloques de cuadros en las páginas web de Internet (#61).
- Teclado: R1 es Mayús, L1 es Espacio, y Mayús dos veces es bloqueo de mayúsculas (#61).
- Los juegos `.zar` muestran su nombre, icono y fondo en la pantalla de inicio (#54).

Para actualizar desde la 1.0.3 o anteriores, inicia la actualización una vez a mano, porque la actualización de software antigua no puede: activa SSH en Ajustes, conéctate con `ssh ps5@<dirección de la PS4>` (contraseña `ps5` si no la cambiaste) y ejecuta

```bash
sudo systemd-run --unit=emufive-update --collect /opt/ps5-on-ps4/bin/ps5-update install
```

Instala todas las actualizaciones que faltan (desde la 1.0.0 o la 1.0.1 eso incluye los paquetes del navegador de la 1.0.2, unos 110 MB); después reinicia desde la pantalla de inicio. Desde la 1.0.4, la actualización de software en Ajustes funciona. Las instalaciones nuevas usan el `ps5-ps4-rootfs.tar.xz` de la versión 1.0.13.

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

## Apoya el proyecto

Si EmuFive te resulta útil, puedes apoyar el proyecto con Bitcoin:

BTC: `bc1q7w5ns9vsguseppllpy609yhwrtq3v56g94mjde`

## Licencia

Copyright (C) 2026 [Chokri Hammedi (blue0x1)](https://github.com/blue0x1).

GPL-2.0 (consulta `LICENSE`). KytyPS5, Mesa y el kernel Linux tienen sus propias licencias. PlayStation es una marca de Sony Interactive Entertainment; este proyecto no está afiliado a Sony.
