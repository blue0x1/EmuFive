<h1 align="center"><img src="assets/emufive-logo.png" alt="EmuFive" width="480"></h1>

<p align="center">
  <img src="https://img.shields.io/badge/platform-PS4-003791?logo=playstation&logoColor=white" alt="Platform: PS4">
  <img src="https://img.shields.io/badge/status-experimental-red" alt="Status: experimental">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--2.0-blue" alt="License: GPL-2.0"></a>
</p>

<p align="center">
  <a href="README.md">EN</a> · <a href="README.ar.md">AR</a> · <b>ZH</b> · <a href="README.fr.md">FR</a> · <a href="README.es.md">ES</a> · <a href="README.de.md">DE</a> · <a href="README.it.md">IT</a> · <a href="README.pt-BR.md">PT</a> · <a href="README.tr.md">TR</a>
</p>

在 PS4 上运行的 PS5 模拟器。

作者：**[Chokri Hammedi (blue0x1)](https://github.com/blue0x1)**。基于 [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot) 构建。

> **状态：实验性研究。** 在 PS4 Pro 上，《Sons of Sparta》可以达到约 40 FPS 或更高。KytyPS5 会改写游戏代码中 PS5 专有的 CPU 指令（补丁 `0004`）。其他游戏仍在测试中，目前很多运行较慢。请参阅 [CPU 问题](#the-cpu-problem)。

<p align="center"><img src="assets/home-screen.png" alt="PS4 Pro 上的 EmuFive 主屏幕，选中了 God of War Sons of Sparta" width="900"></p>

<p align="center">
  <b><a href="#installing">安装</a></b> · <b><a href="#games">游戏</a></b> · <b><a href="#changelog">更新日志</a></b> · <a href="#how-it-works">工作原理</a> · <a href="#the-cpu-problem">CPU 问题</a> · <a href="#plan">计划</a> · <a href="#building">构建</a> · <a href="#credits">致谢</a>
</p>

<a id="how-it-works"></a>
## 工作原理

- **[PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot)** 在 PS4 上启动 Linux，并用手柄把 Linux 系统安装到 PS4 的内置硬盘上。
- **PS4 Mesa** 是 PS4 Multiboot 的一部分，为 PS4 的 GPU（PS4 和 Slim 上的 Liverpool，Pro 上的 Gladius）提供 Vulkan 1.3。KytyPS5 需要稀疏资源（sparse resources），RADV 在这款 GPU 上通过 `RADV_EXPERIMENTAL=sparse` 提供。
- **KytyPS5**：上游代码固定在某个提交，加上本项目的补丁（`patches/kytyps5/`），使用 `-march=btver2` 为 PS4 的 AMD Jaguar CPU 编译。官方版本使用 AVX2，在 PS4 上会以 "Illegal instruction" 停止。
  - `0001`：构建选项 `KYTY_HOST_ARCH`（模拟器编译的目标 CPU）。
  - `0002`：为自制程序（homebrew）提供的 C 库。用 ps5-native-app-boilerplate 构建的 PS5 自制程序自带一个替身模块 `sce_module/libc.prx`，其中所有函数都返回 0（主机使用自己的 C 库），因此在 KytyPS5 中它的 `malloc` 会失败。该补丁加入了这类自制程序导入的 C 库函数，并且只对这种替身模块使用。
  - `0003`：更多自制程序支持：文件和文件夹、系统调用、前台用户，以及额外的挂载点（`KYTY_MOUNTS`）。
  - `0004`：在 PS4 的 CPU 上运行 PS5 代码。模块加载时，每条 AVX2、FMA 和 BMI2 指令都会被改写为 SSE4.2/AVX/BMI1 代码；无法在加载时改写的指令会在第一次运行时被替换。请参阅 [CPU 问题](#the-cpu-problem)。
- **EmuFive** 把这一切打包成一个小型 Linux 系统，开机直接全屏进入模拟器，没有桌面。它和其他系统一样通过 PS4 Multiboot 安装。

<a id="the-cpu-problem"></a>

## CPU 问题

KytyPS5 并不模拟 PS5 的 CPU：它直接运行游戏自己的 x86-64 代码。PS5 游戏是为 PS5 的 Zen 2 CPU 编译的，到处使用 AVX2、BMI2 和 FMA 指令。PS4 的 Jaguar CPU 一条都没有，所以游戏代码会在遇到第一条这样的指令时停止。

补丁 `0004` 把这一功能加入了 KytyPS5 的客户机指令修补器。当主机 CPU 缺少 AVX2、FMA 或 BMI2 时，每条这样的指令都会被替换为效果相同的代码：256 位整数运算拆成两个 128 位的半部分，跨半部分的置换用 AVX 移动和混合指令完成，逐元素移位一个元素一个元素地做，FMA 用双精度计算，gather 一个元素一个元素地做，BMI2 则保存寄存器后执行。跳转到替换代码的指令写在原指令的位置；如果一条指令太短放不下跳转，又位于修补器无法重新排列的位置，它会触发异常并在运行时被替换。

`tools/jaguar-test/` 在拥有这些指令的 PC 上检查每一个替换：它取出程序代码中出现的每种指令形式，从相同的随机状态分别运行原指令和替换代码，并比较所有寄存器、标志和内存。目前测试过的程序中出现的指令形式全部一致：God of War Sons of Sparta 中有 287 种（包括 gather 和 VFMADDSUB），之前测试的程序中有 227 种。例外是 FMA 中罕见的最后一位差异（单精度会舍入两次，双精度是先乘后加），以及 0 乘以无穷大的一个 NaN 边界情况。

Jaguar 仍然比 PS5 的 CPU 慢得多，替换代码还会增加开销，所以即使游戏能运行，也可能运行得很慢。

<a id="plan"></a>
## 计划

| 步骤 | 状态 |
|---|---|
| PS4 GPU 上的 Vulkan 满足 KytyPS5 的要求 | 完成（`RADV_EXPERIMENTAL=sparse`） |
| 为 PS4 的 CPU 编译 KytyPS5 | 完成（`KYTY_HOST_ARCH=btver2`） |
| KytyPS5 在 PS4 上启动并初始化 GPU | 完成，PS4 Pro |
| EmuFive 系统镜像，通过 PS4 Multiboot 安装 | 完成，PS4 Pro |
| 不使用 AVX2 的 PS5 自制程序能运行并绘制画面 | 完成：为 btver2 重新编译的 Snes9x PS5 2.11，PS4 Pro |
| 手柄、`/data` 和 USB 存储、在该程序中加载游戏 | 已在 PC 测试版本上完成（相同补丁）；接下来是 PS4 |
| 游戏代码的 AVX2、BMI2 和 FMA 转换 | 完成（`0004`），已在 PC 上验证 |
| PS5 游戏在 PS4 上运行 | 完成：God of War Sons of Sparta，约 40 FPS 或更高，PS4 Pro |
| Hollow Knight: Silksong 在 PS4 上运行 | 自 1.0.1 起完成（补丁 `0006` 和 `0007`），PS4 Pro |
| 主屏幕：用手柄选择游戏；Wi-Fi；设置 | 完成，已在 PC 上验证 |
| 从 USB 硬盘、PS4 硬盘或 PC 共享文件夹运行游戏 | 完成，已在 PC 上验证；接下来是 PS4 |

<a id="building"></a>

## 构建

需要 Docker、git，以及来自 PS4 Multiboot 的 PS4 Mesa（`../PS4-Multiboot/out/ps4-mesa.tar.xz`，在那里用 `make mesa` 构建）。`build-kyty.sh` 第一次会把 KytyPS5 克隆到 `build/kytyps5`，之后每次构建都会把它重置到固定的提交并应用补丁。

```bash
scripts/build-kyty.sh      # out/kytyps5-ps4.tar.xz
scripts/build-rootfs.sh    # out/ps5-ps4-rootfs.tar.xz
```

`PS4_MESA` 和 `KYTY` 可以让 `build-rootfs.sh` 使用其他路径。

<a id="installing"></a>

## 安装

EmuFive 和其他 Linux 系统一样，通过 [PS4 Multiboot](https://github.com/blue0x1/ps4-multiboot) 安装。

你需要：

- 一台已破解并装有 **GoldHEN** 的 PS4（用于它的 FTP 服务器和 payload 加载器）。
- 一台在同一网络中、装有 FTP 客户端（例如 FileZilla）的 PC。
- PS4 上约 28 GB 的可用空间（16 GB 的磁盘，再加上始终为 PS4 保留的 10 GB），或者一个 8 GB 及以上的 USB 硬盘。
- 一个 DualShock 4 手柄（用 USB 线连接，或之后通过蓝牙配对）。

步骤：

1. 从 [PS4 Multiboot 发布页](https://github.com/blue0x1/ps4-multiboot/releases) 下载 `bzImage`、`initramfs.cpio.gz`、`bootargs.txt` 和 `linux-2048mb.bin`。（不需要 `ps4-mesa.tar.xz`：EmuFive 已内置 PS4 Mesa。）
2. 从 [EmuFive 发布页](https://github.com/blue0x1/EmuFive/releases) 下载 `ps5-ps4-rootfs.tar.xz`（或者自己构建，见 [构建](#building)）。不要改名：PS4 Multiboot 通过文件名中的 `-ps4-rootfs` 识别系统。
3. 打开 GoldHEN 的 FTP 服务器，把文件复制到 PS4（端口 2121）：

   | 文件 | PS4 上的文件夹 |
   |---|---|
   | `bzImage`、`initramfs.cpio.gz`、`bootargs.txt` | `/data/linux/boot/` |
   | `ps5-ps4-rootfs.tar.xz` | `/user/home/` |
   | `linux-2048mb.bin` | `/data/payloads/` |

4. 在 GoldHEN 的 payload 菜单中运行 `linux-2048mb.bin`。

   > **请耐心等待：** payload 启动后，Linux 启动期间电视可能会 **显示 "No signal" 或黑屏 1 到 2 分钟**。这是正常的。

5. 在 PS4 Multiboot 菜单中选择 **EmuFive**，然后选择 **Install to PS4** 或 **Install to USB drive**。需要几分钟。
6. 把游戏放到下面列出的某个位置。一个游戏就是一个包含 `eboot.bin`（和 `sce_sys`）的文件夹，或者一个 ZArchive（`.zar`）转储。

之后运行 payload 即可启动 EmuFive：如果只安装了 EmuFive，它会直接启动；如果还装了其他系统，会先出现 PS4 Multiboot 菜单。在主屏幕上关机或重启即可回到 PS4 系统。要重新安装 EmuFive，通过 FTP 删除 `/user/home/ps5-ps4.img` 再运行 payload。

更新来自 EmuFive 的发布页：设置（Settings）、系统（System）、软件更新（Software update）（无需重新安装）。

系统启动后进入主屏幕，不需要键盘：

- 游戏以图块显示，每个图块标明游戏所在位置：**USB**、**PS4** 或 **PC**。选中一个并按“开始”（Play）；游戏退出后会回到主屏幕。
- 顶部：Wi-Fi（密码可用屏幕键盘输入）和设置（Settings），以及两个标签页 **游戏（Games）** 和 **媒体（Media）**（L1 / R1）。媒体中显示你的截图；打开一张，按方块（Square）键删除。
- 在游戏上按 OPTIONS：收藏、隐藏、该游戏自己的设置、奖杯和游戏时长。
- **Internet**，游戏后面的图块：用手柄操作的网页浏览器。左摇杆（或触摸板）移动指针，X 键点击；右摇杆滚动；O 或 L1 后退，R1 前进；L2 和 R2 缩放。三角键输入网址或搜索词，选中网页上的文本框会打开屏幕键盘。OPTIONS 打开菜单：书签、起始页、缩放、搜索引擎（Google、DuckDuckGo 或 Bing）、移动版网站（更轻量的页面），以及清除历史记录和 Cookie。PS 键返回主屏幕，下次会打开同一个页面。它是一次只显示一个页面的 WebKitGTK，打开文字页面约占 450 MB 内存，视频网站更多；它运行时主屏幕会关闭，暂停中的游戏需要先关闭。下载、上传、摄像头、麦克风和位置都会被拒绝。书签保存在 `~/.config/ps5-on-ps4/browser.json`，Cookie 保存在 `~/.local/share/ps5-browser`。
- 游戏中按 PS 键会暂停游戏并打开快捷菜单：继续（Resume）、**主屏幕（Home）**（游戏保持暂停：按 PS 或“继续”返回游戏；启动另一个游戏时会先询问，然后关闭它）、关闭游戏、音量、电源。
- 截图：PS + 方块，或 Share，游戏中也可以。截图保存到 USB 硬盘上的 `PS5-screenshots`（没有 USB 时保存到 `~/Screenshots`），角落会显示一个小提示。要把截图传到手机上，在媒体中打开它并按三角键（分享）：用手机（在同一网络中）扫描二维码即可在手机上打开，然后保存或分享。PS4 只提供这一张图片，使用随机地址，并且只在二维码显示期间可用。二维码由 `python3-segno` 生成。
- 设置、外观（Appearance）：强调色、主题（深色、午夜、浅色）、背景（游戏图片、渐变、纯色或 USB 硬盘中你自己的图片）、背景变暗、漂浮光球、动画、图块大小和形状、文字大小和字体、时钟、顶部栏显示的内容（电池是手柄的电量）、菜单音效、震动、按键提示、屏幕边缘（overscan）和屏幕保护程序。
- 设置、控制器（Controllers）：灯条颜色和亮度、震动开关及强度、手柄麦克风开关（手柄需用 USB 线连接；Linux 不支持通过蓝牙传输手柄声音）、交换 X 和 O，以及每个按键和摇杆的测试页面。设置、游戏（Games）：所有游戏的默认设置、游戏语言、HDR 和帧节奏。设置、日期和时间（Date and time）：从互联网自动设置（默认）或手动设置。设置、系统（System）：菜单语言（英语、阿拉伯语、法语、土耳其语、西班牙语、德语、意大利语或巴西葡萄牙语）、温度和 CPU 负载、把设置备份到 USB 硬盘，或全部重置。
- 用户档案（设置、档案（Profile），以及快捷菜单中的切换档案（Switch profile））：最多 8 个，每个都有自己的名字、头像、存档、奖杯和游戏时长。有多个档案时，启动时会出现 "Who's playing?"。每个档案都有自己的 KytyPS5 文件夹（`~/.kytyps5/users/<ID>`，第一个档案仍使用 `~/.kytyps5`），着色器缓存共享。
- 左上角的通知，游戏中也会显示：截图已保存、手柄已连接（附连接方式和电量）、手柄电量低（15%）。顶部栏的电池按电量显示为绿色、黄色或红色，充电时显示闪电图标。
- 内存不足时：系统盘上有一个 4 GB 的 swap 文件（`ps5-swap.service`，在空间足够时创建一次），让大型游戏变慢而不是让 PS4 卡死；如果内存和 swap 仍然耗尽，游戏会在 PS4 卡死之前被关闭，主屏幕会说明原因。
- 菜单语言：翻译在 `lib/ps5/translations.json` 中，每条英文文本一项。阿拉伯语右对齐，使用 DejaVu Sans 绘制；由于这里的 SDL_ttf 不会连接阿拉伯字母，字母连写在 `lib/ps5/i18n.py` 中完成。
- 程序把 USB 硬盘看作 `/mnt/usb0`，把系统中的一个文件夹（`~/data`，重启后保留）看作 `/data`。对于 Snes9x PS5，ROM 放在 USB 硬盘的 `snes9x/roms` 或 `~/data/snes9x/roms` 中。
- 如果模拟器因错误停止，主屏幕会显示原因。
- `/etc/ps5-on-ps4.conf` 中的 `PS5_GAME` 可以直接运行一个游戏，而不显示主屏幕。
- 手柄：用线连接的 DualShock 4，或者按住 SHARE + PS 直到灯条双闪后通过蓝牙连接。
- 声音通过 HDMI 输出到电视，即使用线连接的手柄带来了自己的声卡也是如此（`/etc/wireplumber/wireplumber.conf.d/51-ps5-hdmi.conf`）。

### 游戏可以放在哪里

- **USB 硬盘：** 硬盘根目录下的 `PS5` 文件夹。最好使用 exFAT（支持超过 4 GB 的文件）；NTFS 也可以。
- **PS4 硬盘：** PS4 上的 `/user/home/PS5`，用 GoldHEN 的 FTP 复制进去。系统以只读方式读取 PS4 硬盘，绝不会修改它。如果系统本身安装在 USB 硬盘上，则不可用。
- **PC：** Windows 或 Linux 上的共享文件夹。在设置中打开 **从 PC 使用游戏（Use games from PC）**，填写 PC 地址、共享文件夹，以及用户名和密码（访客共享除外）；然后点击“连接”（Connect）。游戏可以放在共享文件夹的根目录，或其中的 `PS5` 文件夹里。网线比 Wi-Fi 更快。
  - Windows：共享该文件夹（属性、共享）。如果要访客共享，请共享给 Everyone，并在高级共享设置中关闭 *Password protected sharing*。
  - Linux（Samba）：访客共享使用 `guest ok = yes`，或者使用 Samba 用户（`smbpasswd -a`）。
  - PS4 内核没有 SMB 客户端，所以系统使用 smbnetfs（FUSE）。设置（包括密码）保存在 `~/.config/ps5-on-ps4/pc-share.json` 中，只有 `ps5` 用户可以读取。

`tools/make-pad-test-rom.py` 会生成一个用于检查手柄的小型 SNES ROM：平时显示蓝色，按住按键时显示绿色。

登录：在 tty2 或 SSH 上使用 `ps5` / `ps5`。模拟器的输出在 `~/kytyps5.log`（上一次运行：`~/kytyps5.log.1`）。

<a id="games"></a>
## 游戏

本项目不包含任何 PS5 系统软件，也不包含任何游戏。请只使用你自己拥有并亲自转储的游戏。

已测试的游戏：

| 游戏 | 主机 | 结果 |
|---|---|---|
| God of War Sons of Sparta | PS4 Pro | 可玩，约 40 FPS 及以上 |
| Hollow Knight: Silksong | PS4 Pro | 可玩，50 到 60 FPS |
| Plants vs. Zombies: Replanted | PS4 Pro | 可玩，锁定 60 FPS |
| Vampire Survivors | PS4 Slim | 可玩，稳定 60 FPS |
| Spider-Man 2 | | 尚未测试 |

测试过某个游戏？请开一个 [issue](https://github.com/blue0x1/EmuFive/issues)，写明游戏、主机型号和运行情况。

<a id="changelog"></a>
## 更新日志

### 1.0.6 (2026-11-14)

- 改进：无人操作时主屏幕占用的 CPU 大幅减少（4K 下约为一个核心的三分之一，之前占满一个核心），PS4 因此更凉、更安静。

从 1.0.3 或更早版本更新时，旧的软件更新无法完成，请手动启动一次：在设置中打开 SSH，用 `ssh ps5@<PS4 地址>` 连接（未修改时密码为 `ps5`），然后运行

```bash
sudo systemd-run --unit=emufive-update --collect /opt/ps5-on-ps4/bin/ps5-update install
```

它会安装所有缺少的更新（从 1.0.0 或 1.0.1 更新时包括 1.0.2 的浏览器软件包，约 110 MB），完成后在主屏幕上重启。从 1.0.4 起，设置中的软件更新可以正常使用。新安装请使用 1.0.6 版本中的 `ps5-ps4-rootfs.tar.xz`。

## 项目结构

| 路径 | 内容 |
|---|---|
| `scripts/build-kyty.sh` | 为 PS4 的 CPU 构建 KytyPS5（上游代码加上 `patches/kytyps5/`） |
| `patches/kytyps5/` | 本项目对 KytyPS5 的修改 |
| `scripts/build-rootfs.sh` | 构建 PS4 Multiboot 使用的系统镜像 |
| `scripts/make-release.sh` | 制作发布版的更新包（由 设置、系统、软件更新 安装） |
| `scripts/updates/` | 更新在 PS4 上复制完文件后运行的脚本（`--post`） |
| `docker/` | 两者的构建环境 |
| `overlay/` | 添加到系统中的文件：会话、主屏幕、设置、USB 和 PS4 硬盘挂载、手柄配对 |
| `tools/` | Logo 转换器、手柄测试 ROM、`extract-code.py`（提取 PS5 SELF/ELF 的代码） |
| `tools/jaguar-test/` | 将补丁 `0004` 的替换代码与真实指令进行对比检查 |

## 特别感谢

- [KytyPS5](https://github.com/KytyPS5/KytyPS5)，EmuFive 所基于的 PS5 模拟器（GPL-2.0）
- InoriRus 的 [Kyty](https://github.com/InoriRus/Kyty)，KytyPS5 所基于的模拟器

<a id="credits"></a>
## 致谢

- [Mesa](https://mesa3d.org)，以及 fail0verflow、DionKill 和 striker91n 的 PS4 GPU 补丁
- PS4 Linux 内核开发者（[sony-jaguar-devs/ps4-linux](https://github.com/sony-jaguar-devs/ps4-linux)）

## 许可证

Copyright (C) 2026 [Chokri Hammedi (blue0x1)](https://github.com/blue0x1)。

GPL-2.0（见 `LICENSE`）。KytyPS5、Mesa 和 Linux 内核使用各自的许可证。PlayStation 是 Sony Interactive Entertainment 的商标；本项目与 Sony 没有任何关联。
