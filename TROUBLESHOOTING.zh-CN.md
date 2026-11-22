# 故障排除

<p align="center">
  <a href="TROUBLESHOOTING.md">EN</a> · <a href="TROUBLESHOOTING.ar.md">AR</a> · <b>ZH</b> · <a href="TROUBLESHOOTING.fr.md">FR</a> · <a href="TROUBLESHOOTING.es.md">ES</a> · <a href="TROUBLESHOOTING.de.md">DE</a> · <a href="TROUBLESHOOTING.it.md">IT</a> · <a href="TROUBLESHOOTING.pt-BR.md">PT</a> · <a href="TROUBLESHOOTING.tr.md">TR</a>
</p>

这里是大家在 [issues](https://github.com/blue0x1/EmuFive/issues) 中报告过的问题，以及对他们有效的解决方法。请按顺序尝试。仍然不行？请开一个 issue，附上[需要发送的信息](#what-to-send)。

EmuFive 的菜单没有中文，下面的菜单名称用英文写出，括号里是中文意思。

- [先检查文件](#check-the-files-first)
- [运行 payload 后黑屏或“无信号”](#black-screen-or-no-signal-after-the-payload)
- [菜单或 EmuFive 标志之后黑屏](#black-screen-after-the-menu-or-the-emufive-logo)
- [画面发绿、颜色不对或闪烁](#green-screen-wrong-colors-or-flickering)
- [PS4 关机，或指示灯一直是白色](#the-ps4-turns-off-or-the-light-stays-white)
- [“No Linux install or archive found”](#no-linux-install-or-archive-found)
- [安装非常慢](#installing-takes-very-long)
- [安装中断后 EmuFive 无法启动](#emufive-doesnt-start-after-a-stopped-install)
- [只有插着 USB 硬盘才能用](#it-only-works-with-the-usb-drive-plugged-in)
- [游戏不显示](#games-dont-show-up)
- [找不到外接硬盘](#an-external-drive-isnt-found)
- [手柄不能用](#the-controller-doesnt-work)
- [游戏关闭、卡死或很慢](#a-game-closes-freezes-or-runs-slowly)
- [如何保存日志](#how-to-save-the-logs)
- [需要发送的信息](#what-to-send)

<a id="check-the-files-first"></a>
## 先检查文件

大多数“什么都没发生”的报告都是下面某一点造成的：

- **同一个版本：** `bzImage`、`initramfs.cpio.gz`、`bootargs.txt` 和 `linux-2048mb.bin` 必须都来自同一个 [PS4 Multiboot 版本](https://github.com/blue0x1/ps4-multiboot/releases)（最好是最新版）。混用不同版本的文件无法启动。
- **文件夹名用小写：** PS4 把 `LINUX` 和 `linux` 当作不同的文件夹。路径必须正好是 `/data/linux/boot/bzImage`、`/data/linux/boot/initramfs.cpio.gz` 和 `/data/linux/boot/bootargs.txt`。
- **压缩包的准确名称：** `/user/home/ps5-ps4-rootfs.tar.xz`。浏览器有时会把它存成 `ps5-ps4-rootfs (1).tar.xz`，这样菜单就找不到它。
- **二进制传输：** 在 FileZilla 中，上传前选择 传输 → 传输类型 → **二进制**。用文本模式上传的文件会损坏。确认 PS4 上每个文件的大小和发布页上的一样。
- **我们的 payload：** 使用 PS4 Multiboot 的 `linux-2048mb.bin`（固件 14.02 上用 `linux-2048mb-14.02.bin`）。它支持固件 5.05 到 14.02。不支持其他 Linux payload。

<a id="black-screen-or-no-signal-after-the-payload"></a>
## 运行 payload 后黑屏或“无信号”

payload 启动后，Linux 启动期间电视会显示“无信号”或黑屏 **1 到 2 分钟**。这是正常的。payload 运行后屏幕和手柄马上熄灭也是正常的：PS4 系统关闭，由 Linux 接管。

**屏幕黑着的时候不要按 PS 键**：这会让 PS4 关机。如果 PS4 上只有 EmuFive，安装程序会在 60 秒后自动开始，所以它可能已经在安装了。

如果 3 分钟后还是什么都没有：

1. 把 PS4 **直接**连到电视上，不要经过 HDMI 切换器、功放或采集卡。
2. 在 PS4 上关闭 **设定 → 系统 → 启用 HDCP**，然后再次运行 payload。
3. 换一根 HDMI 线，换一个 HDMI 接口。
4. 试一次别的电视或显示器。有些电视不接受 PS4 的 Linux 信号，换一个屏幕就能看出是不是电视的问题。
5. 还是不行？保存 [PS4BOOT 日志](#the-ps4boot-stick-boot-problems)，然后开一个 issue。告诉我们电视显示的是 **“无信号”**，还是开着但全黑。

<a id="black-screen-after-the-menu-or-the-emufive-logo"></a>
## 菜单或 EmuFive 标志之后黑屏

如果你看到了 PS4 Multiboot 菜单或 EmuFive 的标志，然后变成黑屏，说明 EmuFive 切换到了你的电视偏好、但 PS4 无法输出的模式。

1. 更新 EmuFive（Settings → System → Software update，即 设置 → 系统 → 软件更新）。
2. 通过 FTP 打开 `/data/linux/boot/bootargs.txt`，在这一行末尾加上 ` emufive.mode=1920x1080@60`。同时保留 `video=HDMI-A-1:1920x1080@60D`。文件必须保持**只有一行**。
3. 再次运行 payload。

因为黑屏没法更新？先接一次别的电视或显示器来更新，或者用最新的 `ps5-ps4-rootfs.tar.xz` 重新安装 EmuFive。

<a id="green-screen-wrong-colors-or-flickering"></a>
## 画面发绿、颜色不对或闪烁

画面蒙上一层绿色、黑色显示成绿色或白色显示成青色，或者画面闪烁：说明电视用错误的色彩格式读取了 PS4 的信号。

1. 在 `bootargs.txt` 中加上 ` emufive.mode=1920x1080@60`（见上文）。
2. 换一根 HDMI 线或换一个接口。在电视对应接口的设置里，切换 **HDMI UHD Color**、**增强格式**、**Deep Colour** 或 **Input Signal Plus** 之类的选项（开改成关，或关改成开），并关闭 HDMI-CEC（**Anynet+**、**Bravia Sync** 等）。
3. 换一台电视或显示器试试。

<a id="the-ps4-turns-off-or-the-light-stays-white"></a>
## PS4 关机，或指示灯一直是白色

- **在 14.02 上**，第一次运行 payload 有时会让 PS4 关机。再运行一次：第二次通常就能成功。
- **指示灯一直是白色**，5 分钟都没有反应：长按电源键关闭 PS4，重新开机，再运行一次 payload。
- 安装之后 **指示灯变成紫色** 是正常的。
- 黑屏时 **按了 PS 键 PS4 就关机**：不要按，耐心等待（见上文）。

<a id="no-linux-install-or-archive-found"></a>
## “No Linux install or archive found”

菜单既没有找到已安装的 EmuFive，也没有找到 `ps5-ps4-rootfs.tar.xz`。

1. 检查压缩包的名称和位置：必须正好是 `/user/home/ps5-ps4-rootfs.tar.xz`。
2. 在 **初代 PS4（fat）**（CUH-10xx、11xx 或 12xx）上，PS4 Multiboot v1.5.0-beta.3 到 beta.7 找不到内置硬盘。请使用 [v1.5.0-beta.8](https://github.com/blue0x1/ps4-multiboot/releases/tag/v1.5.0-beta.8) 或更新版本的 `bzImage` 和 `initramfs.cpio.gz`。

<a id="installing-takes-very-long"></a>
## 安装非常慢

- **创建磁盘**是进度条的前 25%，也是最慢的部分：写入 PS4 硬盘的所有数据都要经过 PS4 的磁盘加密。Baikal 主机在这一步更慢。磁盘越大耗时越长，所以第一次尝试时选小一点（16 GB 就够）。25% 之后的部分会快很多。
- 只要百分比还在走，**就不要关闭 PS4**。如果 30 分钟都不动，请开一个 issue，说明停在了哪里。
- **最后黑屏：** 如果电视仍然有信号，安装很可能已经完成，EmuFive 正在启动。如果按 PS4 的电源键能正常关机，说明 EmuFive 在运行，只是画面是黑的：见[菜单之后黑屏](#black-screen-after-the-menu-or-the-emufive-logo)。

<a id="emufive-doesnt-start-after-a-stopped-install"></a>
## 安装中断后 EmuFive 无法启动

如果安装过程中 PS4 被关机，可能会留下一个只创建了一半的磁盘。错误界面会显示 **“The EmuFive disk is incomplete”**，或者日志里有 `is a hole`。

1. 通过 FTP 删除 `/user/home/ps5-ps4.img`。保留 `ps5-ps4-rootfs.tar.xz`。
2. 运行 payload 重新安装。等它装完，不要关闭 PS4。

<a id="it-only-works-with-the-usb-drive-plugged-in"></a>
## 只有插着 USB 硬盘才能用

你选择了 **Install to USB drive**，所以 EmuFive 装在那个 USB 硬盘上，需要它插着。想装到 PS4 上：拔掉 USB 硬盘，运行 payload，然后选择 **Install to PS4**。

<a id="games-dont-show-up"></a>
## 游戏不显示

一个游戏是一个**文件夹**，里面有 `eboot.bin` 和 `sce_sys`，或者是单个 `.zar` 文件。`.pkg` 和 fpkg 文件不能用：请先把游戏解包。请使用你自己拥有的游戏的 dump。

USB 硬盘上的结构必须是这样：

```
USB 硬盘（exFAT，一个分区；NTFS 也可以）
└── PS5/                      <- 必须是 "PS5"，大写，放在硬盘最上层
    ├── PPSA01234/            <- 每个游戏一个文件夹（名字随意）
    │   ├── eboot.bin         <- 直接放在游戏文件夹里
    │   ├── sce_sys/
    │   │   └── param.json    <- 提供游戏名称和图片
    │   └── ...
    └── MyGame.zar            <- .zar dump，单个文件
```

常见错误：

- `ps5/` 或 `Ps5/`：名字必须正好是 `PS5`。
- `Games/PS5/...`：`PS5` 文件夹必须在硬盘最上层。
- `PS5/PPSA01234/PPSA01234/eboot.bin`：多了一层文件夹（解压后很常见）。把里面那层文件夹移上来。
- `PS5/eboot.bin`：游戏文件直接散放在 `PS5` 里，没有自己的文件夹。
- 两个游戏放在同一个文件夹里：只会显示一个。图标上的名字来自 `sce_sys/param.json`，而不是文件夹名，所以每个游戏都要有自己的文件夹。

在 PS4 硬盘上，文件夹是 `/user/home/PS5`，而且只有 EmuFive 装在 PS4 上（不是装在 USB 硬盘上）时才有效。在 PS4 系统中用 GoldHEN 的 FTP 复制游戏，然后启动 EmuFive：它在启动时读取这个文件夹。

只插着放游戏的硬盘。玩游戏时拔掉 `PS4BOOT` 日志 U 盘。

<a id="an-external-drive-isnt-found"></a>
## 找不到外接硬盘

- 外接 SSD 和机械硬盘从 EmuFive 1.0.5 起可用。请先更新。
- 以前装过 Linux 的硬盘，普通格式化后可能仍然不显示。删除它的所有分区（Windows：磁盘管理），然后只建一个 **exFAT** 分区。
- 如果 EmuFive 装在一个 USB 硬盘上，游戏要放在第二个 USB 硬盘上（从 EmuFive 1.0.4 起）。

<a id="the-controller-doesnt-work"></a>
## 手柄不能用

- **在 PS4 Multiboot 菜单以及安装和错误界面上**，手柄只能**用 USB 线**连接。蓝牙要到 EmuFive 里才启动。
- **蓝牙**需要和 EmuFive 配对一次，因为 PS4 系统里的配对不会沿用。拔掉线，按住 **SHARE + PS** 直到灯条快速双闪，然后等几秒。如果连不上，使用 Settings → Controllers → Pair a new controller（设置 → 手柄 → 配对新手柄）。
- 使用能传输数据的线。有些线只能充电。
- 在 **Baikal** 主机上（很多 CUH-71xx/72xx Pro 和较新的 Slim；可在 设定 → 系统 → 系统信息 中查看），USB 需要 PS4 Multiboot v1.5.0-beta.7 或更新版本。

<a id="a-game-closes-freezes-or-runs-slowly"></a>
## 游戏关闭、卡死或很慢

- **“The game stopped (error code 65)” 并带有 `ErrorDeviceLost`：** PS4 的 GPU 在绘制游戏画面时卡死了。这在大型 Unreal Engine 游戏中很常见，这些游戏目前还不能玩。如果想让我们看看，请发送[游戏日志](#game-logs)。
- **内存不足：** 一个 PS5 游戏最多可以用大约 12.5 GB，而 PS4 上的 Linux 只有大约 6 GB。EmuFive 会在 PS4 卡死之前关闭游戏。关闭 Settings → Games → **GPU-shared game memory**（设置 → 游戏 → 与 GPU 共享游戏内存）后再试。EmuFive 只有在它的磁盘有 8 GB 空闲时才会创建 4 GB 的交换文件，磁盘满了请腾出空间。
- **游戏卡死或崩溃：** 关闭 **GPU-shared game memory** 再试一次。它能加快大型 3D 游戏，但不适合所有游戏（Minecraft 开着它会卡死）。
- **第一次运行时卡顿：** 场景第一次出现时要编译着色器。第二次会流畅一些。
- **画面撕裂：** Settings → Games → Frame pacing → **Smooth (no tearing)**（设置 → 游戏 → 帧节奏 → 流畅（无撕裂））。
- **帧数低：** PS4 的 CPU 和 GPU 比 PS5 慢得多。2D 游戏和轻量游戏运行良好；大型 3D 游戏常常能加载并显示菜单，但进入游戏后非常慢或一直黑屏。PS4 Pro 大约比 Slim 快一倍。尝试大型游戏前，请先看[游戏](README.zh-CN.md#games)列表。

<a id="how-to-save-the-logs"></a>
## 如何保存日志

<a id="the-ps4boot-stick-boot-problems"></a>
### PS4BOOT U 盘（启动问题）

1. 把一个 U 盘格式化为 **FAT32**，卷标为 **`PS4BOOT`**（全大写）。Windows 无法把大于 32 GB 的 U 盘格式化为 FAT32：请用更小的 U 盘，或者用 [Rufus](https://rufus.ie)（引导类型选择：*非可引导*，文件系统：*Large FAT32*，卷标：`PS4BOOT`）。NTFS 和 exFAT 不能用于这个用途。
2. **在运行 payload 之前**把它插到 PS4 上，并一直插着。
3. 运行 payload，等 **5 分钟**，即使屏幕一直是黑的。如果出现错误界面，它会自己把详细信息保存到 U 盘上。
4. 长按电源键关闭 PS4。把 U 盘插到电脑上，把 `.log` 文件附到你的 issue 里（`ps4-linux-boot.log`、`ps4-linux-late.log`、`ps4-linux-error.log` 或 `ps4-linux-rescue.log`）。

如果 U 盘一直是空的，也请告诉我们：这说明 Linux 没有运行到那一步，这同样有帮助。

<a id="game-logs"></a>
### 游戏日志

游戏停止后，马上进入 Settings → System → **Copy logs to USB**（设置 → 系统 → 复制日志到 USB），然后附上 U 盘中 `PS5-logs` 文件夹里的文件（最重要的是 `kytyps5.log`）。请附上真实的文件，而不是摘要。

<a id="what-to-send"></a>
## 需要发送的信息

- PS4 型号（CUH-xxxx，在机身背面的标签上）、固件版本和南桥（设定 → 系统 → 系统信息，例如 Belize、Baikal、Aeolia）。
- PS4 Multiboot 的版本，以及你运行的 payload 文件。
- 你的 `bootargs.txt` 那一行。
- 你的 EmuFive 版本（Settings → System），以及它装在 PS4 上还是 USB 硬盘上。
- 你的电视或显示器型号，以及它显示什么：“无信号”，还是开着但全黑。
- PS4 的指示灯：白色、蓝色、紫色或熄灭。
- 上面提到的日志。
