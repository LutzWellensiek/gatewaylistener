# ChirpStack Gateway Bridge - Technische Dokumentation

## Projektübersicht

**Name**: ChirpStack Gateway Bridge  
**Typ**: Python-basierte Middleware  
**Hauptzweck**: Brücke zwischen ChirpStack MQTT-Broker und UART-Geräten  
**Programmiersprache**: Python 3.x  
**Hauptdatei**: `main.py`  
**Konfigurationsdatei**: `config.json`

## Technische Details

### Datenfluss
1. **Eingang**: MQTT-Nachrichten von ChirpStack (JSON-Format mit Base64-kodierter Payload)
2. **Verarbeitung**: 
   - JSON-Parsing
   - Base64-Dekodierung
   - Optional: Hex-Dekodierung bei doppelt kodierten Daten
   - Device-ID Extraktion aus MQTT-Topic
3. **Ausgang**: UART-Signal im Format `<device_name>: <binary_payload>`

### MQTT-Topic-Format
```
application/{application_id}/device/{device_id}/event/up
```

### JSON-Nachrichtenstruktur (ChirpStack)
```json
{
  "data": "BASE64_ENCODED_PAYLOAD",
  "devEUI": "DEVICE_EUI",
  "applicationID": "APP_ID",
  "deviceName": "OPTIONAL_NAME",
  ...
}
```

### Module und deren Funktionen

#### 1. `config.py`
- **Funktion**: Konfigurationsmanagement
- **Hauptmethoden**:
  - `load_config(file_path)`: Lädt JSON-Konfiguration
  - `get_default_config()`: Gibt Standardkonfiguration zurück

#### 2. `logger.py`
- **Funktion**: Logging-Setup
- **Features**: Rotating File Handler, konfigurierbares Log-Level
- **Log-Level**: DEBUG, INFO, WARNING, ERROR

#### 3. `uart_comm.py` (Klasse: UARTCommunicator)
- **Funktion**: UART-Kommunikation
- **Features**:
  - Automatische Wiederverbindung
  - Retry-Mechanismus (3 Versuche)
  - Konfigurierbare Parameter (Baudrate, Parity, etc.)

#### 4. `mqtt_handler.py` (Klasse: MQTTHandler)
- **Funktion**: MQTT-Verbindungsverwaltung
- **Features**:
  - Auto-Reconnect
  - Topic-Subscription
  - Callback-basierte Nachrichtenverarbeitung

#### 5. `processor.py` (Klasse: MessageProcessor)
- **Funktion**: Nachrichtenverarbeitung
- **Features**:
  - Base64-Dekodierung
  - Hex-String-Erkennung und -Dekodierung
  - Payload-Validierung (Größenlimit: 255 Bytes)
  - UART-Nachrichtenerstellung

#### 6. `stats.py` (Klasse: StatsManager)
- **Funktion**: Statistikverwaltung
- **Metriken**:
  - Empfangene Nachrichten
  - Gesendete Nachrichten
  - Fehleranzahl
  - Uptime

### Konfigurationsparameter

```json
{
    "mqtt": {
        "broker": "localhost",           // MQTT-Broker-Adresse
        "port": 1883,                   // MQTT-Port
        "username": null,               // Optional: MQTT-Benutzername
        "password": null,               // Optional: MQTT-Passwort
        "topic": "application/+/device/+/event/up",  // MQTT-Topic-Pattern
        "keepalive": 60,                // MQTT Keep-Alive in Sekunden
        "reconnect_delay_min": 1,       // Min. Wiederverbindungsverzögerung
        "reconnect_delay_max": 120      // Max. Wiederverbindungsverzögerung
    },
    "uart": {
        "port": "/dev/ttyAMA0",         // UART-Port (Linux/Windows)
        "baudrate": 115200,             // Baudrate
        "bytesize": 8,                  // Datenbits
        "parity": "none",               // Parität: none/even/odd
        "stopbits": 1,                  // Stopbits
        "timeout": 1,                   // Timeout in Sekunden
        "xonxoff": false,               // Software Flow Control
        "rtscts": false,                // Hardware Flow Control (RTS/CTS)
        "dsrdtr": false,                // Hardware Flow Control (DSR/DTR)
        "max_payload_size": 255         // Maximale Payload-Größe in Bytes
    },
    "logging": {
        "level": "DEBUG",               // Log-Level
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": "chirpstack_bridge.log", // Log-Datei
        "max_file_size": "10MB",        // Max. Log-Dateigröße
        "backup_count": 5               // Anzahl Backup-Dateien
    },
    "system": {
        "stats_interval": 300,          // Statistik-Ausgabe-Intervall (Sek.)
        "retry_attempts": 3,            // Wiederholungsversuche
        "retry_delay": 0.5,             // Verzögerung zwischen Versuchen
        "graceful_shutdown_timeout": 5  // Shutdown-Timeout
    }
}
```

### Fehlerbehandlung

1. **MQTT-Fehler**: Automatische Wiederverbindung mit exponentieller Backoff-Strategie
2. **UART-Fehler**: 3 Wiederholungsversuche mit konfigurierbarer Verzögerung
3. **Dekodierungsfehler**: Fehler werden geloggt, Nachricht wird verworfen
4. **JSON-Parse-Fehler**: Detailliertes Error-Logging mit Payload-Ausgabe

### Debug-Ausgaben (bei LOG_LEVEL=DEBUG)

- Raw MQTT Payload
- Parsed JSON-Struktur
- Device-Name Extraktion
- Base64-dekodierte Daten (Hex-Format)
- UART-Sendebestätigung

### Performance-Metriken

- Nachrichten pro Sekunde: Abhängig von MQTT-Traffic
- UART-Durchsatz: Bis zu 115200 baud
- Memory-Footprint: ~20-50 MB RAM
- CPU-Auslastung: Minimal (<5% bei normaler Last)

### Systemanforderungen

- Python 3.6+
- pyserial>=3.5
- paho-mqtt>=1.6.1
- Betriebssystem: Linux, Windows, macOS
- UART-Zugriff (Benutzerrechte erforderlich)

### Typische Anwendungsfälle

1. **LoRaWAN zu serieller Schnittstelle**: Weiterleitung von LoRaWAN-Gerätedaten
2. **IoT-Gateway**: Verbindung von Cloud-basierten Diensten mit lokaler Hardware
3. **Datenlogger**: Protokollierung von Sensordaten über serielle Schnittstelle
4. **Protokoll-Konverter**: MQTT zu UART Protokollübersetzung

### Bekannte Einschränkungen

- Maximale Payload-Größe: 255 Bytes (konfigurierbar)
- Keine bidirektionale Kommunikation (nur MQTT → UART)
- Keine Verschlüsselung der UART-Kommunikation
- Single-threaded MQTT-Loop (kann bei sehr hoher Last limitierend sein)

### Erweiterungsmöglichkeiten

1. Bidirektionale Kommunikation (UART → MQTT)
2. Mehrere UART-Ports gleichzeitig
3. Nachrichtenpufferung bei Verbindungsverlust
4. Erweiterte Protokollunterstützung (z.B. Modbus)
5. Web-Interface für Konfiguration und Monitoring
