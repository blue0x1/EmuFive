#!/usr/bin/env bash
# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
# Builds KytyPS5 for the PS4's CPU (AMD Jaguar, -march=btver2) and packs it as
# out/kytyps5-ps4.tar.xz for the system image.
#   KYTY_SRC=path/to/KytyPS5 scripts/build-kyty.sh
# KYTY_SRC defaults to ../KytyPS5-PS4: a KytyPS5 checkout with the
# KYTY_HOST_ARCH build option (branch ps4-host-arch).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/out"
KYTY_SRC="$(cd "${KYTY_SRC:-$ROOT/../KytyPS5-PS4}" && pwd)"
IMAGE=ps5-on-ps4-kyty-builder
BUILD_DIR=_Build/ps4

log() { printf '\033[1;34m[*]\033[0m %s\n' "$*"; }
ok()  { printf '\033[1;32m[+]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[-]\033[0m %s\n' "$*" >&2; exit 1; }

grep -q KYTY_HOST_ARCH "$KYTY_SRC/src/utils.cmake" 2>/dev/null \
    || die "$KYTY_SRC has no KYTY_HOST_ARCH option (use the ps4-host-arch branch)"
version="$(git -C "$KYTY_SRC" describe --always --dirty 2>/dev/null || echo unknown)"
branch="$(git -C "$KYTY_SRC" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"

log "Build environment"
docker build -q -t "$IMAGE" -f "$ROOT/docker/kyty-build.Dockerfile" "$ROOT/docker" > /dev/null

log "Building KytyPS5 $version ($branch) for btver2"
git -C "$KYTY_SRC" submodule update --init --recursive
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -v "$KYTY_SRC:/src" -w /src "$IMAGE" sh -euc "
    cmake -S . -B $BUILD_DIR -G Ninja -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
        -DKYTY_BUILD_LAUNCHER=OFF -DKYTY_HOST_ARCH=btver2 -DKYTY_DEBUG_INFO=OFF
    cmake --build $BUILD_DIR --target kyty_emulator --parallel"

log "Packing"
stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT
mkdir -p "$stage/kytyps5" "$OUT"
cp "$KYTY_SRC/$BUILD_DIR/kyty_emulator" "$stage/kytyps5/"
strip "$stage/kytyps5/kyty_emulator"
cp -a "$KYTY_SRC/$BUILD_DIR/assets" "$stage/kytyps5/"
cp "$KYTY_SRC/LICENSE" "$stage/kytyps5/LICENSE"
printf 'KytyPS5 %s (branch %s), built for -march=btver2\n' "$version" "$branch" > "$stage/kytyps5/VERSION"
tar -C "$stage" --owner=0 --group=0 --numeric-owner -cJf "$OUT/kytyps5-ps4.tar.xz" kytyps5
ok "KytyPS5: $OUT/kytyps5-ps4.tar.xz ($(du -h "$OUT/kytyps5-ps4.tar.xz" | cut -f1)), $version"
