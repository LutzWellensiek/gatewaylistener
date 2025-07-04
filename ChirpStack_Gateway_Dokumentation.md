# ChirpStack Gateway System - Dokumentation

**Datum:** 2025-07-04  
**System:** Raspberry Pi (Raspbian GNU/Linux)  
**Benutzer:** pi  
**Arbeitsverzeichnis:** /home/pi/gatewaylistener

## 1. Projektübersicht

### 1.1 Zielsetzung
- Git-Repository für Python-Scripts zur Gateway-Überwachung
- Analyse und Dokumentation des ChirpStack-Systems
- Monitoring von LoRaWAN-Gateway und ChirpStack-Server

### 1.2 GitHub Repository
- **URL:** https://github.com/LutzWellensiek/gatewaylistener.git
- **Zweck:** Sammlung von Python-Scripts für Gateway-Monitoring

## 2. Vorhandene Python-Scripts

### 2.1 Gefundene Dateien
1. **lorawan_gateway_monitor.py** - Gateway-Überwachung
2. **chirpstack_mqtt_listener.py** - MQTT-Listener für ChirpStack
3. **Gateway_Check.py** - Gateway-Status-Prüfung
4. **lorawan_system_monitor.py** - System-Monitoring

### 2.2 Git-Status
- Alle Scripts sind bereits committed
- Repository ist 1 Commit voraus (bereit zum Push)
- Remote-Origin konfiguriert auf GitHub-Repository

### 2.3 Netzwerkproblem
- DNS-Auflösung zu github.com nicht möglich
- Push-Vorgang aufgrund fehlender Internetverbindung gescheitert
- **Lösung:** Nach Wiederherstellung der Internetverbindung: `git push -u origin main`

## 3. ChirpStack Server - Detailanalyse

### 3.1 Installierte Komponenten
- **ChirpStack Gateway Bridge** - Aktiv und laufend
- **ChirpStack SQLite Service** - Aktiv und laufend (All-in-One Version)

### 3.2 Systemd Services
```
chirpstack-gateway-bridge.service - loaded active running
chirpstack-sqlite.service - loaded active running
```

### 3.3 ChirpStack Architektur

#### 3.3.1 Hauptkomponenten
1. **ChirpStack Gateway Bridge**
   - Verbindet LoRaWAN-Gateways mit Network Server
   - Kommunikation: UDP → MQTT
   - Standard-Port: UDP 1700

2. **ChirpStack Network Server** (in SQLite-Version integriert)
   - MAC-Layer-Verwaltung
   - Join-Requests und ADR (Adaptive Data Rate)
   - Duplikat-Erkennung und Frame-Counter-Validation
   - Geolocation über mehrere Gateways
   - Multicast und Class-B/C-Unterstützung

3. **ChirpStack Application Server** (in SQLite-Version integriert)
   - Device-Management
   - Payload-Dekodierung (JavaScript-basiert)
   - Integrationen (HTTP, MQTT, InfluxDB)
   - REST und gRPC APIs
   - Web-Interface

#### 3.3.2 Unterstützende Komponenten
- **SQLite Datenbank** - Speichert Geräte, Gateways, Anwendungen, Frames
- **MQTT Broker** - Message-Routing zwischen Komponenten

### 3.4 Datenfluss
```
LoRaWAN Device 
    ↓ (LoRa Radio)
LoRaWAN Gateway 
    ↓ (UDP Port 1700)
ChirpStack Gateway Bridge 
    ↓ (MQTT)
ChirpStack Network Server 
    ↓ (Internal/gRPC)
ChirpStack Application Server 
    ↓ (HTTP/MQTT/Integration)
Anwendung
```

### 3.5 Ports und Protokolle
- **UDP 1700:** Gateway → Gateway Bridge
- **MQTT 1883:** Gateway Bridge → Network Server
- **HTTP 8080:** Web Interface (Standard)
- **gRPC 8090:** API Access (Standard)

### 3.6 Aktuelle Systemaktivität
- Gateway-ID: **aa555a0000000000**
- Regelmäßige Statistik-Updates werden empfangen
- Metriken werden stündlich, täglich und monatlich gespeichert
- System läuft seit: 2025-07-04 06:43:57 BST (3h 10min)

#### 3.6.1 Letzte Log-Einträge
```
2025-07-04T08:55:03.153652Z INFO Message received from gateway region_id="eu868"
2025-07-04T08:55:03.182600Z INFO Gateway partially updated gateway_id=aa555a0000000000
2025-07-04T08:55:03.182834Z INFO Metrics saved name=gw:aa555a0000000000 aggregation=HOUR
2025-07-04T08:55:03.182914Z INFO Metrics saved name=gw:aa555a0000000000 aggregation=DAY
2025-07-04T08:55:03.182983Z INFO Metrics saved name=gw:aa555a0000000000 aggregation=MONTH
```

## 4. Konfigurationsdateien

### 4.1 Gefundene Konfigurationsverzeichnisse
- `/etc/chirpstack-sqlite` - SQLite-spezifische Konfiguration
- `/etc/chirpstack` - Allgemeine ChirpStack-Konfiguration
- `/etc/chirpstack-gateway-bridge` - Gateway Bridge Konfiguration

### 4.2 Systemd-Integration
- Services automatisch beim Systemstart aktiviert
- Logrotation konfiguriert unter `/etc/logrotate.d/chirpstack-gateway-bridge`

## 5. Installationstyp

**All-in-One SQLite-Version:**
- Vereint Network Server, Application Server und Database
- Ideal für kleinere Installationen und Entwicklungsumgebungen
- Geringerer Ressourcenverbrauch als verteilte PostgreSQL-Installation
- Vollständige Funktionalität in einem Service

## 6. Monitoring und Wartung

### 6.1 Service-Überwachung
```bash
systemctl status chirpstack-sqlite.service
systemctl status chirpstack-gateway-bridge.service
```

### 6.2 Log-Analyse
```bash
journalctl -u chirpstack-sqlite.service -f
journalctl -u chirpstack-gateway-bridge.service -f
```

### 6.3 Python-Scripts für Monitoring
- Automatisierte Überwachung der Services
- MQTT-Listener für Echtzeit-Datenerfassung
- Gateway-Status-Checks
- System-Performance-Monitoring

## 7. Nächste Schritte

### 7.1 Sofortige Maßnahmen
1. Internetverbindung prüfen und wiederherstellen
2. Git-Push durchführen: `git push -u origin main`
3. Repository auf GitHub verifizieren

### 7.2 Empfohlene Erweiterungen
1. README.md für das Repository erstellen
2. Systemd-Timer für automatische Script-Ausführung
3. Logging-Konfiguration für Python-Scripts
4. Alerting-System bei Gateway-Ausfällen

## 8. Technische Details

### 8.1 Systemumgebung
- **Betriebssystem:** Raspbian GNU/Linux
- **Shell:** bash 5.2.15(1)-release
- **Python-Scripts:** 4 Monitoring-Tools
- **ChirpStack-Version:** SQLite-Edition

### 8.2 Gateway-Konfiguration
- **Gateway-ID:** aa555a0000000000
- **Region:** EU868
- **Protokoll:** Semtech Packet Forwarder
- **Status:** Aktiv und sendend

---

**Dokumentation erstellt am:** 2025-07-04T09:34:17Z  
**Erstellt von:** ChirpStack Gateway Monitoring System  
**Letzte Aktualisierung:** 2025-07-04T09:34:17Z
