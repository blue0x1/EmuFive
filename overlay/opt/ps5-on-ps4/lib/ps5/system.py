# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
"""The system behind the home screen: games on the drives, Wi-Fi, the PC share, controllers,
sound, storage, saves, logs and the few things that need root (through ps5-admin)."""

import errno
import glob
import json
import os
import queue
import re
import shutil
import socket
import subprocess
import threading
import time

from . import store

USB_MOUNT = "/media/ps5-usb"
USB_GAMES = USB_MOUNT + "/PS5"
PS4_MOUNT = "/media/ps4-drive"
PS4_GAMES = PS4_MOUNT + "/home/PS5"
PS4_GAMES_SHOWN = "/user/home/PS5"     # The same folder, as the PS4 and GoldHEN FTP name it.
PC_SETTINGS = os.path.join(store.CONFIG_DIR, "pc-share.json")
PC_MOUNT = os.path.expanduser("~/.pc-share")   # smbnetfs: PC_MOUNT/<address>/<share>
DATA_DIR = os.path.expanduser("~/data")         # The games' /data (saves).
GAME_LOG = os.path.expanduser("~/kytyps5.log")
ADMIN = "/opt/ps5-on-ps4/bin/ps5-admin"
RUNTIME = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"


def run(args, timeout=20, root=False, text_input=None):
    """Runs a command: (exit code, output, errors). root: through sudo -n (allowed commands only)."""
    command = (["sudo", "-n"] if root else []) + list(args)
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=timeout,
                              input=text_input)
        return done.returncode, done.stdout, done.stderr
    except (OSError, subprocess.TimeoutExpired) as error:
        return 1, "", str(error)


def admin(*args, timeout=30):
    """ps5-admin, the root helper (sudoers allows it without a password)."""
    return run([ADMIN, *args], timeout=timeout, root=True)


# --------------------------------------------------------------------------------------------
# Games.

class Game:
    """A game folder (with eboot.bin and sce_sys) or a .zar dump. The pictures are loaded by the
    home screen; this is what can be read without pygame."""

    def __init__(self, path, source="USB", source_name="USB drive"):
        self.path = path
        self.source = source            # USB, PS4 or PC: the label on the tile.
        self.source_name = source_name  # Shown under the title.
        self.title = os.path.basename(path.rstrip("/"))
        self.title_id = ""
        self.version = ""
        sys_dir = os.path.join(path, "sce_sys")
        try:
            with open(os.path.join(sys_dir, "param.json"), encoding="utf-8") as f:
                param = json.load(f)
            names = param.get("localizedParameters", {})
            language = names.get("defaultLanguage", "en-US")
            name = (names.get(language) or names.get("en-US") or {}).get("titleName")
            if name:
                self.title = name.replace("™", "").replace("®", "").strip()
            self.title_id = param.get("titleId", "")
            self.version = param.get("contentVersion", "")
        except (OSError, ValueError, AttributeError):
            pass
        self.key = store.game_key(path, self.title_id)

    def subtitle(self):
        parts = [p for p in (self.title_id, "version " + self.version if self.version else "") if p]
        return "  ·  ".join(parts)


def find_games(folder):
    games = []
    try:
        entries = sorted(os.listdir(folder), key=str.lower)
    except OSError:
        return games
    for entry in entries:
        path = os.path.join(folder, entry)
        if os.path.isfile(os.path.join(path, "eboot.bin")) or (
                os.path.isfile(path) and entry.lower().endswith(".zar")):
            games.append(path)
    return games


# --------------------------------------------------------------------------------------------
# Wi-Fi through NetworkManager (nmcli). Changes go through sudo -n (sudoers allows nmcli), since
# the system has no polkit. Connected networks are remembered by NetworkManager.

def split_terse(line):
    fields, current, escaped = [], "", False
    for ch in line:
        if escaped:
            current += ch
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == ":":
            fields.append(current)
            current = ""
        else:
            current += ch
    fields.append(current)
    return fields


class Network:
    def __init__(self, dry_run):
        self.dry_run = dry_run
        self.lock = threading.Lock()
        self.ssid = ""          # Connected network.
        self.state = "unknown"  # connected, connecting, disconnected, unavailable.
        self.ethernet = "unavailable"
        self.networks = []      # [(ssid, signal, secured, in_use)]
        self.saved_names = set()
        self.scanning = False
        self.results = queue.Queue()
        self.manual = False         # A connection the user started is under way.
        self.disconnected_since = None
        self.last_auto = 0.0
        threading.Thread(target=self._watch, daemon=True).start()

    def _nmcli(self, args, timeout=45, root=False):
        return run(["nmcli"] + args, timeout=timeout, root=root and not self.dry_run)

    def _watch(self):
        while True:
            code, out, _ = self._nmcli(["-t", "-f", "TYPE,STATE,CONNECTION", "device"], timeout=10)
            state, ssid, ethernet = "unavailable", "", "unavailable"
            if code == 0:
                for line in out.splitlines():
                    kind, device_state, connection = (split_terse(line) + ["", "", ""])[:3]
                    if kind == "wifi":
                        if device_state.startswith("connected"):
                            state, ssid = "connected", connection
                        elif device_state.startswith("connecting"):
                            state, ssid = "connecting", connection
                        elif state == "unavailable":
                            state = "disconnected" if device_state != "unavailable" else "unavailable"
                    elif kind == "ethernet":
                        if device_state.startswith("connected"):
                            ethernet = "connected"
                        elif ethernet != "connected":
                            ethernet = "disconnected" if device_state != "unavailable" else "unavailable"
            saved = self.saved()
            with self.lock:
                self.state, self.ssid, self.ethernet = state, ssid, ethernet
                self.saved_names = saved
            self._auto_connect(state, ethernet, saved)
            time.sleep(4)

    def _auto_connect(self, state, ethernet, saved):
        """NetworkManager joins saved networks by itself; this is the backup. When Wi-Fi stays
        disconnected for 10 seconds and a saved network is in range, join the strongest one
        (again every 20 seconds while it does not work)."""
        now = time.monotonic()
        if state != "disconnected" or ethernet == "connected" or not saved or self.manual or self.dry_run:
            self.disconnected_since = None
            return
        if self.disconnected_since is None:
            self.disconnected_since = now
        if now - self.disconnected_since < 10 or now - self.last_auto < 20:
            return
        self.last_auto = now
        code, out, _ = self._nmcli(["-t", "-f", "SSID,SIGNAL", "device", "wifi", "list", "--rescan", "auto"],
                                   timeout=20)
        if code != 0:
            return
        best = None
        for line in out.splitlines():
            name, signal = (split_terse(line) + ["", ""])[:2]
            try:
                strength = int(signal)
            except ValueError:
                strength = 0
            if name in saved and (best is None or strength > best[1]):
                best = (name, strength)
        if best is not None:
            self._nmcli(["--wait", "30", "connection", "up", "id", best[0]], timeout=40, root=True)

    def online(self):
        with self.lock:
            return self.state == "connected" or self.ethernet == "connected"

    def scan(self):
        if self.scanning:
            return
        self.scanning = True

        def work():
            if not self.dry_run:
                self._nmcli(["device", "wifi", "rescan"], timeout=15, root=True)
                time.sleep(2.5)
            code, out, _ = self._nmcli(
                ["-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "device", "wifi", "list", "--rescan", "no"],
                timeout=20)
            best = {}
            if code == 0:
                for line in out.splitlines():
                    in_use, ssid, signal, security = (split_terse(line) + ["", "", "", ""])[:4]
                    if not ssid:
                        continue
                    try:
                        strength = int(signal)
                    except ValueError:
                        strength = 0
                    secured = security not in ("", "--")
                    entry = (ssid, strength, secured, in_use.strip() == "*")
                    if ssid not in best or entry[3] or strength > best[ssid][1]:
                        best[ssid] = entry
            with self.lock:
                self.networks = sorted(best.values(), key=lambda n: (not n[3], -n[1]))
            self.scanning = False

        threading.Thread(target=work, daemon=True).start()

    def saved(self):
        code, out, _ = self._nmcli(["-t", "-f", "NAME,TYPE", "connection", "show"], timeout=10)
        names = set()
        if code == 0:
            for line in out.splitlines():
                name, kind = (split_terse(line) + ["", ""])[:2]
                if "wireless" in kind:
                    names.add(name)
        return names

    def is_saved(self, ssid):
        with self.lock:
            return ssid in self.saved_names

    def forget(self, ssid):
        code, _, err = self._nmcli(["connection", "delete", "id", ssid], timeout=15, root=True)
        with self.lock:
            self.saved_names.discard(ssid)
        return code == 0, err.strip()

    def connect(self, ssid, password):
        """Connects in the background; the result arrives in self.results as (ok, message)."""

        def work():
            self.manual = True
            try:
                connect()
            finally:
                self.manual = False

        def connect():
            if self.dry_run:
                time.sleep(2)
                ok = not password or not password.startswith("wrong")
                self.results.put((ok, f"Connected to {ssid}" if ok else "Wrong password. Try again."))
                return
            known = ssid in self.saved()
            if known and password is None:
                code, _, err = self._nmcli(["--wait", "40", "connection", "up", "id", ssid], root=True)
            else:
                args = ["--wait", "40", "device", "wifi", "connect", ssid]
                if password:
                    args += ["password", password]
                code, _, err = self._nmcli(args, timeout=60, root=True)
            if code == 0:
                self.results.put((True, f"Connected to {ssid}"))
                return
            if not known:
                # Do not keep a profile with a wrong password.
                self._nmcli(["connection", "delete", "id", ssid], timeout=15, root=True)
            text = err.strip().splitlines()[-1] if err.strip() else "Could not connect."
            if "Secrets were required" in text or "psk" in text.lower() or "password" in text.lower():
                text = "Wrong password. Try again."
            elif "No network with SSID" in text:
                text = f"{ssid} is out of range."
            else:
                text = text.replace("Error: ", "")
            self.results.put((False, text))

        threading.Thread(target=work, daemon=True).start()


def ip_addresses():
    """[(interface, address)] for the network interfaces that have an IPv4 address."""
    code, out, _ = run(["ip", "-4", "-o", "addr", "show"], timeout=5)
    found = []
    if code == 0:
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 4 and parts[1].startswith(("mlan", "wl", "eth", "en")):
                found.append((parts[1], parts[3].split("/")[0]))
    return found


# --------------------------------------------------------------------------------------------
# Games from a PC: a shared folder on Windows or Linux (Samba), opened with smbnetfs (FUSE, since
# the PS4 kernel has no SMB client). A blank username means a guest share.

def clean_address(text):
    text = text.strip()
    for prefix in ("smb://", "\\\\", "//"):
        if text.lower().startswith(prefix):
            text = text[len(prefix):]
    return text.strip("\\/ ")


def clean_share(text):
    return "/".join(part for part in text.replace("\\", "/").split("/") if part.strip())


def smb_quote(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


class PcShare:
    def __init__(self, test_dir=None):
        self.test_dir = test_dir      # For testing: a folder that stands for the mounted share.
        self.mount = test_dir or PC_MOUNT
        self.lock = threading.Lock()
        self.settings = {"enabled": False, "address": "", "share": "", "user": "", "password": ""}
        saved = store.read_json(PC_SETTINGS)
        for key in self.settings:
            if isinstance(saved.get(key), type(self.settings[key])):
                self.settings[key] = saved[key]
        self.state = "off"      # off, connecting, connected, error
        self.message = ""
        self.games = []         # Game objects, made here (reading param.json over the network).
        self.restart = False
        self.wake = threading.Event()
        threading.Thread(target=self._loop, daemon=True).start()

    def get(self):
        with self.lock:
            return dict(self.settings)

    def status(self):
        with self.lock:
            return self.state, self.message, len(self.games)

    def save(self, **changes):
        with self.lock:
            self.settings.update(changes)
            settings = dict(self.settings)
        try:
            store.write_private(PC_SETTINGS, json.dumps(settings, indent=2) + "\n")
        except OSError:
            pass

    def connect(self):
        """Uses the saved settings now: connects, or disconnects when turned off."""
        with self.lock:
            self.restart = True
            if self.settings["enabled"]:
                self.state, self.message = "connecting", ""
        self.wake.set()

    def label(self):
        s = self.get()
        share = clean_share(s["share"]).replace("/", "\\")
        return f"PC  {clean_address(s['address'])}\\{share}"

    def _set(self, state, message="", games=None):
        with self.lock:
            self.state, self.message = state, message
            if games is not None:
                self.games = games

    def _mounted(self):
        return self.test_dir is not None or os.path.ismount(self.mount)

    def _unmount(self):
        if self.test_dir is None and os.path.ismount(self.mount):
            run(["fusermount", "-u", "-z", self.mount], timeout=20)

    def _mount(self, s):
        if self.test_dir is not None:
            return None
        self._unmount()
        user = s["user"].strip().replace("\\", "/")
        auth = f"auth {smb_quote(clean_address(s['address']))} {smb_quote(user)} {smb_quote(s['password'])}" \
            if user else 'auth "guest" ""'
        smb_dir = os.path.expanduser("~/.smb")
        store.write_private(os.path.join(smb_dir, "smbnetfs.conf"),
                            'smb_query_browsers "false"\nsmb_timeout 10000\n' + auth + "\n")
        if not os.path.exists(os.path.join(smb_dir, "smb.conf")):
            store.write_private(os.path.join(smb_dir, "smb.conf"), "")
        os.makedirs(self.mount, exist_ok=True)
        try:
            done = subprocess.run(["smbnetfs", self.mount, "-o", "ro"], capture_output=True, text=True,
                                  timeout=30, start_new_session=True)
        except (OSError, subprocess.TimeoutExpired) as error:
            return f"Could not start smbnetfs: {error}"
        if done.returncode != 0 or not os.path.ismount(self.mount):
            return "Could not open network shares: " + (done.stderr.strip().splitlines() or ["smbnetfs failed"])[-1]
        return None

    def _list(self, s):
        address, share = clean_address(s["address"]), clean_share(s["share"])
        folder = os.path.join(self.mount, address, *share.split("/"))
        label = self.label()
        try:
            os.listdir(folder)
        except OSError as error:
            if error.errno == errno.EACCES:
                return ("This share needs a username and password." if not s["user"].strip()
                        else "Wrong username or password."), []
            if error.errno == errno.ENOENT:
                return f"{address} has no shared folder named {share}.", []
            return f"Cannot reach {address}. Check the address, and that the PC is on and sharing.", []
        paths = find_games(folder) + find_games(os.path.join(folder, "PS5"))
        if os.path.isfile(os.path.join(folder, "eboot.bin")):
            paths.insert(0, folder)     # The share itself is a game folder.
        with self.lock:
            known = {g.path: g for g in self.games}
        return None, [known.get(p) or Game(p, "PC", label) for p in paths]

    def _loop(self):
        while True:
            with self.lock:
                restart, self.restart = self.restart, False
                s = dict(self.settings)
            if not s["enabled"]:
                if restart:
                    self._unmount()
                self._set("off", "", [])
            elif not clean_address(s["address"]) or not clean_share(s["share"]):
                self._set("error", "Type the PC address and the shared folder name.", [])
            else:
                error = None
                if restart or not self._mounted():
                    self._set("connecting", "")
                    error = self._mount(s)
                if error is None:
                    error, games = self._list(s)
                    if error is None:
                        self._set("connected", "", games)
                    else:
                        self._set("error", error, [])
                else:
                    self._set("error", error, [])
            self.wake.wait(6)
            self.wake.clear()


# --------------------------------------------------------------------------------------------
# Controllers: connected ones with their battery (the kernel's power supply entries), and the
# Bluetooth ones that are paired.

def controllers():
    """[{name, connection, battery, charging, mac}] for the PlayStation controllers connected now."""
    found = []
    for supply in sorted(glob.glob("/sys/class/power_supply/ps-controller-battery-*")):
        mac = supply.rsplit("-", 1)[-1].upper()
        try:
            device = os.path.realpath(os.path.join(supply, "device"))
        except OSError:
            device = ""
        # The HID device is named BUS:VENDOR:PRODUCT.N; bus 0005 is Bluetooth, 0003 USB.
        bus = os.path.basename(device).split(":")[0].upper()
        connection = "Bluetooth" if bus == "0005" or "bluetooth" in device else "USB cable"

        def read(name):
            try:
                with open(os.path.join(supply, name)) as f:
                    return f.read().strip()
            except OSError:
                return ""

        try:
            battery = int(read("capacity"))
        except ValueError:
            battery = None
        status = read("status")
        name = "DualSense" if os.path.exists(os.path.join(device, "..", "..", "dualsense")) else "DualShock 4"
        try:
            with open(os.path.join(device, "uevent")) as f:
                uevent = f.read()
            if "0CE6" in uevent.upper() or "0DF2" in uevent.upper():
                name = "DualSense"
        except OSError:
            pass
        found.append({"name": name, "connection": connection, "battery": battery,
                      "charging": status in ("Charging", "Full"), "mac": mac})
    return found


def paired_controllers():
    """[(mac, name, connected)] for paired Bluetooth controllers."""
    code, out, _ = run(["bluetoothctl", "devices", "Paired"], timeout=8)
    result = []
    if code != 0:
        return result
    for line in out.splitlines():
        parts = line.split(" ", 2)
        if len(parts) == 3 and parts[0] == "Device" and "Controller" in parts[2]:
            _, info, _ = run(["bluetoothctl", "info", parts[1]], timeout=8)
            result.append((parts[1], parts[2], "Connected: yes" in info))
    return result


# --------------------------------------------------------------------------------------------
# Sound through PipeWire (wpctl).

def _wpctl(args, timeout=8):
    env_args = ["env", f"XDG_RUNTIME_DIR={RUNTIME}", "wpctl"] + args
    return run(env_args, timeout=timeout)


def _sinks(names=False):
    """{id: (text, is_default)} from wpctl status (node names with names=True)."""
    code, out, _ = _wpctl(["status", "-n"] if names else ["status"])
    sinks = {}
    if code != 0:
        return sinks
    section = False
    for line in out.splitlines():
        if "Sinks:" in line:
            section = True
            continue
        if section and ("Sources:" in line or "Filters:" in line or "Streams:" in line):
            break
        if section:
            m = re.search(r"(\*)?\s*(\d+)\.\s+(.*?)(\s+\[vol:.*\])?$", line)
            if m:
                sinks[int(m.group(2))] = (m.group(3).strip(), bool(m.group(1)))
    return sinks


def controller_microphones():
    """PipeWire IDs of the controllers' microphones (a DualShock 4 or DualSense on a USB cable;
    Linux has no controller sound over Bluetooth)."""
    code, out, _ = _wpctl(["status", "-n"])
    found, section = [], False
    for line in out.splitlines() if code == 0 else []:
        if "Sources:" in line:
            section = True
            continue
        if section and ("Filters:" in line or "Streams:" in line or "Sinks:" in line or "Video" in line):
            section = False
            continue
        if section:
            m = re.search(r"(\d+)\.\s+(\S+)", line)
            if m and re.search(r"sony|054c|wireless.controller|dualsense|dualshock", m.group(2), re.I):
                found.append(int(m.group(1)))
    return found


def set_controller_mic(on):
    """Mutes or unmutes the controllers' microphones. Returns how many there are."""
    ids = controller_microphones()
    for node in ids:
        _wpctl(["set-mute", str(node), "0" if on else "1"])
    return len(ids)


def sound_outputs():
    """[(id, name, is_default)] for the sound outputs (sinks)."""
    described = _sinks()
    names = _sinks(names=True)
    outputs = []
    for node, (text, default) in described.items():
        node_name = names.get(node, ("", False))[0]
        if node_name.startswith("bluez_output") or "bluez" in node_name:
            text = "Headphones: " + text
        elif "HDMI" in text or "hdmi" in node_name:
            text = "TV (HDMI)"
        elif "DualShock" in text or "Wireless Controller" in text or "DualSense" in text:
            text = "Controller headphones"
        outputs.append((node, text, default))
    return outputs


def bluetooth_sink():
    """The id of a Bluetooth headphones output, or None."""
    for node, (name, _) in _sinks(names=True).items():
        if name.startswith("bluez_output"):
            return node
    return None


def set_sound_output(node_id):
    _wpctl(["set-default", str(node_id)])
    _wpctl(["set-mute", str(node_id), "0"])


def sound_volume():
    code, out, _ = _wpctl(["get-volume", "@DEFAULT_AUDIO_SINK@"])
    m = re.search(r"Volume:\s*([\d.]+)", out) if code == 0 else None
    return int(round(float(m.group(1)) * 100)) if m else None


def set_sound_volume(percent):
    percent = max(0, min(100, percent))
    _wpctl(["set-volume", "@DEFAULT_AUDIO_SINK@", f"{percent / 100:.2f}"])
    _wpctl(["set-mute", "@DEFAULT_AUDIO_SINK@", "0"])


# --------------------------------------------------------------------------------------------
# Bluetooth headphones (BlueZ through bluetoothctl; PipeWire's Bluetooth plugin plays to them).
# Pairing questions are answered by the agent that ps5-pad-pair keeps registered.

def _bt(args, timeout=15):
    return run(["bluetoothctl"] + args, timeout=timeout)


def _bt_info(mac):
    code, out, _ = _bt(["info", mac], timeout=8)
    info = {"mac": mac, "name": mac, "paired": False, "connected": False, "audio": False}
    if code != 0:
        return info
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("Name:"):
            info["name"] = line.split(":", 1)[1].strip()
        elif line.startswith("Paired:"):
            info["paired"] = line.endswith("yes")
        elif line.startswith("Connected:"):
            info["connected"] = line.endswith("yes")
        elif line.startswith("Icon:") and "audio" in line:
            info["audio"] = True
        elif line.startswith("UUID:") and ("Audio Sink" in line or "Headset" in line or "Handsfree" in line):
            info["audio"] = True
    return info


def headphones(paired_only=True):
    """[{mac, name, paired, connected}] for Bluetooth audio devices (paired ones, or all known)."""
    code, out, _ = _bt(["devices"] + (["Paired"] if paired_only else []), timeout=8)
    found = []
    if code != 0:
        return found
    for line in out.splitlines():
        parts = line.split(" ", 2)
        if len(parts) >= 2 and parts[0] == "Device":
            info = _bt_info(parts[1])
            if info["audio"] and "Controller" not in info["name"]:
                found.append(info)
    return found


def find_headphones(seconds=12):
    """Looks for headphones in pairing mode; returns the ones not paired yet."""
    _bt(["power", "on"], timeout=8)
    _bt(["--timeout", str(seconds), "scan", "on"], timeout=seconds + 10)
    return [d for d in headphones(paired_only=False) if not d["paired"]]


def _use_headphones():
    """Sound goes to the headphones once their output shows up (a few seconds after connecting)."""
    for _ in range(20):
        node = bluetooth_sink()
        if node is not None:
            set_sound_output(node)
            return True
        time.sleep(0.5)
    return False


def pair_headphones(mac):
    _bt(["trust", mac])
    code, out, err = _bt(["pair", mac], timeout=40)
    if code != 0 and "AlreadyExists" not in out + err:
        return False, "Could not pair. Put the headphones in pairing mode and try again."
    return connect_headphones(mac)


def connect_headphones(mac):
    code, out, err = _bt(["connect", mac], timeout=30)
    if code != 0 or "Failed" in out:
        return False, "Could not connect. Turn the headphones on and try again."
    if _use_headphones():
        return True, "Headphones connected. The sound plays there now."
    return True, "Headphones connected, but no sound output came up for them yet."


def disconnect_headphones(mac):
    code, _, _ = _bt(["disconnect", mac], timeout=20)
    return code == 0, "Headphones disconnected. The sound plays on the TV again." if code == 0 else \
        "Could not disconnect them."


def forget_headphones(mac):
    code, _, _ = _bt(["remove", mac], timeout=20)
    return code == 0, "Headphones forgotten." if code == 0 else "Could not forget them."


# --------------------------------------------------------------------------------------------
# Storage.

def space(path):
    """(free bytes, total bytes) or None."""
    try:
        st = os.statvfs(path)
    except OSError:
        return None
    return st.f_bavail * st.f_frsize, st.f_blocks * st.f_frsize


def mounted(path):
    try:
        with open("/proc/mounts") as f:
            return any(line.split()[1] == path for line in f if len(line.split()) > 1)
    except OSError:
        return False


def usb_label():
    try:
        with open("/proc/mounts") as f:
            for line in f:
                parts = line.split()
                if len(parts) > 1 and parts[1] == USB_MOUNT:
                    code, out, _ = run(["lsblk", "-no", "LABEL", parts[0]], timeout=5)
                    return out.strip() or os.path.basename(parts[0])
    except OSError:
        pass
    return ""


def size_text(n):
    for unit, scale in (("TB", 1000 ** 4), ("GB", 1000 ** 3), ("MB", 1000 ** 2)):
        if n >= scale:
            value = n / scale
            return f"{value:.1f} {unit}" if value < 10 else f"{value:.0f} {unit}"
    return f"{n // 1000} KB"


# --------------------------------------------------------------------------------------------
# Saves: ~/data copied to the USB drive (PS5-saves/<date>) and back.

SAVES_DIR = USB_MOUNT + "/PS5-saves"


def save_backups():
    try:
        names = sorted((n for n in os.listdir(SAVES_DIR) if os.path.isdir(os.path.join(SAVES_DIR, n))),
                       reverse=True)
    except OSError:
        names = []
    return names


def backup_saves():
    if not mounted(USB_MOUNT):
        return False, "Plug in a USB drive first."
    name = time.strftime("%Y-%m-%d %H.%M.%S")
    target = os.path.join(SAVES_DIR, name)
    try:
        os.makedirs(SAVES_DIR, exist_ok=True)
        os.makedirs(DATA_DIR, exist_ok=True)
        shutil.copytree(DATA_DIR, target)
    except (OSError, shutil.Error) as error:
        return False, f"Backup failed: {error}"
    return True, f"Saves backed up to PS5-saves/{name} on the USB drive."


def restore_saves(name):
    source = os.path.join(SAVES_DIR, name)
    if not os.path.isdir(source):
        return False, "That backup is not on the USB drive any more."
    before = DATA_DIR + ".before-restore"
    try:
        if os.path.isdir(before):
            shutil.rmtree(before)
        if os.path.isdir(DATA_DIR):
            os.rename(DATA_DIR, before)
        shutil.copytree(source, DATA_DIR)
    except (OSError, shutil.Error) as error:
        if not os.path.isdir(DATA_DIR) and os.path.isdir(before):
            os.rename(before, DATA_DIR)
        return False, f"Restore failed: {error}"
    return True, f"Saves restored from {name}. The ones before are in ~/data.before-restore."


# --------------------------------------------------------------------------------------------
# Logs.

def read_log(lines=400):
    try:
        with open(GAME_LOG, encoding="utf-8", errors="replace") as f:
            return f.read().splitlines()[-lines:]
    except OSError:
        return []


def copy_logs_to_usb():
    if not mounted(USB_MOUNT):
        return False, "Plug in a USB drive first."
    target = os.path.join(USB_MOUNT, "PS5-logs", time.strftime("%Y-%m-%d %H.%M.%S"))
    copied = 0
    try:
        os.makedirs(target, exist_ok=True)
        for path in (GAME_LOG, GAME_LOG + ".1", os.path.expanduser("~/.ps5-session.log")):
            if os.path.isfile(path):
                shutil.copy(path, target)
                copied += 1
    except OSError as error:
        return False, f"Copy failed: {error}"
    return True, f"{copied} log files copied to PS5-logs on the USB drive."


# --------------------------------------------------------------------------------------------
# System information.

def read_first(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.readline().strip()
    except OSError:
        return ""


def system_info():
    info = []
    model = "PS4"
    try:
        with open("/proc/cpuinfo") as f:
            cpu = f.read()
        cores = cpu.count("processor\t:")
    except OSError:
        cores = 0
    gpu = ""
    for path in glob.glob("/sys/class/drm/card*/device/device"):
        gpu = read_first(path).lower()
        break
    if gpu in ("0x9923",):
        model = "PS4 Pro"
    elif gpu:
        model = "PS4"
    info.append(("Console", model + (f", {cores} CPU cores" if cores else "")))
    info.append(("KytyPS5", read_first("/opt/kytyps5/VERSION").replace("KytyPS5 ", "") or "unknown"))
    info.append(("PS5 on PS4", read_first("/etc/ps5-on-ps4-release") or "unknown"))
    info.append(("Linux", os.uname().release))
    addresses = ip_addresses()
    info.append(("IP address", ", ".join(a for _, a in addresses) or "not connected"))
    try:
        with open("/proc/uptime") as f:
            seconds = int(float(f.read().split()[0]))
        info.append(("Running for", f"{seconds // 3600} h {seconds % 3600 // 60} min"))
    except (OSError, ValueError):
        pass
    try:
        with open("/proc/meminfo") as f:
            mem = {line.split(":")[0]: int(line.split()[1]) for line in f if line.split()}
        info.append(("Memory", f"{mem.get('MemAvailable', 0) // 1024} MB free of {mem.get('MemTotal', 0) // 1024} MB"))
    except (OSError, ValueError, IndexError):
        pass
    info.append(("Host name", socket.gethostname()))
    return info


# --------------------------------------------------------------------------------------------
# Temperature, fan and CPU load.

_cpu_sample = [None]


def _read_int(path):
    try:
        with open(path) as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return None


def sensors():
    """{"console": °C, "cpu": °C, "fan": rpm, "load": percent} (each may be missing)."""
    found = {}
    for hwmon in glob.glob("/sys/class/hwmon/hwmon*"):
        name = read_first(os.path.join(hwmon, "name"))
        temp = _read_int(os.path.join(hwmon, "temp1_input"))
        if name == "ps4_fan":
            if temp is not None:
                found["console"] = temp / 1000
            fan = _read_int(os.path.join(hwmon, "fan1_input"))
            if fan is not None:
                found["fan"] = fan
        elif name == "k10temp" and temp is not None:
            found["cpu"] = temp / 1000
    try:
        with open("/proc/stat") as f:
            values = [int(v) for v in f.readline().split()[1:]]
        idle, total = values[3] + values[4], sum(values)
        before = _cpu_sample[0]
        _cpu_sample[0] = (idle, total)
        if before is not None and total > before[1]:
            found["load"] = int(round(100 * (1 - (idle - before[0]) / (total - before[1]))))
    except (OSError, ValueError, IndexError):
        pass
    return found


# --------------------------------------------------------------------------------------------
# Screenshots: PS5-screenshots on the USB drive, or ~/Screenshots without one.

LOCAL_SHOTS = os.path.expanduser("~/Screenshots")
USB_SHOTS = USB_MOUNT + "/PS5-screenshots"


def screenshot_dir():
    return USB_SHOTS if mounted(USB_MOUNT) else LOCAL_SHOTS


def screenshots():
    """Newest first: [path]."""
    found = []
    for folder in (USB_SHOTS, LOCAL_SHOTS):
        found += glob.glob(os.path.join(folder, "**", "*.png"), recursive=True)
    return sorted(found, key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0, reverse=True)


def delete_screenshot(path):
    try:
        os.remove(path)
        return True
    except OSError:
        return False


# --------------------------------------------------------------------------------------------
# Trophies: the names, details and icons are in the game's sce_sys/trophy2/trophyNN.ucp, and what
# was earned in KytyPS5's ~/.kytyps5/_Trophies/<title ID>/trophies_<user>_<NN>.json.

LOCALES = ["ja-JP", "en-US", "fr-FR", "es-ES", "de-DE", "it-IT", "nl-NL", "pt-PT", "ru-RU", "ko-KR",
           "zh-Hant", "zh-Hans", "fi-FI", "sv-SE", "da-DK", "no-NO", "pl-PL", "pt-BR", "en-GB", "tr-TR",
           "es-419", "ar-AE", "fr-CA", "cs-CZ", "hu-HU", "el-GR", "ro-RO", "th-TH", "vi-VN", "id-ID"]
TROPHY_GRADES = {"P": "platinum", "G": "gold", "S": "silver", "B": "bronze"}


def _ucp_files(path):
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 0x40 or int.from_bytes(data[:4], "big") != 0xb228c60a:
        return {}
    count, toc = int.from_bytes(data[0x10:0x14], "big"), int.from_bytes(data[0x14:0x18], "big")
    files = {}
    for i in range(min(count, 4096)):
        entry = toc + 0x20 + i * 0x40
        name = data[entry:entry + 0x20].split(b"\0")[0].decode(errors="replace")
        offset = int.from_bytes(data[entry + 0x20:entry + 0x28], "big")
        length = int.from_bytes(data[entry + 0x28:entry + 0x30], "big")
        files[name] = data[offset:offset + length]
    return files


def trophies(game_path, title_id, language=1, profile_id=store.FIRST_PROFILE):
    """(title, [trophy]) for a game, or (None, []) when it has none. A trophy is a dict: id, name,
    detail, grade, hidden, earned, when (a datetime or None) and icon (PNG bytes or None). Earned
    means earned by this profile."""
    import datetime
    folder = os.path.join(game_path, "sce_sys", "trophy2")
    packages = sorted(glob.glob(os.path.join(folder, "trophy*.ucp")))
    if not packages:
        return None, []
    earned = {}
    unlocks = os.path.join(store.work_dir(profile_id), "_Trophies", title_id)
    for unlock_file in glob.glob(os.path.join(unlocks, f"trophies_{profile_id}_*.json")):
        data = store.read_json(unlock_file)
        when = data.get("unlockedAt") if isinstance(data.get("unlockedAt"), dict) else {}
        for tid in data.get("unlockedTrophies", []):
            try:
                tick = int(when.get(str(tid), 0))
                stamp = datetime.datetime(1, 1, 1) + datetime.timedelta(microseconds=tick) if tick else None
            except (ValueError, OverflowError, TypeError):
                stamp = None
            earned[int(tid)] = stamp
    try:
        files = _ucp_files(packages[0])
        conf = json.loads(files["tropconf.json"])
    except (OSError, KeyError, ValueError):
        return None, []
    locale = LOCALES[language] if 0 <= language < len(LOCALES) else "en-US"
    meta_raw = files.get(f"tropmeta_{locale}.json") or files.get(f"tropmeta_{conf.get('defaultLanguage', 'en-US')}.json")
    try:
        meta = json.loads(meta_raw)["metadata"] if meta_raw else {}
    except (ValueError, KeyError):
        meta = {}
    texts = {}
    for item in meta.get("trophyMetadata", []):
        try:
            texts[int(item["id"])] = item
        except (KeyError, ValueError, TypeError):
            pass
    title = (meta.get("titleMetadata") or {}).get("name")
    result = []
    for item in conf.get("trophies", []):
        try:
            tid = int(item["id"])
        except (KeyError, ValueError, TypeError):
            continue
        text = texts.get(tid, {})
        result.append({"id": tid, "name": text.get("name", f"Trophy {tid}"), "detail": text.get("detail", ""),
                       "grade": TROPHY_GRADES.get(item.get("grade", "B"), "bronze"),
                       "hidden": bool(item.get("hidden")), "earned": tid in earned, "when": earned.get(tid),
                       "icon": files.get(f"trop{tid:04d}.png")})
    return title, result


def play_time_text(seconds):
    seconds = int(seconds or 0)
    if seconds < 60:
        return "less than a minute" if seconds else "not played yet"
    hours, minutes = seconds // 3600, seconds % 3600 // 60
    return f"{hours} h {minutes} min" if hours else f"{minutes} min"


# --------------------------------------------------------------------------------------------
# Settings: back up to the USB drive, or reset.

def backup_settings():
    if not mounted(USB_MOUNT):
        return False, "Plug in a USB drive first."
    target = os.path.join(USB_MOUNT, "PS5-settings", time.strftime("%Y-%m-%d %H.%M.%S"))
    try:
        shutil.copytree(store.CONFIG_DIR, target)
    except (OSError, shutil.Error) as error:
        return False, f"Backup failed: {error}"
    return True, f"Settings backed up to PS5-settings/{os.path.basename(target)} on the USB drive."


def reset_settings():
    """Settings and the PC share back to their defaults. Game saves, play time, favorites and
    Wi-Fi networks are kept."""
    for path in (store.SETTINGS_FILE, PC_SETTINGS, store.AVATAR_FILE, store.BACKGROUND_FILE):
        try:
            os.remove(path)
        except OSError:
            pass
    return True, "All settings are back to their defaults."


# --------------------------------------------------------------------------------------------
# Root things, through ps5-admin.

def ssh_enabled():
    code, out, _ = run(["systemctl", "is-enabled", "ssh"], timeout=8)
    return out.strip() == "enabled"


def set_ssh(on):
    code, out, err = admin("ssh", "on" if on else "off")
    return code == 0, (err or out).strip()


def timezones():
    code, out, _ = run(["timedatectl", "list-timezones"], timeout=10)
    zones = [z for z in out.splitlines() if z.strip()] if code == 0 else []
    return zones or ["UTC"]


def current_timezone():
    try:
        link = os.readlink("/etc/localtime")
        return link.split("zoneinfo/", 1)[1]
    except (OSError, IndexError):
        return "UTC"


def time_automatic():
    """True when the time comes from the internet (systemd-timesyncd)."""
    code, out, _ = run(["timedatectl", "show", "-p", "NTP", "--value"], timeout=5)
    return code != 0 or out.strip() == "yes"


def set_time_automatic(on):
    code, out, err = admin("ntp", "on" if on else "off")
    return code == 0, (err or out).strip()


def set_time(when):
    """Sets the date and time by hand: `when` is a datetime (local time)."""
    code, out, err = admin("settime", when.strftime("%Y-%m-%d %H:%M"))
    return code == 0, (err or out).strip()


def set_timezone(zone):
    code, out, err = admin("timezone", zone)
    if code == 0:
        os.environ["TZ"] = ":/usr/share/zoneinfo/" + zone
        time.tzset()
    return code == 0, (err or out).strip()


def eject_usb():
    code, out, err = admin("eject")
    return code == 0, (err or out).strip() or ("You can unplug the USB drive." if code == 0 else "")


def reboot():
    return admin("reboot")


def set_lightbar(rgb):
    """The light bar of the connected controllers (on the home screen; games get --controller-color)."""
    code, out, err = admin("lightbar", *[str(v) for v in rgb])
    return code == 0


def pair_mode():
    code, out, err = admin("pair")
    return code == 0


def forget_controller(mac):
    code, out, err = admin("forget", mac)
    return code == 0


def change_password(current, new):
    """Changes the ps5 user's password with passwd (it checks the current one). (ok, message)"""
    import pty
    import select
    pid, fd = pty.fork()
    if pid == 0:
        os.environ["LC_ALL"] = "C"
        try:
            os.execvp("passwd", ["passwd"])
        finally:
            os._exit(127)
    answers = [current, new, new]
    output = ""
    deadline = time.time() + 20
    try:
        while time.time() < deadline:
            ready, _, _ = select.select([fd], [], [], 0.5)
            if fd in ready:
                try:
                    chunk = os.read(fd, 1024).decode(errors="replace")
                except OSError:
                    break
                if not chunk:
                    break
                output += chunk
                if output.rstrip().lower().endswith("password:") and answers:
                    os.write(fd, (answers.pop(0) + "\n").encode())
                    output += "\n"
            elif not answers:
                pid_done, _ = os.waitpid(pid, os.WNOHANG)
                if pid_done:
                    pid = 0
                    break
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
    status = 1
    if pid:
        try:
            _, raw = os.waitpid(pid, 0)
            status = os.waitstatus_to_exitcode(raw)
        except ChildProcessError:
            pass
    else:
        status = 0 if "successfully" in output.lower() else 1
    if status == 0 or "successfully" in output.lower():
        return True, "Password changed. Use it for SSH and sudo."
    lower = output.lower()
    if "authentication token manipulation" in lower or "authentication failure" in lower:
        return False, "The current password is wrong."
    for hint in ("too short", "too simple", "palindrome", "same as", "too similar", "dictionary"):
        if hint in lower:
            return False, "The new password is too simple or too short. Try a longer one."
    lines = [l.strip() for l in output.splitlines() if l.strip() and "password" not in l.lower()]
    return False, lines[-1] if lines else "The password was not changed."


def password_is_default():
    """True while the ps5 user's password is still the published one (checked by ps5-admin)."""
    code, out, _ = admin("default-password", timeout=10)
    return code == 0 and out.strip() == "yes"
