#!/usr/bin/env bash
# network.sh — Waybar custom network module
# Shows icon + rich tooltip with IP, VPN, speeds

# Find default route interface
IFACE=$(ip -4 route show default 2>/dev/null | awk 'NR==1{print $5}')

if [ -z "$IFACE" ]; then
    jq -n '{"text": "󰤭", "tooltip": "Disconnected", "class": "disconnected"}'
    exit 0
fi

# Detect wifi vs ethernet
IS_WIFI=0
[ -e "/sys/class/net/$IFACE/wireless" ] && IS_WIFI=1
[ -d "/sys/class/net/$IFACE/phy80211" ] && IS_WIFI=1
[ -f "/proc/net/wireless" ] && grep -q "^[[:space:]]*${IFACE}:" /proc/net/wireless && IS_WIFI=1

if [ "$IS_WIFI" = "1" ]; then
    ICON="󰤨"
    TYPE="Wi-Fi"
    # WiFi signal via /proc/net/wireless (quality 0-70, approximate)
    SIG_Q=$(awk -v if="${IFACE}:" '$1==if{gsub(/\./, "", $3); print int($3)}' /proc/net/wireless 2>/dev/null)
    if [ -n "$SIG_Q" ] && [ "$SIG_Q" -gt 0 ] 2>/dev/null; then
        SIG_PCT=$(awk -v q="$SIG_Q" 'BEGIN{p=int(q/70*100); if(p>100)p=100; print p}')
    fi
    # SSID via /proc/net/wireless or nmcli fallback
    SSID=$(nmcli -t -f active,ssid dev wifi 2>/dev/null | awk -F: '/^yes/{print $2}' | head -1)
    [ -z "$SSID" ] && SSID="unknown"
else
    ICON="󰈀"
    TYPE="Ethernet"
fi

# Local IP
IP=$(ip -4 addr show "$IFACE" 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1 | head -1)

# VPN detection (tun, wireguard, ppp, openvpn)
VPN_IP=""
for viface in tun0 tun1 wg0 wg1 ppp0 vpn0 utun0; do
    [ ! -e "/sys/class/net/$viface" ] && continue
    STATE=$(cat "/sys/class/net/$viface/operstate" 2>/dev/null)
    if [ "$STATE" = "up" ] || [ "$STATE" = "unknown" ]; then
        VPN_IP=$(ip -4 addr show "$viface" 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1 | head -1)
        [ -n "$VPN_IP" ] && break
    fi
done

# Network speed (sample /proc/net/dev over 0.5s)
read_rx_tx() {
    awk -v iface="$1:" '$1==iface{print $2+0, $10+0}' /proc/net/dev 2>/dev/null
}

SNAP1=$(read_rx_tx "$IFACE")
sleep 0.5
SNAP2=$(read_rx_tx "$IFACE")

format_speed() {
    awk -v a="${1:-0}" -v b="${2:-0}" 'BEGIN {
        d = (b - a) * 2
        if (d < 0) d = 0
        if      (d >= 1073741824) { printf "%.1f GB/s", d/1073741824 }
        else if (d >= 1048576)    { printf "%.1f MB/s", d/1048576    }
        else if (d >= 1024)       { printf "%.0f KB/s", d/1024       }
        else                      { printf "%d B/s",    d            }
    }'
}

RX1=$(echo "$SNAP1" | awk '{print $1}')
TX1=$(echo "$SNAP1" | awk '{print $2}')
RX2=$(echo "$SNAP2" | awk '{print $1}')
TX2=$(echo "$SNAP2" | awk '{print $2}')

DL=$(format_speed "$RX1" "$RX2")
UL=$(format_speed "$TX1" "$TX2")

# Build tooltip lines array for jq
TIP="${TYPE}: ${IFACE}"$'\n'"IP: ${IP:----}"
[ -n "$VPN_IP" ]   && TIP="${TIP}"$'\n'"VPN: ${VPN_IP}"
[ -n "$SSID" ] && [ "$IS_WIFI" = "1" ] && TIP="${TIP}"$'\n'"SSID: ${SSID}"
[ -n "$SIG_PCT" ]  && TIP="${TIP}"$'\n'"Signal: ${SIG_PCT}%"
TIP="${TIP}"$'\n'"↓ ${DL}   ↑ ${UL}"

# Safe compact JSON (single line — required by Waybar custom module)
jq -cn \
    --arg text    "$ICON" \
    --arg tooltip "$TIP" \
    --arg class   "connected" \
    '{text: $text, tooltip: $tooltip, class: $class}'
