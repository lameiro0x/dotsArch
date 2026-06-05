#!/usr/bin/env bash
# audio.sh — Volume module with automatic VM/laptop detection
# Uses wpctl (WirePlumber) when available, shows placeholder otherwise

VOL_RAW=$(wpctl get-volume @DEFAULT_AUDIO_SINK@ 2>/dev/null)

# No sink or error → show placeholder
if [ -z "$VOL_RAW" ] || echo "$VOL_RAW" | grep -qi "not found\|error\|invalid"; then
    jq -cn '{"text":"󰕿","tooltip":"Audio not available","class":"unavailable"}'
    exit 0
fi

# Parse "Volume: 0.75" or "Volume: 0.75 [MUTED]"
PCT=$(echo "$VOL_RAW" | awk '{printf "%d", $2 * 100}')
IS_MUTED=0
echo "$VOL_RAW" | grep -q "MUTED" && IS_MUTED=1

if [ "$IS_MUTED" = "1" ]; then
    jq -cn --argjson v "$PCT" \
        '{"text":"󰖁","tooltip":("Volume: " + ($v|tostring) + "% (muted)"),"class":"muted"}'
elif [ "${PCT:-0}" -ge 66 ]; then
    jq -cn --argjson v "$PCT" \
        '{"text":"󰕾","tooltip":("Volume: " + ($v|tostring) + "%"),"class":"high"}'
elif [ "${PCT:-0}" -ge 33 ]; then
    jq -cn --argjson v "$PCT" \
        '{"text":"󰖀","tooltip":("Volume: " + ($v|tostring) + "%"),"class":"medium"}'
else
    jq -cn --argjson v "$PCT" \
        '{"text":"󰕿","tooltip":("Volume: " + ($v|tostring) + "%"),"class":"low"}'
fi
