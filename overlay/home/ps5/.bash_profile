# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
# On tty1 (the automatic login), start X with the PS5 session. Other logins
# (tty2, SSH) get a normal shell.
[ -f ~/.bashrc ] && . ~/.bashrc
if [ -z "$DISPLAY" ] && [ "$(tty)" = /dev/tty1 ]; then
    exec startx /opt/ps5-on-ps4/bin/ps5-session -- :0 vt1 -nolisten tcp > ~/.ps5-session.log 2>&1
fi
