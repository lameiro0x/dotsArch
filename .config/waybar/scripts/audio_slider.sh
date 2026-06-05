#!/usr/bin/env bash
# Slider horizontal de volumen al clic en Waybar.
# Usa wpctl (PipeWire/WirePlumber). Con yad muestra un mini-popup con barra
# horizontal; si yad no esta instalado, cae a pavucontrol.
# Arrastrar a 0 silencia (mute).
SINK="@DEFAULT_AUDIO_SINK@"

# Toggle: si ya hay un popup abierto, cerrarlo.
if pgrep -x yad >/dev/null 2>&1; then
    pkill -x yad
    exit 0
fi

# Sin yad -> mezclador grafico (tambien barra horizontal, arrastrar a 0 = mute).
if ! command -v yad >/dev/null 2>&1; then
    command -v pavucontrol >/dev/null 2>&1 && pavucontrol &
    exit 0
fi

# Volumen actual 0-100
cur=$(wpctl get-volume "$SINK" 2>/dev/null | awk '{printf "%d", $2 * 100}')
[ -z "$cur" ] && cur=0

# yad --scale: barra horizontal; --print-partial emite el valor mientras se arrastra.
yad --scale --class="vol-slider" --title="Volumen" \
    --value="$cur" --min-value=0 --max-value=100 --step=1 --page=5 \
    --print-partial --no-buttons --undecorated --on-top --skip-taskbar \
    --width=340 --height=64 2>/dev/null | while read -r v; do
        [ -z "$v" ] && continue
        wpctl set-volume "$SINK" "${v}%"
        if [ "$v" -le 0 ]; then
            wpctl set-mute "$SINK" 1
        else
            wpctl set-mute "$SINK" 0
        fi
    done
