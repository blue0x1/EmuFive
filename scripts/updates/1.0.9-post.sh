#!/bin/sh
# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
# Run as root on the PS4 by the 1.0.9 update (scripts/make-release.sh 1.0.9 --post this file):
# installs ffmpeg for video clips (PS + Triangle, ps5-record) and playing them in Media. New
# installs have it in the image. If apt can't install it, the update still finishes: only video
# clips don't work until ffmpeg is installed (apt-get install ffmpeg).
command -v ffmpeg > /dev/null && command -v ffplay > /dev/null && exit 0
echo "Installing ffmpeg for video clips"
if apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ffmpeg; then
    status=installed
else
    status="could not be installed; video clips need it"
fi
apt-get clean
rm -rf /var/lib/apt/lists/*
echo "ffmpeg $status"
exit 0
