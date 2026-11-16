#!/bin/sh
# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
# Run as root on the PS4 by the 1.0.7 update (scripts/make-release.sh 1.0.7 --post this file):
# installs the PS4 Mesa of PS4 Multiboot v1.5.0-beta-4, from /user/home when it was copied there,
# otherwise downloaded (about 45 MB). Its Vulkan
# driver draws correctly with all 4 GPU engines of the PS4 Pro on (the beta-4 linux-2048mb.bin);
# the older one hangs the GPU there. New installs have it in the image.
# The Mesa in use is kept in /opt/ps4-mesa.prev and put back if anything fails.
set -e
URL="https://github.com/blue0x1/ps4-multiboot/releases/download/v1.5.0-beta.4/ps4-mesa.tar.xz"
SHA256="8303213f51e8eb43c5f6f811e9f94beb4ad0ae3d7c4ef7d38d1a5286c5683076"
P=/opt/ps4-mesa
STAMP="$P/.release-sha256"

[ -d "$P" ] || exit 0                                    # No PS4 Mesa here: nothing to replace.
[ "$(cat "$STAMP" 2>/dev/null)" = "$SHA256" ] && exit 0  # Already this one.

work="$(mktemp -d /opt/.ps4-mesa-update.XXXXXX)"
trap 'rm -rf "$work"' EXIT
# The copy PS4 Multiboot installs from (/user/home on the PS4 drive), when it is this one;
# otherwise the download.
src="/media/ps4-drive/home/ps4-mesa.tar.xz"
if [ -f "$src" ] && echo "$SHA256  $src" | sha256sum -c --quiet > /dev/null 2>&1; then
    echo "Using the PS4 Mesa in /user/home on the PS4 drive"
else
    echo "Downloading the PS4 Mesa of PS4 Multiboot v1.5.0-beta-4"
    src="$work/ps4-mesa.tar.xz"
    curl -fsSL --retry 3 --connect-timeout 20 -o "$src" "$URL"
    echo "$SHA256  $src" | sha256sum -c --quiet
fi
tar -xJf "$src" -C "$work"
ls "$work$P"/lib/libgallium-*.so "$work$P"/lib/libvulkan_radeon.so > /dev/null
[ -e "$P/.bundled" ] && touch "$work$P/.bundled"
echo "$SHA256" > "$work$P/.release-sha256"

# Swap by renaming, so programs running now keep the files they opened.
rm -rf "$P.prev"
mv "$P" "$P.prev"
if ! mv "$work$P" "$P" || ! ldconfig; then
    rm -rf "$P"
    mv "$P.prev" "$P"
    ldconfig || true
    exit 1
fi
echo "PS4 Mesa updated (the one before is in $P.prev)"
