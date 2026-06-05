#!/usr/bin/env bash
# Slider horizontal de brillo al clic en Waybar.
# Usa brightnessctl. Con yad muestra un mini-popup con barra horizontal.
# El minimo es 5% para no apagar la pantalla por completo.

# Toggle: si ya hay un popup abierto, cerrarlo.
if pgrep -f "brightness-slider" >/dev/null 2>&1; then
    pkill -f "brightness-slider"
    exit 0
fi

# Sin brightnessctl no hay nada que hacer.
command -v brightnessctl >/dev/null 2>&1 || exit 0

# Sin yad no se puede mostrar el slider grafico.
command -v yad >/dev/null 2>&1 || exit 0

# Porcentaje actual 0-100.
CUR=$(brightnessctl get 2>/dev/null)
MAX=$(brightnessctl max 2>/dev/null)
[ -z "$CUR" ] || [ -z "$MAX" ] || [ "$MAX" -eq 0 ] 2>/dev/null && exit 0
cur=$(( CUR * 100 / MAX ))

# yad --scale: barra horizontal; --print-partial emite el valor al arrastrar.
# --class permite identificar el proceso para el toggle (pkill -f).
yad --scale --class="brightness-slider" --title="Brillo" \
    --value="$cur" --min-value=5 --max-value=100 --step=1 --page=5 \
    --print-partial --no-buttons --undecorated --on-top --skip-taskbar \
    --width=340 --height=64 2>/dev/null | while read -r v; do
        [ -z "$v" ] && continue
        brightnessctl set "${v}%" >/dev/null 2>&1
    done
