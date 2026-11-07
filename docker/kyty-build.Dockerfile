# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
# Build environment for KytyPS5 on the PS4 (Linux on PS4, AMD Jaguar CPU).
# The packages are the ones the Linux build instructions in KytyPS5's README.md list.
FROM docker.io/library/debian:trixie

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        clang lld ninja-build cmake git glslang-tools python3 pkg-config ca-certificates curl \
        libgl1-mesa-dev libx11-dev libxcursor-dev libxext-dev libxfixes-dev \
        libxi-dev libxrandr-dev libxss-dev libxtst-dev libxkbcommon-dev \
        libasound2-dev libpulse-dev libudev-dev libdbus-1-dev libwayland-dev wayland-protocols \
        qt6-base-dev \
    && rm -rf /var/lib/apt/lists/*
