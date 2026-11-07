#!/usr/bin/env bash
# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
# Builds out/ps5-ps4-rootfs.tar.xz, the PS5 on PS4 system for PS4 Multiboot.
#   scripts/build-kyty.sh && scripts/build-rootfs.sh
# PS4_MESA defaults to ../PS4-Multiboot/out/ps4-mesa.tar.xz (make mesa there),
# KYTY to out/kytyps5-ps4.tar.xz (scripts/build-kyty.sh).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"
OUT="$ROOT/out"
IMAGE=ps5-on-ps4-rootfs
NAME="PS5 on PS4"
ARCHIVE=ps5-ps4-rootfs.tar.xz
PS4_MESA="${PS4_MESA:-$ROOT/../PS4-Multiboot/out/ps4-mesa.tar.xz}"
KYTY="${KYTY:-$OUT/kytyps5-ps4.tar.xz}"

log() { printf '\033[1;34m[*]\033[0m %s\n' "$*"; }
ok()  { printf '\033[1;32m[+]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[-]\033[0m %s\n' "$*" >&2; exit 1; }

[ -f "$PS4_MESA" ] || die "No PS4 Mesa at $PS4_MESA (build it with 'make mesa' in PS4 Multiboot, or set PS4_MESA)"
[ -f "$KYTY" ] || die "No KytyPS5 at $KYTY (build it with scripts/build-kyty.sh, or set KYTY)"
mkdir -p "$BUILD/ctx" "$OUT"
cp "$PS4_MESA" "$BUILD/ctx/ps4-mesa.tar.xz"
cp "$KYTY" "$BUILD/ctx/kytyps5-ps4.tar.xz"

log "Building the $NAME image"
docker build -t "$IMAGE" -f "$ROOT/docker/rootfs.Dockerfile" "$ROOT"

log "Exporting the root filesystem"
cid="$(docker create "$IMAGE")"
trap 'docker rm -f "$cid" > /dev/null' EXIT
docker export "$cid" -o "$BUILD/rootfs.tar"

# Menu name and logo for PS4 Multiboot, first in the archive so the menu reads
# them without unpacking the rest.
rm -rf "$BUILD/meta"
mkdir -p "$BUILD/meta/etc/ps4-distro"
echo "$NAME" > "$BUILD/meta/etc/ps4-distro/name"
python3 "$ROOT/tools/logo-to-rgba.py" "$ROOT/assets/logo.png" "$BUILD/meta/etc/ps4-distro/logo.rgba"

log "Compressing"
docker run --rm -v "$BUILD:/build" -v "$OUT:/out" \
    -e HOST_UID="$(id -u)" -e HOST_GID="$(id -g)" -e ARCHIVE="$ARCHIVE" \
    "$IMAGE" bash -euo pipefail -c '
        r=/tmp/root
        mkdir -p "$r"
        tar -xpf /build/rootfs.tar -C "$r" --numeric-owner
        # docker export leaves its own versions of these.
        echo ps5-ps4 > "$r/etc/hostname"
        printf "127.0.0.1\tlocalhost\n127.0.1.1\tps5-ps4\n::1\t\tlocalhost ip6-localhost ip6-loopback\n" > "$r/etc/hosts"
        rm -f "$r/etc/resolv.conf" && : > "$r/etc/resolv.conf"
        rm -f "$r/.dockerenv"
        cp -a /build/meta /tmp/meta && chown -R 0:0 /tmp/meta
        apt-get -qq update > /dev/null 2>&1 || true
        command -v xz > /dev/null || { apt-get -qq install -y xz-utils > /dev/null 2>&1; }
        tar -cpf - --numeric-owner -C /tmp/meta --no-recursion ./etc --recursion ./etc/ps4-distro \
            -C "$r" . | xz -T0 -6 > "/out/$ARCHIVE"
        chown "$HOST_UID:$HOST_GID" "/out/$ARCHIVE"
    '
rm -f "$BUILD/rootfs.tar"
ok "$NAME: $OUT/$ARCHIVE ($(du -h "$OUT/$ARCHIVE" | cut -f1))"
