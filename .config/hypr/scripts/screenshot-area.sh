#!/usr/bin/env bash
# Area screenshot: select zone → save file + copy to clipboard

SAVEDIR="$HOME/Pictures/Screenshots"
mkdir -p "$SAVEDIR"

FILE="$SAVEDIR/screenshot-$(date +%Y-%m-%d_%H-%M-%S).png"

SELECTION=$(slurp 2>/dev/null) || exit 0   # exit silently if user cancels

grim -g "$SELECTION" "$FILE" && wl-copy < "$FILE"
