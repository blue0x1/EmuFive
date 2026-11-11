#!/bin/sh
# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
# Run as root on the PS4 by the 1.0.3 update (scripts/make-release.sh 1.0.3 --post this file):
# mounts the PS4 drive now with the fixed ps5-ps4-drive, so its games show up without a restart.
# Systems where it was already mounted are left as they are.
mountpoint -q /media/ps4-drive && exit 0
systemctl restart ps5-ps4-drive.service || true
