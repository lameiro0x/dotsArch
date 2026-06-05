#!/usr/bin/env bash
# brightness.sh — Modulo de brillo para Waybar.
# Usa brightnessctl. Muestra un icono que cambia segun el nivel y el
# porcentaje actual en el tooltip. Si brightnessctl no esta disponible
# o no hay backlight, muestra un placeholder.

if ! command -v brightnessctl >/dev/null 2>&1; then
    jq -cn '{"text":"󰳲","tooltip":"Brillo no disponible","class":"unavailable"}'
    exit 0
fi

CUR=$(brightnessctl get 2>/dev/null)
MAX=$(brightnessctl max 2>/dev/null)

if [ -z "$CUR" ] || [ -z "$MAX" ] || [ "$MAX" -eq 0 ] 2>/dev/null; then
    jq -cn '{"text":"󰳲","tooltip":"Brillo no disponible","class":"unavailable"}'
    exit 0
fi

PCT=$(( CUR * 100 / MAX ))

# Icono segun nivel (Nerd Font weather/brightness glyphs).
if   [ "$PCT" -ge 80 ]; then ICON="󰃠"
elif [ "$PCT" -ge 50 ]; then ICON="󰃝"
elif [ "$PCT" -ge 20 ]; then ICON="󰃟"
else                         ICON="󰃞"
fi

jq -cn --arg i "$ICON" --argjson p "$PCT" \
    '{"text":$i,"tooltip":("Brillo: " + ($p|tostring) + "%"),"class":"brightness"}'
