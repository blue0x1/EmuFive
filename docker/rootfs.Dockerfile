# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
# The EmuFive system: Debian, X, the PS4 Mesa (Vulkan on the PS4 GPU) and
# KytyPS5 built for the PS4's CPU, starting straight into the emulator. Built
# with `docker build` and exported as a rootfs archive by
# scripts/build-rootfs.sh; PS4 Multiboot installs it and adds the PS4 kernel
# modules, firmware and HDMI fix.
FROM docker.io/library/debian:trixie

ARG USER_NAME=ps5
ARG USER_PASS=ps5
ENV DEBIAN_FRONTEND=noninteractive

# Base system, network, X, audio, and the libraries KytyPS5 loads at run time
# (X11, Vulkan, audio, input). The home screen: Python and pygame; smbnetfs
# opens a PC's shared folder (the PS4 kernel has no SMB client, but has FUSE).
# Internet, the web browser (ps5-browser): WebKitGTK, with GStreamer for video.
RUN apt-get update && apt-get install -y --no-install-recommends \
        systemd systemd-sysv dbus dbus-user-session udev kmod sudo locales less nano xz-utils \
        systemd-timesyncd network-manager wpasupplicant iproute2 iputils-ping openssh-server ca-certificates curl \
        bluez \
        xserver-xorg-core xserver-xorg-input-libinput xinit x11-xserver-utils xterm \
        matchbox-window-manager \
        pipewire pipewire-pulse pipewire-alsa wireplumber libspa-0.2-bluetooth \
        libgl1 libegl1 libgles2 libvulkan1 libgl1-mesa-dri libglx-mesa0 libegl-mesa0 \
        vulkan-tools fonts-dejavu-core libasound2t64 libpulse0 libxkbcommon-x11-0 \
        libx11-6 libx11-xcb1 libxcursor1 libxext6 libxfixes3 libxi6 libxrandr2 libxss1 libxtst6 \
        libxkbcommon0 libwayland-client0 libwayland-cursor0 libwayland-egl1 libdecor-0-0 \
        libxcb-keysyms1 libudev1 libdbus-1-3 libusb-1.0-0 \
        python3 python3-pygame python3-segno fonts-inter \
        smbnetfs fuse3 \
        python3-gi python3-gi-cairo gir1.2-webkit2-4.1 gstreamer1.0-plugins-good gstreamer1.0-libav \
        adwaita-icon-theme \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# KytyPS5 for the PS4's CPU (scripts/build-kyty.sh), in /opt/kytyps5.
COPY build/ctx/kytyps5-ps4.tar.xz /tmp/kytyps5.tar.xz
RUN tar -xJf /tmp/kytyps5.tar.xz -C /opt && rm /tmp/kytyps5.tar.xz \
 && ln -s /opt/kytyps5/kyty_emulator /usr/local/bin/kyty_emulator

# PS4 Mesa: OpenGL and Vulkan on the PS4 GPU, the system's driver, and GPU
# acceleration for X (glamor).
COPY build/ctx/ps4-mesa.tar.xz /tmp/ps4-mesa.tar.xz
# .bundled tells the PS4 Multiboot installer to keep this one, even when an
# older ps4-mesa.tar.xz is in /user/home.
RUN tar -xJf /tmp/ps4-mesa.tar.xz -C / && rm /tmp/ps4-mesa.tar.xz \
 && /opt/ps4-mesa/bin/ps4-mesa-enable \
 && touch /opt/ps4-mesa/.bundled

# The PS5 user logs in on tty1 by itself; tty2 keeps a normal login prompt.
RUN useradd -m -s /bin/bash -G sudo,video,render,input,audio,netdev,plugdev "$USER_NAME" \
 && echo "$USER_NAME:$USER_PASS" | chpasswd \
 && echo "LANG=C.UTF-8" > /etc/default/locale

COPY overlay/ /
RUN chmod 0440 /etc/sudoers.d/ps5-poweroff /etc/sudoers.d/ps5-network /etc/sudoers.d/ps5-admin \
 && visudo -c \
 && chown -R "$USER_NAME:$USER_NAME" "/home/$USER_NAME"

# Bluetooth powers on at boot; ps5-pad-pair pairs controllers held in pairing
# mode (SHARE + PS), so they work without a cable.
# IdleTimeout=0: a connected controller stays connected while it is not used.
# FastConnectable: a paired controller reconnects quickly (PS button).
RUN sed -i 's/^#AutoEnable=.*/AutoEnable=true/' /etc/bluetooth/main.conf \
 && grep -q '^AutoEnable=true' /etc/bluetooth/main.conf \
 && sed -i 's/^#IdleTimeout=.*/IdleTimeout=0/' /etc/bluetooth/input.conf \
 && grep -q '^IdleTimeout=0' /etc/bluetooth/input.conf \
 && sed -i 's/^#FastConnectable *=.*/FastConnectable = true/' /etc/bluetooth/main.conf \
 && grep -q '^FastConnectable = true' /etc/bluetooth/main.conf

# Unique SSH host keys and machine-id per install; services. SSH starts off: the
# password is the published default until changed in Settings, Advanced, which
# asks for a new one before it turns SSH on.
RUN rm -f /etc/ssh/ssh_host_* \
 && : > /etc/machine-id && rm -f /var/lib/dbus/machine-id \
 && systemctl enable ps5-hostkeys.service NetworkManager.service systemd-timesyncd.service \
        bluetooth.service ps5-pad-pair.service ps5-bt-watchdog.service ps5-ps4-drive.service ps5-swap.service ps5-clear-logs.timer \
 && systemctl disable ssh.service \
 && systemctl set-default multi-user.target \
 && date -u +%Y-%m-%d > /etc/ps5-on-ps4-release
