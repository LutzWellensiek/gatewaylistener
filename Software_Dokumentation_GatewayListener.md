# LoRaWAN Gateway Listener System - Detaillierte Software-Dokumentation

**Erstellt am:** 2025-07-11  
**System:** Raspberry Pi (Raspbian GNU/Linux)  
**Projektverzeichnis:** /home/pi/gatewaylistener  
**Git Repository:** https://github.com/LutzWellensiek/gatewaylistener.git

---

## 1. Systemarchitektur

### 1.1 Überblick
Das Gateway Listener System ist eine Python-basierte Monitoring- und Datenverarbeitungsplattform für LoRaWAN-Gateways mit ChirpStack-Integration. Das System besteht aus mehreren spezialisierten Komponenten für verschiedene Aspekte der Gateway-Überwachung und Datenweiterleitung.

### 1.2 Architektur-Diagramm
```
LoRaWAN Device 
    ↓ (LoRa Radio)
LoRaWAN Gateway 
    ↓ (UDP Port 1700)
ChirpStack Gateway Bridge 
    ↓ (MQTT)
ChirpStack Network Server 
    ↓ (MQTT/HTTP)
Python Gateway Listener Scripts
    ↓ (UART/Logging/Monitoring)
Externe Systeme/Datenbanken
```

### 1.3 Hauptkomponenten
1. **MQTT-zu-UART Bridge** - Datenweiterleitung über serielle Schnittstelle
2. **System Monitor** - Umfassende Systemüberwachung
3. **ChirpStack Services** - LoRaWAN Network/Application Server
4. **Datenlogging** - Persistente Speicherung von Sitzungsdaten

---

## 2. Software-Komponenten

### 2.1 Python-Scripts im Detail

#### 2.1.1 chirpstack_mqtt_to_uart.py
**Zweck:** MQTT-zu-UART Bridge für LoRaWAN-Datenweiterleitung
**Dateigröße:** ~234 Zeilen Code
**Ausführungsmodus:** Executable

**Funktionalität:**
- Empfang von ChirpStack MQTT-Nachrichten
- Filterung auf Uplink-Daten (tatsächlich empfangene Daten)
- Weiterleitung über UART-Schnittstelle
- Statistikerfassung und Logging

**Technische Details:**
- **MQTT-Broker:** localhost:1883
- **UART-Port:** /dev/ttyAMA0 (Standard)
- **Baudrate:** 9600 (Standard)
- **Subscription:** application/+/device/+/event/up

**Abhängigkeiten:**
```python
import serial
import paho.mqtt.client as mqtt
import json
import time
import base64
from datetime import datetime
```

#### 2.1.2 chirpstack_mqtt_to_uart_backup.py
**Zweck:** Backup-Version des MQTT-zu-UART Bridge Scripts
**Dateigröße:** ~252 Zeilen Code
**Status:** Backup/Fallback-Version

#### 2.1.3 lorawan_system_monitor.py
**Zweck:** Umfassende Systemüberwachung und Monitoring
**Dateigröße:** ~651 Zeilen Code (größtes Script)
**Ausführungsmodus:** Executable

**Erweiterte Funktionalität:**
- ChirpStack Service-Überwachung
- Gateway-Status-Monitoring
- Systemmetriken-Erfassung
- Performance-Analyse
- Fehlerbehandlung und Alerting

### 2.2 Konfigurationsdateien

#### 2.2.1 LICENSE
**Typ:** MIT License
**Größe:** 1.072 Bytes
**Zweck:** Lizenzierung des Projekts

#### 2.2.2 Session_Summary.txt
**Typ:** Log-Datei
**Größe:** 1.472 Bytes
**Zweck:** Sitzungsprotokoll und Zusammenfassung

### 2.3 Datenverzeichnisse

#### 2.3.1 Lora_Sesion_Data/
**Zweck:** Speicherung von LoRa-Sitzungsdaten
**Typ:** Verzeichnis für temporäre/permanente Datenspeicherung

---

## 3. ChirpStack-Integration

### 3.1 Installierte ChirpStack-Komponenten

#### 3.1.1 ChirpStack Gateway Bridge
**Service:** chirpstack-gateway-bridge.service
**Status:** Aktiv und laufend
**Funktion:** UDP-zu-MQTT Bridge für Gateway-Kommunikation

**Konfiguration:**
- **Eingangsport:** UDP 1700
- **Ausgangsprotokoll:** MQTT
- **Konfigurationspfad:** /etc/chirpstack-gateway-bridge

#### 3.1.2 ChirpStack SQLite Service
**Service:** chirpstack-sqlite.service
**Status:** Aktiv und laufend
**Typ:** All-in-One Version (Network Server + Application Server + Database)

**Integrierte Komponenten:**
- Network Server (MAC-Layer-Verwaltung)
- Application Server (Device-Management)
- SQLite-Datenbank (Datenpersistierung)
- Web-Interface (HTTP:8080)
- gRPC-API (Port 8090)

### 3.2 Gateway-Konfiguration

#### 3.2.1 Aktive Gateway-Parameter
- **Gateway-ID:** aa555a0000000000
- **Region:** EU868
- **Protokoll:** Semtech Packet Forwarder
- **Status:** Aktiv und sendend
- **Statistik-Updates:** Stündlich, täglich, monatlich

#### 3.2.2 Datenfluss-Monitoring
```
Gateway → UDP:1700 → Gateway Bridge → MQTT → Network Server → Application Server → Python Scripts
```

---

## 4. Systemüberwachung und Monitoring

### 4.1 Service-Überwachung

#### 4.1.1 Systemd-Services
```bash
# ChirpStack Services
systemctl status chirpstack-sqlite.service
systemctl status chirpstack-gateway-bridge.service

# Python Scripts (wenn als Service konfiguriert)
systemctl status gatewaylistener.service
```

#### 4.1.2 Log-Analyse
```bash
# ChirpStack Logs
journalctl -u chirpstack-sqlite.service -f
journalctl -u chirpstack-gateway-bridge.service -f

# System Logs
journalctl -f | grep -i lorawan
```

### 4.2 Performance-Metriken

#### 4.2.1 Gateway-Metriken
- **Uptime:** Kontinuierliche Betriebszeit
- **Packet-Loss:** Paketverlust-Rate
- **Signal-Qualität:** RSSI/SNR-Werte
- **Throughput:** Datenübertragungsrate

#### 4.2.2 System-Metriken
- **CPU-Auslastung:** Python-Script-Performance
- **Memory-Usage:** Speicherverbrauch
- **Disk-I/O:** Datenschreibung/-lesung
- **Network-Traffic:** MQTT/UART-Datenvolumen

---

## 5. Datenverarbeitung und Protokolle

### 5.1 MQTT-Nachrichtenverarbeitung

#### 5.1.1 Nachrichtentypen
- **Uplink-Daten:** application/+/device/+/event/up
- **Downlink-Bestätigung:** application/+/device/+/event/ack
- **Gateway-Statistiken:** gateway/+/event/stats
- **Join-Requests:** application/+/device/+/event/join

#### 5.1.2 Payload-Verarbeitung
```python
# Beispiel-Datenstrukturen
{
    "applicationID": "string",
    "applicationName": "string",
    "deviceName": "string",
    "devEUI": "hex-string",
    "rxInfo": [...],
    "txInfo": {...},
    "data": "base64-encoded-payload"
}
```

### 5.2 UART-Datenübertragung

#### 5.2.1 Serielle Schnittstelle
- **Port:** /dev/ttyAMA0 (Raspberry Pi UART)
- **Baudrate:** 9600 bps
- **Datenformat:** 8N1 (8 Bits, keine Parität, 1 Stop-Bit)
- **Flow-Control:** Keine

#### 5.2.2 Protokoll-Format
```
Timestamp | DevEUI | Payload | RSSI | SNR | Gateway-ID
```

### 5.3 Logging und Datenarchivierung

#### 5.3.1 Log-Struktur
- **Timestamp:** ISO 8601 Format
- **Log-Level:** DEBUG, INFO, WARNING, ERROR
- **Komponente:** Script-Name/Funktion
- **Nachricht:** Detaillierte Beschreibung

#### 5.3.2 Datenrotation
- **Tägliche Rotation:** Automatische Log-Archivierung
- **Komprimierung:** Ältere Logs werden komprimiert
- **Aufbewahrungszeit:** 30 Tage (konfigurierbar)

---

## 6. Fehlerbehandlung und Wartung

### 6.1 Häufige Probleme und Lösungen

#### 6.1.1 MQTT-Verbindungsprobleme
**Symptom:** Keine MQTT-Nachrichten empfangen
**Lösung:**
```bash
# Broker-Status prüfen
systemctl status mosquitto
# Verbindung testen
mosquitto_pub -h localhost -t test -m "test"
```

#### 6.1.2 UART-Kommunikationsfehler
**Symptom:** Keine serielle Datenübertragung
**Lösung:**
```bash
# UART-Status prüfen
dmesg | grep ttyAMA0
# Berechtigungen prüfen
ls -l /dev/ttyAMA0
```

#### 6.1.3 ChirpStack-Service-Ausfälle
**Symptom:** Gateway nicht erreichbar
**Lösung:**
```bash
# Service-Neustart
systemctl restart chirpstack-sqlite.service
systemctl restart chirpstack-gateway-bridge.service
```

### 6.2 Wartungsroutinen

#### 6.2.1 Tägliche Wartung
- Log-Dateien überprüfen
- Service-Status kontrollieren
- Festplattenspeicher prüfen

#### 6.2.2 Wöchentliche Wartung
- Datenbank-Optimierung
- Backup-Überprüfung
- Performance-Analyse

#### 6.2.3 Monatliche Wartung
- System-Updates
- Konfiguration-Review
- Sicherheits-Audit

---

## 7. Sicherheit und Konfiguration

### 7.1 Sicherheitsmaßnahmen

#### 7.1.1 Netzwerk-Sicherheit
- **Firewall:** UFW mit spezifischen Regeln
- **SSH:** Key-basierte Authentifizierung
- **MQTT:** Lokale Bindung (localhost)

#### 7.1.2 Dateisystem-Sicherheit
- **Berechtigungen:** Restriktive Dateirechte
- **Benutzer:** Dedizierte Service-Benutzer
- **Logs:** Sichere Log-Speicherung

### 7.2 Konfigurationsmanagement

#### 7.2.1 Umgebungsvariablen
```bash
# MQTT-Konfiguration
export MQTT_BROKER=localhost
export MQTT_PORT=1883

# UART-Konfiguration
export UART_PORT=/dev/ttyAMA0
export UART_BAUDRATE=9600
```

#### 7.2.2 Konfigurationsdateien
- **ChirpStack:** /etc/chirpstack-sqlite/
- **Gateway Bridge:** /etc/chirpstack-gateway-bridge/
- **Python Scripts:** JSON-Konfigurationsdateien

---

## 8. Deployment und Installation

### 8.1 Systemanforderungen

#### 8.1.1 Hardware
- **Raspberry Pi:** 3B+ oder höher
- **RAM:** Mindestens 1GB
- **Storage:** 16GB SD-Karte
- **Netzwerk:** Ethernet/WiFi

#### 8.1.2 Software
- **OS:** Raspbian GNU/Linux
- **Python:** 3.7+
- **Node.js:** 14+ (für ChirpStack)
- **SQLite:** 3.22+

### 8.2 Installationsprozess

#### 8.2.1 Abhängigkeiten
```bash
# Python-Pakete
pip3 install paho-mqtt pyserial

# System-Pakete
sudo apt update
sudo apt install git python3-pip
```

#### 8.2.2 Service-Installation
```bash
# Repository klonen
git clone https://github.com/LutzWellensiek/gatewaylistener.git

# Berechtigungen setzen
chmod +x *.py

# Systemd-Service erstellen (optional)
sudo systemctl enable gatewaylistener.service
```

### 8.3 Automatisierung

#### 8.3.1 Systemd-Timer
```ini
[Unit]
Description=Gateway Listener Timer
Requires=gatewaylistener.service

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
```

#### 8.3.2 Cron-Jobs
```bash
# Tägliche Log-Rotation
0 0 * * * /usr/local/bin/rotate_logs.sh

# Stündliche Gesundheitsprüfung
0 * * * * /home/pi/gatewaylistener/health_check.py
```

---

## 9. API und Integrationen

### 9.1 ChirpStack-API

#### 9.1.1 REST-API
**Basis-URL:** http://localhost:8080/api
**Authentifizierung:** JWT-Token

**Wichtige Endpoints:**
- `/applications` - Anwendungsmanagement
- `/devices` - Geräteverwaltung
- `/gateways` - Gateway-Konfiguration
- `/device-queue` - Nachrichtenwarteschlange

#### 9.1.2 gRPC-API
**Port:** 8090
**Protokoll:** HTTP/2 + gRPC

### 9.2 Python-API-Integration

#### 9.2.1 HTTP-Client
```python
import requests

# Gateway-Status abfragen
response = requests.get('http://localhost:8080/api/gateways')
gateways = response.json()
```

#### 9.2.2 gRPC-Client
```python
import grpc
from chirpstack_api import gateway_pb2, gateway_pb2_grpc

# gRPC-Verbindung
channel = grpc.insecure_channel('localhost:8090')
stub = gateway_pb2_grpc.GatewayServiceStub(channel)
```

---

## 10. Troubleshooting und Debugging

### 10.1 Debug-Modi

#### 10.1.1 Verbose-Logging
```bash
# Python-Script mit Debug-Ausgabe
python3 -u chirpstack_mqtt_to_uart.py --debug

# ChirpStack mit Debug-Level
journalctl -u chirpstack-sqlite.service -f --output=json
```

#### 10.1.2 Netzwerk-Debugging
```bash
# MQTT-Traffic monitoren
mosquitto_sub -h localhost -t '#' -v

# UDP-Traffic analysieren
sudo tcpdump -i any port 1700
```

### 10.2 Performance-Optimierung

#### 10.2.1 Python-Script-Optimierung
- **Asynchrone Programmierung:** asyncio für bessere Performance
- **Memory-Management:** Regelmäßige Garbage Collection
- **Connection-Pooling:** Wiederverwendung von Verbindungen

#### 10.2.2 System-Optimierung
- **CPU-Scheduling:** Prozess-Prioritäten anpassen
- **Memory-Tuning:** Swap-Konfiguration optimieren
- **I/O-Scheduling:** Disk-Scheduler anpassen

---

## 11. Backup und Wiederherstellung

### 11.1 Backup-Strategie

#### 11.1.1 Automatisierte Backups
```bash
#!/bin/bash
# Backup-Script
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/gatewaylistener_$DATE"

# Code-Backup
cp -r /home/pi/gatewaylistener $BACKUP_DIR/code

# Datenbank-Backup
sqlite3 /var/lib/chirpstack-sqlite/chirpstack.db .dump > $BACKUP_DIR/database.sql

# Konfiguration-Backup
cp -r /etc/chirpstack-sqlite $BACKUP_DIR/config
```

#### 11.1.2 Wiederherstellungsverfahren
```bash
# Code-Wiederherstellung
git checkout -- .
git pull origin main

# Datenbank-Wiederherstellung
sqlite3 /var/lib/chirpstack-sqlite/chirpstack.db < backup_database.sql

# Service-Neustart
systemctl restart chirpstack-sqlite.service
```

### 11.2 Disaster Recovery

#### 11.2.1 Vollständige Systemwiederherstellung
1. **OS-Neuinstallation:** Raspbian von Image
2. **Basis-Pakete:** Python, Git, ChirpStack
3. **Konfiguration:** Backup-Wiederherstellung
4. **Services:** Automatischer Start
5. **Validierung:** Funktionstest

#### 11.2.2 Minimale Wiederherstellungszeit
- **RTO (Recovery Time Objective):** < 2 Stunden
- **RPO (Recovery Point Objective):** < 1 Tag
- **Kritische Services:** < 30 Minuten

---

## 12. Monitoring und Alerting

### 12.1 Überwachungsmetriken

#### 12.1.1 System-Metriken
- **CPU-Auslastung:** Durchschnitt und Spitzen
- **Memory-Usage:** RAM und Swap-Verbrauch
- **Disk-Usage:** Freier Speicherplatz
- **Network-I/O:** Bandbreiten-Auslastung

#### 12.1.2 Application-Metriken
- **MQTT-Nachrichten:** Empfangen/Gesendet pro Minute
- **UART-Übertragungen:** Erfolgreiche/Fehlgeschlagene
- **Gateway-Uptime:** Verfügbarkeit in Prozent
- **Fehlerrate:** Fehler pro Stunde

### 12.2 Alerting-System

#### 12.2.1 Alarm-Schwellenwerte
- **CPU > 80%:** Warning nach 5 Minuten
- **Memory > 90%:** Critical sofort
- **Disk < 10%:** Warning nach 1 Stunde
- **Service Down:** Critical sofort

#### 12.2.2 Benachrichtigungskanäle
- **E-Mail:** Für alle Critical-Alerts
- **SMS:** Für Service-Ausfälle
- **Logs:** Für alle Ereignisse
- **Dashboard:** Echtzeit-Visualisierung

---

## 13. Zukunftige Erweiterungen

### 13.1 Geplante Features

#### 13.1.1 Erweiterte Datenanalyse
- **Machine Learning:** Anomalie-Erkennung
- **Predictive Analytics:** Vorhersage von Ausfällen
- **Data Visualization:** Grafische Dashboards
- **Historical Analysis:** Langzeit-Trends

#### 13.1.2 Skalierbarkeit
- **Multi-Gateway:** Unterstützung mehrerer Gateways
- **Load Balancing:** Verteilung der Last
- **Clustering:** Redundante Systeme
- **Cloud Integration:** AWS/Azure-Anbindung

### 13.2 Technologie-Roadmap

#### 13.2.1 Kurze Frist (3 Monate)
- **Docker-Integration:** Containerisierung
- **REST-API:** Externe Schnittstellen
- **Web-Dashboard:** Benutzeroberfläche
- **Automated Testing:** Unit/Integration Tests

#### 13.2.2 Mittlere Frist (6 Monate)
- **Microservices:** Service-Architektur
- **Message Queues:** Asynchrone Verarbeitung
- **Database Optimization:** Performance-Tuning
- **Security Hardening:** Erweiterte Sicherheit

#### 13.2.3 Lange Frist (12 Monate)
- **AI/ML Integration:** Intelligente Analyse
- **Edge Computing:** Dezentrale Verarbeitung
- **5G Integration:** Neue Kommunikationsprotokolle
- **IoT Platform:** Vollständige IoT-Lösung

---

## 14. Fazit und Bewertung

### 14.1 Systemstärken
- **Modular:** Klar getrennte Komponenten
- **Erweiterbar:** Einfache Integration neuer Features
- **Robust:** Fehlertolerante Architektur
- **Überwachbar:** Umfassende Monitoring-Capabilities

### 14.2 Verbesserungspotenzial
- **Dokumentation:** Erweiterte Code-Kommentierung
- **Testing:** Automatisierte Testabdeckung
- **Configuration:** Zentrale Konfigurationsverwaltung
- **Deployment:** Automatisierte Installationsprozesse

### 14.3 Empfehlungen
1. **Sofortige Maßnahmen:** Backup-Strategie implementieren
2. **Kurzfristig:** Monitoring-Dashboard entwickeln
3. **Mittelfristig:** Docker-basierte Deployment
4. **Langfristig:** Cloud-Integration planen

---

**Dokumentation Ende**

*Diese Dokumentation wird kontinuierlich aktualisiert und erweitert basierend auf Systemänderungen und neuen Anforderungen.*

---

**Technische Spezifikationen:**
- **Dokumentversion:** 1.0
- **Letzte Aktualisierung:** 2025-07-11T08:12:31Z
- **Autor:** Gateway Listener System Documentation
- **Klassifikation:** Interne Entwicklungsdokumentation
