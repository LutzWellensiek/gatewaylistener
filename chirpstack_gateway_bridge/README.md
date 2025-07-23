# ChirpStack Gateway Bridge

Eine modulare Python-Bibliothek für die Kommunikation zwischen ChirpStack (über MQTT) und UART-Geräten.

## Features

- Empfängt MQTT-Nachrichten von ChirpStack
- Extrahiert Device-Namen aus MQTT-Topics
- Dekodiert Base64- und Hex-kodierte Payloads
- Sendet Daten über UART mit Device-Identifikation
- Umfangreiche Fehlerbehandlung und Wiederholungsmechanismen
- Detaillierte Statistiken und Logging
- Konfigurierbar über JSON-Datei

## Installation

1. Abhängigkeiten installieren:
```bash
pip install pyserial paho-mqtt
```

2. Konfigurationsdatei erstellen:
```bash
cp config.json.example config.json
```

3. Konfiguration anpassen (siehe unten)

## Konfiguration

Die Konfiguration erfolgt über eine JSON-Datei. Beispiel:

```json
{
    "mqtt": {
        "broker": "localhost",
        "port": 1883,
        "username": null,
        "password": null,
        "topic": "application/+/device/+/event/up"
    },
    "uart": {
        "port": "COM3",  // Windows: "COM3", Linux: "/dev/ttyUSB0"
        "baudrate": 115200
    },
    "logging": {
        "level": "DEBUG",  // DEBUG, INFO, WARNING, ERROR
        "file": "chirpstack_bridge.log"
    }
}
```

## Verwendung

### Starten der Bridge:
```bash
python main.py
```

### Mit eigener Konfigurationsdatei:
```bash
python main.py my_config.json
```

## Projektstruktur

```
chirpstack_gateway_bridge/
├── chirpstack_mqtt_to_uart/      # Library-Module
│   ├── __init__.py              # Package-Initialisierung
│   ├── config.py                # Konfigurationsverwaltung
│   ├── logger.py                # Logging-Setup
│   ├── uart_comm.py             # UART-Kommunikation
│   ├── mqtt_handler.py          # MQTT-Handling
│   ├── processor.py             # Nachrichtenverarbeitung
│   └── stats.py                 # Statistikverwaltung
├── main.py                      # Hauptskript
├── config.json.example          # Beispielkonfiguration
└── README.md                    # Diese Datei
```

## Nachrichtenformat

Die Bridge erwartet MQTT-Nachrichten im ChirpStack-Format mit Base64-kodierter Payload.

Ausgabe über UART:
```
<device_name>: <decoded_payload>
```

## Debugging

Bei Problemen:

1. Log-Level auf "DEBUG" setzen
2. Log-Datei überprüfen (standardmäßig `chirpstack_bridge.log`)
3. Überprüfen Sie die MQTT-Verbindung mit einem MQTT-Client
4. Überprüfen Sie die UART-Verbindung und Berechtigungen

## Fehlerbehandlung

- Automatische Wiederverbindung bei MQTT-Verbindungsverlust
- Wiederholungsversuche bei UART-Fehlern
- Validierung der Payload-Größe
- Graceful Shutdown bei SIGINT/SIGTERM

## Lizenz

[Ihre Lizenz hier]
