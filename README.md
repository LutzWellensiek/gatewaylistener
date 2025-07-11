# 🌐 LoRaWAN Gateway Monitor & Data Bridge

**Ein intelligenter All-in-One Monitor für LoRaWAN-Gateways mit ChirpStack**

Dieses Repository enthält Python-Tools für die Überwachung, Datenerfassung und Weiterleitung von LoRaWAN-Gateway-Systemen mit ChirpStack.

## 🚀 Features

- **🔍 Automatische Service-Erkennung**: Prüft alle kritischen LoRaWAN-Services
- **⚡ Auto-Start Funktion**: Startet ausgefallene Services automatisch neu
- **📡 Real-time MQTT Monitoring**: Empfängt und zeigt alle LoRa-Nachrichten live an
- **📊 CSV-Datenexport**: Automatische Speicherung aller Session-Daten
- **🔗 MQTT-to-UART Bridge**: Weiterleitung von ChirpStack-Daten über UART
- **🛠️ Zero-Configuration**: Läuft out-of-the-box ohne weitere Konfiguration

## 📋 Überwachte Komponenten

|| Service | Beschreibung | Auto-Start |
||---------|--------------|------------|
|| 🦟 **Mosquitto** | MQTT Broker für ChirpStack | ✅ |
|| 🌉 **ChirpStack Gateway Bridge** | Verbindung zwischen Packet Forwarder und ChirpStack | ✅ |
|| 📦 **Packet Forwarder** | SX1302/1303 LoRa Packet Forwarder | ✅ |
|| 🗄️ **ChirpStack SQLite** | All-in-One LoRaWAN Network Server | ✅ |

## 🏗️ Systemarchitektur

### 📡 Datenfluss
```
LoRaWAN Device 
    ↓ (LoRa Radio 868MHz)
LoRaWAN Gateway (SX1302/1303)
    ↓ (UDP Port 1700)
Packet Forwarder (lora_pkt_fwd)
    ↓ (UDP → MQTT)
ChirpStack Gateway Bridge 
    ↓ (MQTT Topic: gateway/+/event/+)
MQTT Broker (Mosquitto)
    ↓ (MQTT → gRPC)
ChirpStack Network Server
    ↓ (Internal Processing)
ChirpStack Application Server
    ↓ (MQTT Topic: application/+/device/+/event/+)
Monitoring Scripts
```

### 🔧 Kernkomponenten im Detail

#### 📦 Packet Forwarder
**Zweck:** Schnittstelle zwischen LoRa-Hardware und ChirpStack
- **Pfad:** `/home/pi/sx1302_hal/packet_forwarder/lora_pkt_fwd`
- **Protokoll:** Semtech UDP Packet Forwarder Protocol
- **Port:** UDP 1700 (Standard)
- **Funktion:** 
  - Empfängt LoRa-Pakete von SX1302/1303 Concentrator
  - Konvertiert RF-Daten in JSON-Format
  - Sendet Uplink-Pakete an Gateway Bridge
  - Empfängt Downlink-Kommandos für Übertragung
- **Konfiguration:** `global_conf.json`, `local_conf.json`

#### 🌉 ChirpStack Gateway Bridge
**Zweck:** Protokoll-Übersetzer zwischen UDP und MQTT
- **Service:** `chirpstack-gateway-bridge.service`
- **Protokoll-Konvertierung:** UDP ↔ MQTT
- **MQTT Topics:**
  - Uplink: `gateway/[gateway-id]/event/up`
  - Downlink: `gateway/[gateway-id]/command/down`
  - Stats: `gateway/[gateway-id]/event/stats`
- **Funktionen:**
  - Packet Forwarder Kompatibilität
  - Automatische Gateway-Registrierung
  - Metriken und Statistiken
  - Regionale Frequenz-Unterstützung (EU868, US915, etc.)

#### 🦟 MQTT Broker (Mosquitto)
**Zweck:** Zentrale Nachrichtenvermittlung
- **Service:** `mosquitto.service`
- **Port:** 1883 (Standard, unverschlüsselt)
- **Funktionen:**
  - Message Routing zwischen ChirpStack-Komponenten
  - Pub/Sub-Pattern für lose Kopplung
  - Persistent Sessions für Clients
  - QoS-Level-Unterstützung
- **Topic-Struktur:**
  ```
  gateway/
  ├── [gateway-id]/
  │   ├── event/up        # Uplink-Daten
  │   ├── event/stats     # Gateway-Statistiken
  │   └── command/down    # Downlink-Kommandos
  application/
  ├── [app-id]/
  │   └── device/
  │       └── [dev-eui]/
  │           └── event/
  │               ├── up      # Device-Uplinks
  │               ├── join    # Join-Requests
  │               ├── ack     # Acknowledgements
  │               └── status  # Device-Status
  ```

#### 🗄️ ChirpStack SQLite
**Zweck:** All-in-One LoRaWAN Network Server
- **Service:** `chirpstack-sqlite.service`
- **Komponenten:**
  - **Network Server:** MAC-Layer-Verwaltung, Join-Handling, ADR
  - **Application Server:** Device-Management, Payload-Dekodierung
  - **Web Interface:** Management-UI (Port 8080)
  - **SQLite Database:** Lokale Datenspeicherung
- **Funktionen:**
  - Frame-Counter-Validation
  - Duplikat-Erkennung
  - Geolocation (bei mehreren Gateways)
  - Adaptive Data Rate (ADR)
  - Multicast-Unterstützung
  - Class A/B/C Device-Unterstützung

### 🌐 Netzwerk-Ports

| Port | Protokoll | Service | Zweck |
|------|-----------|---------|-------|
| 1700 | UDP | Packet Forwarder | Gateway ↔ Bridge |
| 1883 | TCP | MQTT (Mosquitto) | Message Broker |
| 8080 | HTTP | ChirpStack Web UI | Management Interface |
| 8090 | gRPC | ChirpStack API | Programmatic Access |

## 💻 Python-Skripte

### 📊 lorawan_system_monitor.py
**Hauptskript für vollständiges System-Monitoring**
- Automatische Service-Überwachung und -Neustart
- Real-time MQTT-Datenempfang von ChirpStack
- CSV-Export aller Session-Daten mit eindeutiger Session-ID
- Anzeige von Gateway- und Device-Informationen
- Dekodierung von LoRaWAN-Payloads (Base64, Hex, ASCII, JSON)

### 🔗 chirpstack_mqtt_to_uart.py
**MQTT-to-UART Bridge für Datenweiterleitung**
- Empfängt ChirpStack MQTT-Nachrichten
- Verarbeitet und strukturiert LoRaWAN-Daten
- Sendet JSON-formatierte Daten über UART
- Unterstützt alle ChirpStack-Event-Typen (uplink, join, status, stats)

## 🔧 Installation & Setup

### Voraussetzungen
- Raspberry Pi mit installiertem ChirpStack (SQLite oder PostgreSQL)
- Python 3.7+
- Konfigurierter SX1302/SX1303 LoRa Concentrator

### Installation
```bash
# Repository klonen
git clone https://github.com/LutzWellensiek/gatewaylistener.git
cd gatewaylistener

# Python-Abhängigkeiten installieren
pip3 install paho-mqtt pyserial

# System Monitor starten
python3 lorawan_system_monitor.py

# MQTT-to-UART Bridge starten
python3 chirpstack_mqtt_to_uart.py
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

#### 📦 Packet Forwarder Probleme
**Problem**: Packet Forwarder startet nicht
```bash
# Prüfe Hardware-Verbindung
sudo dmesg | grep -i spi

# Prüfe Konfigurationsdateien
ls -la /home/pi/sx1302_hal/packet_forwarder/
cat /home/pi/sx1302_hal/packet_forwarder/global_conf.json

# Starte manuell für Debug
cd /home/pi/sx1302_hal/packet_forwarder/
sudo ./lora_pkt_fwd
```

**Problem**: Gateway-ID nicht konfiguriert
```bash
# Prüfe Gateway-ID in local_conf.json
cat /home/pi/sx1302_hal/packet_forwarder/local_conf.json
# Gateway-ID sollte eindeutig sein (z.B. MAC-basiert)
```

#### 🌉 ChirpStack Gateway Bridge Probleme
**Problem**: Bridge kann nicht zu MQTT verbinden
```bash
# Prüfe Mosquitto Status
sudo systemctl status mosquitto

# Prüfe MQTT-Verbindung
mosquitto_pub -h localhost -p 1883 -t test -m "hello"
mosquitto_sub -h localhost -p 1883 -t test

# Prüfe Gateway Bridge Logs
journalctl -u chirpstack-gateway-bridge.service -f
```

**Problem**: Keine Uplink-Daten empfangen
```bash
# Prüfe MQTT Topics
mosquitto_sub -h localhost -p 1883 -t "gateway/+/event/+"

# Prüfe Gateway Bridge Konfiguration
sudo nano /etc/chirpstack-gateway-bridge/chirpstack-gateway-bridge.toml
```

#### 🦟 MQTT Broker (Mosquitto) Probleme
**Problem**: Mosquitto startet nicht
```bash
# Prüfe Service Status
sudo systemctl status mosquitto

# Prüfe Konfiguration
sudo nano /etc/mosquitto/mosquitto.conf

# Prüfe Logs
sudo journalctl -u mosquitto.service

# Neustart
sudo systemctl restart mosquitto
```

**Problem**: Port 1883 bereits belegt
```bash
# Prüfe Port-Verwendung
sudo netstat -tlnp | grep 1883
sudo lsof -i :1883
```

#### 🗄️ ChirpStack SQLite Probleme
**Problem**: ChirpStack Web UI nicht erreichbar
```bash
# Prüfe Service Status
sudo systemctl status chirpstack-sqlite

# Prüfe Port 8080
sudo netstat -tlnp | grep 8080
curl http://localhost:8080

# Prüfe Logs
journalctl -u chirpstack-sqlite.service -f
```

**Problem**: Devices können nicht joinen
```bash
# Prüfe Device-Konfiguration im Web UI
# Prüfe Application und Device Profile
# Prüfe Device Keys (DevEUI, AppEUI, AppKey)

# Prüfe Join-Requests in MQTT
mosquitto_sub -h localhost -p 1883 -t "application/+/device/+/event/join"
```

#### 🔧 Allgemeine Debugging-Tipps
```bash
# Alle Services prüfen
sudo systemctl status mosquitto chirpstack-gateway-bridge chirpstack-sqlite

# Alle LoRaWAN-relevanten Logs
sudo journalctl -u mosquitto -u chirpstack-gateway-bridge -u chirpstack-sqlite -f

# Netzwerk-Konnektivität prüfen
sudo netstat -tlnp | grep -E "1700|1883|8080|8090"

# Systemressourcen prüfen
top -p $(pgrep -d, -f "mosquitto|chirpstack|lora_pkt_fwd")
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

### 💻 Python-Skripte
- **`lorawan_system_monitor.py`** - Hauptskript für vollständiges System-Monitoring
- **`chirpstack_mqtt_to_uart.py`** - MQTT-to-UART Bridge für Datenweiterleitung

### 📄 Dokumentation
- **`README.md`** - Diese Datei (Projektdokumentation)
- **`ChirpStack_Gateway_Dokumentation.md`** - Detaillierte Systemdokumentation
- **`Session_Summary.txt`** - Projekt-Session-Zusammenfassung
- **`LICENSE`** - MIT-Lizenz

### 📁 Datenordner
- **`Lora_Sesion_Data/`** - Automatisch generierte CSV-Dateien mit Session-Daten

> **Empfehlung**: Nutze `lorawan_system_monitor.py` als Haupttool für Monitoring und `chirpstack_mqtt_to_uart.py` für UART-Integration.

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
