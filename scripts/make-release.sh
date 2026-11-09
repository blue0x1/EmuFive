#!/usr/bin/env bash
# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
# Makes an EmuFive update pack for a GitHub release (the PS4 installs it from Settings, System,
# Software update; see overlay/opt/ps5-on-ps4/lib/ps5/update.py):
#
#   scripts/make-release.sh VERSION [--since REF] [--kyty FILE] [--post FILE]
#                           [--restart | --no-restart]
#
# The pack has the overlay files changed since the last release (the newest version tag, 1.0.0 or v1.0.0, or REF),
# the ones removed since, and with --kyty a new emulator (out/kytyps5-ps4.tar.xz from
# scripts/build-kyty.sh). --post adds a script run as root on the PS4 after the files are in.
# The PS4 asks to restart after it when files outside /opt/ps5-on-ps4 (or the session, the PS
# button menu and the Bluetooth services) changed; --restart / --no-restart say it instead.
#
# Before: set overlay/etc/ps5-on-ps4-version to VERSION and commit. The pack is made from the
# committed files. Out: out/release/VERSION/ with the pack, its SHA-256 and notes.md.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
log() { printf '\033[1;34m[*]\033[0m %s\n' "$*"; }
ok()  { printf '\033[1;32m[+]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[-]\033[0m %s\n' "$*" >&2; exit 1; }

VERSION="${1:-}"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "usage: $0 VERSION (like 1.0.1) [--since REF] [--kyty FILE] [--post FILE] [--restart|--no-restart]"
shift
SINCE="" KYTY="" POST="" RESTART=auto
while [ $# -gt 0 ]; do
    case "$1" in
        --since) SINCE="${2:?}"; shift 2 ;;
        --kyty) KYTY="$(realpath "${2:?}")"; shift 2 ;;
        --post) POST="$(realpath "${2:?}")"; shift 2 ;;
        --restart) RESTART=yes; shift ;;
        --no-restart) RESTART=no; shift ;;
        *) die "Unknown option: $1" ;;
    esac
done

cd "$ROOT"
[ "$(head -n 1 overlay/etc/ps5-on-ps4-version)" = "$VERSION" ] \
    || die "overlay/etc/ps5-on-ps4-version says $(head -n 1 overlay/etc/ps5-on-ps4-version): set it to $VERSION and commit."
[ -z "$(git status --porcelain -- overlay)" ] || die "overlay/ has changes that are not committed. Commit them first."
if [ -z "$SINCE" ]; then
    # The newest version tag, with or without a v (GitHub releases are tagged 1.0.0).
    SINCE="$(git tag -l | grep -E '^v?[0-9]+\.[0-9]+\.[0-9]+$' | awk '{v = $0; sub(/^v/, "", v); print v " " $0}' \
        | sort -V -k1,1 | tail -n 1 | cut -d' ' -f2)"
    [ -n "$SINCE" ] || die "No release tag yet. Tag the commit of the last release first (git tag 1.0.0 COMMIT), or give --since."
    [ "${SINCE#v}" != "$VERSION" ] || die "$SINCE is already tagged. Make the release before tagging it."
fi
git rev-parse -q --verify "$SINCE^{commit}" > /dev/null || die "Not a commit or tag: $SINCE"
[ -z "$KYTY" ] || [ -f "$KYTY" ] || die "No emulator archive: $KYTY"
[ -z "$POST" ] || [ -f "$POST" ] || die "No post script: $POST"

mapfile -t CHANGED < <(git diff --name-only --no-renames --diff-filter=d "$SINCE" HEAD -- overlay | sed 's|^overlay/||')
mapfile -t REMOVED < <(git diff --name-only --no-renames --diff-filter=D "$SINCE" HEAD -- overlay | sed 's|^overlay/||')
[ ${#CHANGED[@]} -gt 0 ] || [ ${#REMOVED[@]} -gt 0 ] || [ -n "$KYTY" ] || [ -n "$POST" ] || die "Nothing changed since $SINCE."

if [ "$RESTART" = auto ]; then
    RESTART=no
    for f in "${CHANGED[@]}" "${REMOVED[@]}"; do
        case "$f" in
            opt/ps5-on-ps4/bin/ps5-session|opt/ps5-on-ps4/bin/ps5-guide|opt/ps5-on-ps4/bin/ps5-pad-pair|opt/ps5-on-ps4/bin/ps5-bt-watchdog) RESTART=yes ;;
            opt/ps5-on-ps4/*|etc/ps5-on-ps4-version) ;;
            *) RESTART=yes ;;
        esac
    done
fi

OUT="$ROOT/out/release/$VERSION"
PACK="emufive-$VERSION.tar"
stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT
rm -rf "$OUT"; mkdir -p "$OUT"

log "EmuFive $VERSION: changes since $SINCE"
if [ ${#CHANGED[@]} -gt 0 ]; then
    # The committed files (git archive), so nothing half-done from the working tree goes in.
    git archive --format=tar --prefix= HEAD:overlay "${CHANGED[@]}" > "$stage/committed.tar"
    mkdir "$stage/files"
    tar -xf "$stage/committed.tar" -C "$stage/files"
    (cd "$stage/files" && tar --owner=0 --group=0 --numeric-owner --mode=go-w --no-recursion -cf "$stage/files.tar" "${CHANGED[@]}")
    for f in "${CHANGED[@]}"; do echo "    $f"; done
fi
for f in "${REMOVED[@]}"; do echo "    removed: $f"; done
[ -z "$KYTY" ] || { cp "$KYTY" "$stage/kytyps5.tar.xz"; echo "    emulator: $(basename "$KYTY")"; }
[ -z "$POST" ] || { cp "$POST" "$stage/post.sh"; echo "    post script: $(basename "$POST")"; }

python3 - "$stage/update.json" "$VERSION" "$RESTART" "${REMOVED[@]}" <<'EOF'
import json, sys
path, version, restart, removed = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
with open(path, "w") as f:
    json.dump({"version": version, "restart": restart == "yes", "remove": removed}, f, indent=1)
EOF

parts=(update.json)
[ ${#CHANGED[@]} -eq 0 ] || parts+=(files.tar)
[ -z "$KYTY" ] || parts+=(kytyps5.tar.xz)
[ -z "$POST" ] || parts+=(post.sh)
tar --owner=0 --group=0 --numeric-owner -C "$stage" -cf "$OUT/$PACK" "${parts[@]}"
(cd "$OUT" && sha256sum "$PACK" > "$PACK.sha256")

{
    echo "EmuFive $VERSION"
    echo
    git log --no-merges --format='- %s' "$SINCE..HEAD"
    [ "$RESTART" = yes ] && { echo; echo "The PS4 restarts after this update (it asks first)."; }
} > "$OUT/notes.md"

ok "Made $OUT/$PACK ($(du -h "$OUT/$PACK" | cut -f1)), restart: $RESTART"
cat <<EOF

To publish it:
  1. git tag $VERSION && git push origin $VERSION
  2. On github.com/blue0x1/EmuFive, Releases, Draft a new release, tag $VERSION.
  3. Attach $PACK and $PACK.sha256 from $OUT.
  4. Paste notes.md as the description, and publish (not as a pre-release).
EOF
