#!/bin/bash
# Install the shared SFX library from Google Drive if this machine does not have it yet.
# Usage: install-sfx.sh            -> installs to the default folder
#        SFX_DIR=/path install-sfx.sh
# Prints the SFX folder path on the last line.
set -euo pipefail

# Google Drive file ID of the zip (shared as "Anyone with the link").
# To publish a new SFX pack: upload the new zip, replace this ID.
SFX_FILE_ID="1z-7ckwoACdaH_ahoHJgYKVhE4W_wHlsa"

if [ -z "${SFX_DIR:-}" ]; then
  if [ -d "/Volumes/JamesM.2/Claude/Video" ]; then
    SFX_DIR="/Volumes/JamesM.2/Claude/Video/Free SFX"
  else
    SFX_DIR="$HOME/ReelAssets/Free SFX"
  fi
fi
MARKER="$SFX_DIR/.installed-$SFX_FILE_ID"

if [ -f "$MARKER" ]; then
  echo "SFX up to date"
  echo "$SFX_DIR"
  exit 0
fi

# A folder that already has audio but no marker at all was installed by hand: adopt it.
# An older pack's marker means the ID changed, so fall through and download the new pack.
if [ -d "$SFX_DIR" ] && ! ls "$SFX_DIR"/.installed-* >/dev/null 2>&1 && [ -n "$(find "$SFX_DIR" -type f \( -iname '*.wav' -o -iname '*.mp3' -o -iname '*.aif*' -o -iname '*.m4a' \) -print -quit)" ] \
   && [ "${SFX_FORCE:-0}" != "1" ]; then
  touch "$MARKER"
  echo "SFX already present, marked as installed"
  echo "$SFX_DIR"
  exit 0
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Downloading SFX pack from Google Drive..."
curl -fL --retry 3 -o "$TMP/sfx.zip" \
  "https://drive.usercontent.google.com/download?id=$SFX_FILE_ID&export=download&confirm=t"

if ! unzip -tq "$TMP/sfx.zip" >/dev/null 2>&1; then
  echo "Download is not a valid zip. Check that the Drive file is shared as 'Anyone with the link'." >&2
  exit 1
fi

mkdir -p "$TMP/x"
if command -v ditto >/dev/null; then ditto -x -k "$TMP/sfx.zip" "$TMP/x"; else unzip -q "$TMP/sfx.zip" -d "$TMP/x"; fi
rm -rf "$TMP/x/__MACOSX"

# Google Drive zips wrap everything in one top-level folder; unwrap it.
SRC="$TMP/x"
ENTRIES=("$SRC"/*)
if [ "${#ENTRIES[@]}" -eq 1 ] && [ -d "${ENTRIES[0]}" ]; then SRC="${ENTRIES[0]}"; fi

mkdir -p "$SFX_DIR"
# Overwrite same-named files with the new pack; files only in the local folder are kept.
cp -R "$SRC"/. "$SFX_DIR"/
rm -f "$SFX_DIR"/.installed-* "$SFX_DIR"/._.installed-*
touch "$MARKER"
echo "SFX installed"
echo "$SFX_DIR"
