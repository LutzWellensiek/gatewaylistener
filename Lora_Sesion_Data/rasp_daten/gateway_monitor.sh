#!/bin/bash

echo "=== LoRaWAN Gateway Monitor ==="
echo "Überwachung gestartet: $(date)"
echo "Gateway ID: AA555A0000000000"
echo "==============================="

# Terminal in 4 Bereiche aufteilen für verschiedene Monitoring-Streams
tmux new-session -d -s gateway_monitor

# Fenster 1: Packet Forwarder Logs
tmux new-window -t gateway_monitor:1 -n 'PacketFwd' "cd /home/pi/sx1302_hal/packet_forwarder && tail -f live_gateway.log"

# Fenster 2: MQTT Gateway Events
tmux new-window -t gateway_monitor:2 -n 'MQTT-GW' "mosquitto_sub -h localhost -t 'eu868/gateway/+/event/+' -v"

# Fenster 3: MQTT Application Events (Uplinks)
tmux new-window -t gateway_monitor:3 -n 'MQTT-App' "mosquitto_sub -h localhost -t 'application/+/device/+/event/+' -v"

# Fenster 4: ChirpStack Logs
tmux new-window -t gateway_monitor:4 -n 'ChirpStack' "sudo journalctl -f -u chirpstack"

echo "Tmux Session 'gateway_monitor' gestartet."
echo "Verbinden mit: tmux attach -t gateway_monitor"
echo "Zwischen Fenstern wechseln: Ctrl+B dann Nummer (1-4)"
echo "Session beenden: Ctrl+B dann :kill-session"
