# 🌐 LoRaWAN Gateway Monitor

**Ein intelligenter All-in-One Monitor für LoRaWAN-Gateways mit ChirpStack**

Dieses Python-Skript kombiniert Service-Überwachung, automatisches Starten von Gateway-Komponenten und Echtzeit-Datenmonitoring in einem einzigen Tool.

## 🚀 Features

- **🔍 Automatische Service-Erkennung**: Prüft alle kritischen LoRaWAN-Services
- **⚡ Auto-Start Funktion**: Startet ausgefallene Services automatisch neu
- **📡 Real-time MQTT Monitoring**: Empfängt und zeigt alle LoRa-Nachrichten live an
- **📊 Serial Monitor Ausgabe**: Formatierte Ausgabe aller empfangenen Daten
- **🛠️ Zero-Configuration**: Läuft out-of-the-box ohne weitere Konfiguration

## 📋 Überwachte Komponenten

| Service | Beschreibung | Auto-Start |
|---------|--------------|------------|
| 🦟 **Mosquitto** | MQTT Broker für ChirpStack | ✅ |
| 🌉 **ChirpStack Gateway Bridge** | Verbindung zwischen Packet Forwarder und ChirpStack | ✅ |
| 📦 **Packet Forwarder** | SX1302/1303 LoRa Packet Forwarder | ✅ |

## 🔧 Installation & Setup

### Voraussetzungen
- Raspberry Pi mit installiertem ChirpStack
- Python 3.7+
- Konfigurierter SX1302/SX1303 LoRa Concentrator

### Installation
```bash
# Repository klonen
git clone https://github.com/LutzWellensiek/gatewaylistener.git
cd gatewaylistener

# Python-Abhängigkeiten installieren
pip3 install paho-mqtt

# Skript direkt ausführen
python3 lorawan_gateway_monitor.py
```

## 🏃‍♂️ Verwendung

### Einfacher Start
```bash
python3 lorawan_gateway_monitor.py
```

### Als Service (dauerhaft im Hintergrund)
```bash
# Service-Datei erstellen
sudo nano /etc/systemd/system/lorawan-monitor.service

# Service aktivieren
sudo systemctl enable lorawan-monitor.service
sudo systemctl start lorawan-monitor.service
```

## 📺 Ausgabe-Beispiel

```
🚀 LoRaWAN Gateway Monitor gestartet
============================================================
🔍 LoRaWAN SYSTEM CHECK
============================================================

📋 Service Status:
   mosquitto: ✅ AKTIV
   chirpstack-gateway-bridge: ✅ AKTIV
   lora_pkt_fwd: ✅ LÄUFT

🌐 Connectivity Check:
   MQTT Broker: ✅ ERREICHBAR

🎉 Alle Services sind bereit!
============================================================

📡 Verbunden mit MQTT Broker (localhost:1883)
🎯 Lausche auf Topic: application/+/device/+/event/+

============================================================
📊 LIVE DATA MONITOR - Warte auf LoRa-Nachrichten...
============================================================

============================================================
🕐 2024-03-15 14:30:47
📱 App: 1 | 🔷 Device: 1234567890abcdef | 📊 Type: up
============================================================
📈 UPLINK DATA:
   📊 Frame Count: 42
   🚪 Port: 1
   📦 Raw (Base64): SGVsbG8gV29ybGQ=
   🔢 Hex: 48656C6C6F20576F726C64
   📋 Bytes: [72, 101, 108, 108, 111, 32, 87, 111, 114, 108, 100]
   📝 ASCII: 'Hello World'
   📡 Gateway Info:
      📶 gateway-001... | RSSI: -85dBm | SNR: 7.5dB
```

## ⚙️ Konfiguration

Das Skript verwendet standardmäßig folgende Einstellungen:

```python
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "application/+/device/+/event/+"
PACKET_FORWARDER_PATH = "/home/pi/sx1302_hal/packet_forwarder"
```

Diese können bei Bedarf im Skript angepasst werden.

## 🐛 Troubleshooting

### Häufige Probleme

**Problem**: Services starten nicht automatisch
```bash
# Prüfe Berechtigungen
sudo usermod -aG sudo pi
```

**Problem**: Packet Forwarder nicht gefunden
```bash
# Pfad anpassen in der Konfiguration
PACKET_FORWARDER_PATH = "/dein/pfad/zum/packet_forwarder"
```

**Problem**: Keine MQTT-Nachrichten
```bash
# ChirpStack prüfen
sudo systemctl status chirpstack
curl http://localhost:8080
```

## 🛡️ Service-Datei Beispiel

```ini
[Unit]
Description=LoRaWAN Gateway Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/gatewaylistener
ExecStart=/usr/bin/python3 lorawan_gateway_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 📂 Repository-Inhalt

- **`lorawan_gateway_monitor.py`** - Hauptskript (NEU, kombiniert alle Funktionen)
- **`chirpstack_mqtt_listener.py`** - Legacy MQTT Listener
- **`Gateway_Check.py`** - Legacy Service Checker  
- **`lorawan_system_monitor.py`** - Legacy System Monitor

> **Empfehlung**: Verwende das neue `lorawan_gateway_monitor.py` - es kombiniert alle Funktionen der Legacy-Skripte in einem optimierten Tool.

## 🤝 Contributing

Beiträge sind willkommen! Bitte:

1. Forke das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/AmazingFeature`)
3. Committe deine Änderungen (`git commit -m 'Add some AmazingFeature'`)
4. Pushe zum Branch (`git push origin feature/AmazingFeature`)
5. Öffne eine Pull Request

## 📝 License

Dieses Projekt steht unter der MIT License. Siehe `LICENSE` Datei für Details.

## 👤 Autor

**Lutz Wellensiek**
- GitHub: [@LutzWellensiek](https://github.com/LutzWellensiek)

---

⭐ Wenn dir dieses Projekt gefällt, gib ihm einen Star auf GitHub!
