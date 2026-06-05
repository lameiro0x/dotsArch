#!/usr/bin/env bash
# Waybar battery module — works on real laptop and VM (no battery)

BAT_PATH=""
for p in /sys/class/power_supply/BAT*; do
    [ -f "$p/capacity" ] && BAT_PATH="$p" && break
done

if [ -n "$BAT_PATH" ]; then
    capacity=$(cat "$BAT_PATH/capacity")
    status=$(cat "$BAT_PATH/status" 2>/dev/null || echo "Unknown")

    if [ "$status" = "Charging" ]; then
        icon="󰂄"                       # cargando
        css_class="charging"
        tooltip="Charging · ${capacity}%"
    elif [ "$capacity" -ge 90 ]; then
        icon="󰁹"                       # 100% / lleno
        css_class="full"
        tooltip="Battery · ${capacity}%"
    elif [ "$capacity" -ge 60 ]; then
        icon="󰂂"                       # alto
        css_class="good"
        tooltip="Battery · ${capacity}%"
    elif [ "$capacity" -ge 35 ]; then
        icon="󰁽"                       # medio
        css_class="good"
        tooltip="Battery · ${capacity}%"
    elif [ "$capacity" -ge 20 ]; then
        icon="󰁻"                       # bajo
        css_class="warning"
        tooltip="Battery · ${capacity}%  Low"
    else
        icon="󰁺"                       # crítico (<20%, rojo)
        css_class="critical"
        tooltip="Battery · ${capacity}%  Critical"
    fi

    # Add time remaining if available
    if [ -f "$BAT_PATH/time_to_empty_now" ]; then
        mins=$(cat "$BAT_PATH/time_to_empty_now" 2>/dev/null)
        if [ -n "$mins" ] && [ "$mins" -gt 0 ] 2>/dev/null; then
            h=$((mins / 60)); m=$((mins % 60))
            tooltip="$tooltip\n${h}h ${m}m remaining"
        fi
    fi

    printf '{"text": "%s", "tooltip": "%s", "class": "%s", "percentage": %s}\n' \
        "$icon" "$tooltip" "$css_class" "$capacity"
else
    # No battery — VM / desktop
    ac_online=0
    for ac in /sys/class/power_supply/AC* /sys/class/power_supply/ADP*; do
        [ -f "$ac/online" ] && ac_online=$(cat "$ac/online") && break
    done

    if [ "$ac_online" = "1" ]; then
        printf '{"text": "󰚥", "tooltip": "AC connected\nNo battery detected", "class": "ac"}\n'
    else
        printf '{"text": "󰚥", "tooltip": "No power supply detected", "class": "ac"}\n'
    fi
fi
