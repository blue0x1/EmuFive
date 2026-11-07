#!/usr/bin/env bash
# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
# Builds KytyPS5 for the PS4's CPU (AMD Jaguar, -march=btver2) and packs it as
# out/kytyps5-ps4.tar.xz for the system image.
#
# The source is upstream KytyPS5 at KYTY_COMMIT, checked out in build/kytyps5,
# with this project's patches (patches/kytyps5/*.patch) applied on top. Every
# build resets that checkout to KYTY_COMMIT first; _Build/ stays, so rebuilds
# are incremental.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/out"
KYTY_URL=https://github.com/KytyPS5/KytyPS5.git
KYTY_COMMIT=589bd14a9b8934a85e951d1aaa8112a05d62354c
SRC="$ROOT/build/kytyps5"
PATCHES="$ROOT/patches/kytyps5"
IMAGE=ps5-on-ps4-kyty-builder
BUILD_DIR=_Build/ps4

log() { printf '\033[1;34m[*]\033[0m %s\n' "$*"; }
ok()  { printf '\033[1;32m[+]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[-]\033[0m %s\n' "$*" >&2; exit 1; }

if [ ! -d "$SRC/.git" ]; then
    log "Cloning KytyPS5"
    mkdir -p "$(dirname "$SRC")"
    git clone -q "$KYTY_URL" "$SRC"
fi

log "KytyPS5 ${KYTY_COMMIT:0:7} + $(ls "$PATCHES"/*.patch | wc -l) patches"
git -C "$SRC" cat-file -e "$KYTY_COMMIT^{commit}" 2>/dev/null || git -C "$SRC" fetch -q origin
git -C "$SRC" checkout -q --force --detach "$KYTY_COMMIT"
git -C "$SRC" clean -q -fd -e _Build/
git -C "$SRC" submodule update -q --init --recursive
for p in "$PATCHES"/*.patch; do
    git -C "$SRC" apply --whitespace=nowarn "$p" || die "patch does not apply: $p"
done
version="${KYTY_COMMIT:0:7}+$(cd "$PATCHES" && cat ./*.patch | sha256sum | cut -c1-8)"

log "Build environment"
docker build -q -t "$IMAGE" -f "$ROOT/docker/kyty-build.Dockerfile" "$ROOT/docker" > /dev/null

log "Building KytyPS5 $version for btver2"
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -v "$SRC:/src" -w /src "$IMAGE" sh -euc "
    cmake -S . -B $BUILD_DIR -G Ninja -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
        -DKYTY_BUILD_LAUNCHER=OFF -DKYTY_HOST_ARCH=btver2 -DKYTY_DEBUG_INFO=OFF
    cmake --build $BUILD_DIR --target kyty_emulator --parallel"

log "Packing"
stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT
mkdir -p "$stage/kytyps5" "$OUT"
cp "$SRC/$BUILD_DIR/kyty_emulator" "$stage/kytyps5/"
strip "$stage/kytyps5/kyty_emulator"
cp -a "$SRC/$BUILD_DIR/assets" "$stage/kytyps5/"
cp "$SRC/LICENSE" "$stage/kytyps5/LICENSE"
{
    printf 'KytyPS5 %s, built for -march=btver2\n' "$version"
    printf 'Source: %s at %s with these patches from PS5 on PS4:\n' "$KYTY_URL" "$KYTY_COMMIT"
    (cd "$PATCHES" && ls ./*.patch | sed 's|^\./|  |')
} > "$stage/kytyps5/VERSION"
cp -a "$PATCHES" "$stage/kytyps5/patches"
tar -C "$stage" --owner=0 --group=0 --numeric-owner -cJf "$OUT/kytyps5-ps4.tar.xz" kytyps5
ok "KytyPS5: $OUT/kytyps5-ps4.tar.xz ($(du -h "$OUT/kytyps5-ps4.tar.xz" | cut -f1)), $version"
