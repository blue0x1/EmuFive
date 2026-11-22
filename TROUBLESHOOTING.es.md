# Solución de problemas

<p align="center">
  <a href="TROUBLESHOOTING.md">EN</a> · <a href="TROUBLESHOOTING.ar.md">AR</a> · <a href="TROUBLESHOOTING.zh-CN.md">ZH</a> · <a href="TROUBLESHOOTING.fr.md">FR</a> · <b>ES</b> · <a href="TROUBLESHOOTING.de.md">DE</a> · <a href="TROUBLESHOOTING.it.md">IT</a> · <a href="TROUBLESHOOTING.pt-BR.md">PT</a> · <a href="TROUBLESHOOTING.tr.md">TR</a>
</p>

Los problemas que la gente contó en los [issues](https://github.com/blue0x1/EmuFive/issues), con las soluciones que les funcionaron. Prueba los pasos en orden. ¿Sigues atascado? Abre un issue con lo que pone en [Qué enviar](#what-to-send).

- [Revisa primero los archivos](#check-the-files-first)
- [Pantalla negra o «Sin señal» tras el payload](#black-screen-or-no-signal-after-the-payload)
- [Pantalla negra tras el menú o el logo de EmuFive](#black-screen-after-the-menu-or-the-emufive-logo)
- [Pantalla verde, colores mal o parpadeo](#green-screen-wrong-colors-or-flickering)
- [La PS4 se apaga, o la luz se queda blanca](#the-ps4-turns-off-or-the-light-stays-white)
- [«No Linux install or archive found»](#no-linux-install-or-archive-found)
- [La instalación tarda mucho](#installing-takes-very-long)
- [EmuFive no arranca tras una instalación interrumpida](#emufive-doesnt-start-after-a-stopped-install)
- [Solo funciona con la unidad USB conectada](#it-only-works-with-the-usb-drive-plugged-in)
- [Los juegos no aparecen](#games-dont-show-up)
- [No se encuentra un disco externo](#an-external-drive-isnt-found)
- [El mando no funciona](#the-controller-doesnt-work)
- [Un juego se cierra, se congela o va lento](#a-game-closes-freezes-or-runs-slowly)
- [Cómo guardar los registros](#how-to-save-the-logs)
- [Qué enviar](#what-to-send)

<a id="check-the-files-first"></a>
## Revisa primero los archivos

La mayoría de los «no pasa nada» venían de uno de estos puntos:

- **Misma versión:** `bzImage`, `initramfs.cpio.gz`, `bootargs.txt` y `linux-2048mb.bin` tienen que venir todos de la misma [versión de PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot/releases) (mejor la más nueva). Con archivos mezclados no arranca.
- **Carpetas en minúsculas:** la PS4 ve `LINUX` y `linux` como carpetas distintas. Las rutas deben ser exactamente `/data/linux/boot/bzImage`, `/data/linux/boot/initramfs.cpio.gz` y `/data/linux/boot/bootargs.txt`.
- **El nombre exacto del archivo:** `/user/home/ps5-ps4-rootfs.tar.xz`. A veces el navegador lo guarda como `ps5-ps4-rootfs (1).tar.xz`, y entonces el menú no lo encuentra.
- **Transferencia binaria:** en FileZilla, elige Transferencia → Tipo de transferencia → **Binario** antes de subir. Un archivo subido en modo texto queda dañado. Comprueba que cada archivo en la PS4 tiene el mismo tamaño que en la versión.
- **Nuestro payload:** usa `linux-2048mb.bin` de PS4 Multiboot (en el firmware 14.02: `linux-2048mb-14.02.bin`). Funciona del firmware 5.05 al 14.02. Otros payloads de Linux no están soportados.

<a id="black-screen-or-no-signal-after-the-payload"></a>
## Pantalla negra o «Sin señal» tras el payload

Después de lanzar el payload, la TV muestra «Sin señal» o una pantalla negra durante **1 a 2 minutos** mientras arranca Linux. Es normal. Que la pantalla y el mando se apaguen justo después del payload también es normal: el sistema de la PS4 se cierra y Linux toma el control.

**No pulses el botón PS mientras la pantalla está negra**: apaga la PS4. Con solo EmuFive en la PS4, el instalador empieza solo a los 60 segundos, así que puede que ya esté instalando.

Si no aparece nada tras 3 minutos:

1. Conecta la PS4 **directamente** a la TV, sin switch HDMI, receptor AV ni capturadora.
2. En la PS4, desactiva **Ajustes → Sistema → Activar HDCP** y vuelve a lanzar el payload.
3. Prueba otro cable HDMI y otro puerto HDMI.
4. Prueba una vez otra TV u otro monitor. Algunas TV no aceptan la señal de Linux de la PS4, y otra pantalla muestra si el problema es la TV.
5. ¿Nada todavía? Guarda el [registro PS4BOOT](#the-ps4boot-stick-boot-problems) y abre un issue. Dinos si la TV dice **«Sin señal»** o está encendida pero en negro.

<a id="black-screen-after-the-menu-or-the-emufive-logo"></a>
## Pantalla negra tras el menú o el logo de EmuFive

Si ves el menú de PS4 Multiboot o el logo de EmuFive y luego se pone negro, EmuFive cambió a un modo que tu TV prefiere pero que la PS4 no puede enviar.

1. Actualiza EmuFive (Ajustes → Sistema → Actualización de software).
2. Por FTP, abre `/data/linux/boot/bootargs.txt` y añade ` emufive.mode=1920x1080@60` al final de la línea. Deja también `video=HDMI-A-1:1920x1080@60D`. El archivo debe seguir siendo **una sola línea**.
3. Vuelve a lanzar el payload.

¿No puedes actualizar porque la pantalla está negra? Conecta una vez otra TV u otro monitor y actualiza, o instala EmuFive de nuevo con el `ps5-ps4-rootfs.tar.xz` más nuevo.

<a id="green-screen-wrong-colors-or-flickering"></a>
## Pantalla verde, colores mal o parpadeo

Una capa verde, el negro en verde o el blanco en cian, o parpadeo: la TV lee la señal de la PS4 en el formato de color equivocado.

1. Añade ` emufive.mode=1920x1080@60` a `bootargs.txt` (ver arriba).
2. Prueba otro cable o puerto HDMI. En los ajustes de la TV para ese puerto, cambia opciones como **HDMI UHD Color**, **Formato mejorado**, **Deep Colour** o **Input Signal Plus** (de activado a desactivado, o al revés), y desactiva HDMI-CEC (**Anynet+**, **Bravia Sync**...).
3. Prueba otra TV u otro monitor.

<a id="the-ps4-turns-off-or-the-light-stays-white"></a>
## La PS4 se apaga, o la luz se queda blanca

- **En 14.02**, la primera vez que lanzas el payload a veces se apaga la PS4. Lánzalo otra vez: el segundo intento suele funcionar.
- **La luz se queda blanca** y no pasa nada en 5 minutos: mantén pulsado el botón de encendido para apagar la PS4, enciéndela y lanza el payload de nuevo.
- **Una luz morada** después de instalar es normal.
- **La PS4 se apaga al pulsar el botón PS** con la pantalla negra: no lo pulses, espera (ver arriba).

<a id="no-linux-install-or-archive-found"></a>
## «No Linux install or archive found»

El menú no encontró ni un EmuFive instalado ni `ps5-ps4-rootfs.tar.xz`.

1. Revisa el nombre y el sitio del archivo: exactamente `/user/home/ps5-ps4-rootfs.tar.xz`.
2. En una **PS4 fat** (CUH-10xx, 11xx o 12xx), PS4 Multiboot v1.5.0-beta.3 a beta.7 no encontraba el disco interno. Usa el `bzImage` y el `initramfs.cpio.gz` de [v1.5.0-beta.8](https://github.com/blue0x1/ps4-multiboot/releases/tag/v1.5.0-beta.8) o una más nueva.

<a id="installing-takes-very-long"></a>
## La instalación tarda mucho

- **Crear el disco** es el primer 25 % de la barra, y es la parte lenta: todo lo que se escribe en el disco de la PS4 pasa por su cifrado. Las consolas Baikal son más lentas en esto. Un disco grande tarda más, así que para una primera prueba elige uno más pequeño (16 GB está bien). La parte después del 25 % va más rápida.
- **No apagues la PS4** mientras el porcentaje siga avanzando. Si no se mueve en 30 minutos, abre un issue y di dónde se paró.
- **Pantalla negra al final:** si la TV sigue recibiendo señal, lo más probable es que la instalación terminara y EmuFive esté arrancando. Si el botón de encendido de la PS4 la apaga normalmente, EmuFive está funcionando y solo la imagen está negra: mira [Pantalla negra tras el menú](#black-screen-after-the-menu-or-the-emufive-logo).

<a id="emufive-doesnt-start-after-a-stopped-install"></a>
## EmuFive no arranca tras una instalación interrumpida

Si la PS4 se apagó durante una instalación, puede quedar el disco a medio crear. La pantalla de error dice **«The EmuFive disk is incomplete»**, o el registro dice `is a hole`.

1. Borra `/user/home/ps5-ps4.img` por FTP. Deja `ps5-ps4-rootfs.tar.xz`.
2. Lanza el payload e instala de nuevo. Deja que termine sin apagar la PS4.

<a id="it-only-works-with-the-usb-drive-plugged-in"></a>
## Solo funciona con la unidad USB conectada

Elegiste **Install to USB drive**, así que EmuFive está en esa unidad y la necesita. Para tenerlo en la PS4: desconecta la unidad, lanza el payload y elige **Install to PS4**.

<a id="games-dont-show-up"></a>
## Los juegos no aparecen

Un juego es una **carpeta** con `eboot.bin` y `sce_sys` dentro, o un único archivo `.zar`. Los archivos `.pkg` y fpkg no sirven: extrae antes el juego. Usa dumps de juegos que tengas.

En una unidad USB tiene que quedar así:

```
Unidad USB (exFAT, una partición; NTFS también funciona)
└── PS5/                      <- exactamente "PS5", en mayúsculas, en la raíz de la unidad
    ├── PPSA01234/            <- una carpeta por juego (cualquier nombre)
    │   ├── eboot.bin         <- directamente en la carpeta del juego
    │   ├── sce_sys/
    │   │   └── param.json    <- da el nombre y la imagen del juego
    │   └── ...
    └── MiJuego.zar           <- un dump .zar, como un solo archivo
```

Errores habituales:

- `ps5/` o `Ps5/`: el nombre tiene que ser exactamente `PS5`.
- `Juegos/PS5/...`: la carpeta `PS5` tiene que estar en la raíz de la unidad.
- `PS5/PPSA01234/PPSA01234/eboot.bin`: un nivel de carpeta de más (pasa a menudo al descomprimir). Sube la carpeta interior.
- `PS5/eboot.bin`: los archivos del juego sueltos en `PS5`, sin su propia carpeta.
- Dos juegos en una misma carpeta: solo aparece uno. El nombre del icono sale de `sce_sys/param.json`, no del nombre de la carpeta, así que da a cada juego su propia carpeta.

En el disco de la PS4, la carpeta es `/user/home/PS5`, y solo funciona si EmuFive está instalado en la PS4 (no en una unidad USB). Copia los juegos con el FTP de GoldHEN desde el sistema de la PS4 y luego arranca EmuFive: lee esa carpeta al arrancar.

Deja conectada solo la unidad de los juegos. Desconecta el pendrive de registros `PS4BOOT` mientras juegas.

<a id="an-external-drive-isnt-found"></a>
## No se encuentra un disco externo

- Los SSD y discos duros externos funcionan desde EmuFive 1.0.5. Actualiza primero.
- Un disco que antes tuvo Linux puede seguir sin aparecer tras un formateo normal. Borra todas sus particiones (Windows: Administración de discos) y crea una sola partición **exFAT**.
- Si EmuFive está instalado en una unidad USB, los juegos van en una segunda unidad USB (desde EmuFive 1.0.4).

<a id="the-controller-doesnt-work"></a>
## El mando no funciona

- **En el menú de PS4 Multiboot y en las pantallas de instalación y de error**, el mando solo funciona **con cable USB**. El Bluetooth arranca más tarde, en EmuFive.
- **Por Bluetooth** hay que vincularlo una vez con EmuFive, porque la vinculación del sistema de la PS4 no sirve. Desconecta el cable, mantén **SHARE + PS** hasta que la barra de luz parpadee dos veces y espera unos segundos. Si no se conecta, usa Ajustes → Mandos → Vincular un mando nuevo.
- Usa un cable que transmita datos. Algunos cables solo cargan.
- En las consolas **Baikal** (muchas Pro CUH-71xx/72xx y Slim recientes; mira Ajustes → Sistema → Información del sistema), el USB necesita PS4 Multiboot v1.5.0-beta.7 o más nueva.

<a id="a-game-closes-freezes-or-runs-slowly"></a>
## Un juego se cierra, se congela o va lento

- **«El juego se detuvo (código de error 65)» con `ErrorDeviceLost`:** la GPU de la PS4 se bloqueó con el dibujo del juego. Pasa a menudo con juegos pesados de Unreal Engine, que todavía no son jugables. Envía el [registro del juego](#game-logs) si quieres que lo miremos.
- **Sin memoria:** un juego de PS5 puede usar hasta unos 12,5 GB, y Linux en la PS4 tiene unos 6 GB. EmuFive cierra el juego antes de que la PS4 se congele. Desactiva Ajustes → Juegos → **Memoria de juego compartida con la GPU** y prueba otra vez. EmuFive solo crea un archivo de intercambio de 4 GB si su disco tiene 8 GB libres, así que libera espacio si el disco está lleno.
- **Un juego se congela o se cierra:** prueba una vez con la **Memoria de juego compartida con la GPU** desactivada. Acelera los juegos 3D grandes, pero no le va bien a todos (Minecraft se congela con ella).
- **Tirones la primera vez:** la primera vez que sale una escena se compilan los shaders. La segunda va más fluida.
- **Cortes de imagen (tearing):** Ajustes → Juegos → Ritmo de fotogramas → **Fluido (sin cortes)**.
- **Pocos FPS:** la CPU y la GPU de la PS4 son mucho más lentas que las de la PS5. Los juegos 2D y ligeros van bien; los 3D pesados suelen cargar y mostrar sus menús, y luego van muy lentos o se quedan en negro al jugar. Una PS4 Pro es más o menos el doble de rápida que una Slim. Mira la tabla de [Juegos](README.es.md#games) antes de probar un juego grande.

<a id="how-to-save-the-logs"></a>
## Cómo guardar los registros

<a id="the-ps4boot-stick-boot-problems"></a>
### El pendrive PS4BOOT (problemas de arranque)

1. Formatea un pendrive en **FAT32** con la etiqueta **`PS4BOOT`** (en mayúsculas). Windows no puede formatear en FAT32 pendrives de más de 32 GB: usa uno más pequeño, o [Rufus](https://rufus.ie) (Elección de arranque: *No arrancable*, Sistema de archivos: *Large FAT32*, Etiqueta de volumen: `PS4BOOT`). NTFS y exFAT no sirven para esto.
2. Conéctalo a la PS4 **antes** de lanzar el payload y déjalo puesto.
3. Lanza el payload y espera **5 minutos**, aunque la pantalla siga negra. Si sale una pantalla de error, guarda ella misma los detalles en el pendrive.
4. Mantén pulsado el botón de encendido para apagar la PS4. Conecta el pendrive a un PC y adjunta los archivos `.log` a tu issue (`ps4-linux-boot.log`, `ps4-linux-late.log`, `ps4-linux-error.log` o `ps4-linux-rescue.log`).

Si el pendrive sigue vacío, dilo: significa que Linux no llegó tan lejos, y eso también ayuda.

<a id="game-logs"></a>
### Registros de los juegos

Justo después de que el juego se detenga, ve a Ajustes → Sistema → **Copiar registros al USB** y adjunta los archivos de la carpeta `PS5-logs` del USB (`kytyps5.log` es el principal). Adjunta el archivo real, no un resumen.

<a id="what-to-send"></a>
## Qué enviar

- El modelo de PS4 (CUH-xxxx, en la etiqueta de atrás), el firmware y el southbridge (Ajustes → Sistema → Información del sistema, p. ej. Belize, Baikal, Aeolia).
- La versión de PS4 Multiboot y el archivo de payload que lanzas.
- Tu línea de `bootargs.txt`.
- Tu versión de EmuFive (Ajustes → Sistema), y si está instalado en la PS4 o en una unidad USB.
- El modelo de tu TV o monitor, y lo que muestra: «Sin señal», o encendida pero en negro.
- La luz de la PS4: blanca, azul, morada o apagada.
- Los registros de arriba.
