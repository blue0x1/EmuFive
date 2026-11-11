#!/bin/sh
# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
# Run as root on the PS4 by the 1.0.2 update (scripts/make-release.sh 1.0.2 --post this file):
# installs what Internet, the web browser, needs (WebKitGTK and video playback), about 110 MB to
# download. New installs have it in the image (docker/rootfs.Dockerfile).
set -e
PACKAGES="python3-gi python3-gi-cairo gir1.2-webkit2-4.1 gstreamer1.0-plugins-good gstreamer1.0-libav adwaita-icon-theme"
missing=""
for p in $PACKAGES; do
    dpkg-query -W -f='${Status}' "$p" 2>/dev/null | grep -q "install ok installed" || missing="$missing $p"
done
[ -n "$missing" ] || exit 0
export DEBIAN_FRONTEND=noninteractive
apt-get -q update
# shellcheck disable=SC2086
apt-get install -y -q --no-install-recommends $missing
apt-get clean
