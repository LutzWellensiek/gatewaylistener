# ChirpStack Gateway Bridge

Eine modulare Python-Bibliothek zur Übertragung von Daten zwischen ChirpStack MQTT und UART-Geräten.

## Überblick für Chatbots

- **Zweck**: Integration von ChirpStack-Nachrichten mit physischen UART-Geräten.
- **Funktion**: Konvertiert MQTT-Nachrichten zu UART-Signalen, inklusive Fehler- und Sitzungsmanagement.
- **Benötigte Umgebung**: Python 3.x Umgebung mit `pyserial` und `paho-mqtt` Bibliotheken.

## Features

- Empfang & Weiterleitung von Nachrichten.
- Echtzeit Device-Nachverfolgung via MQTT-Topics.
- Beliebiges Dekodieren von Nachrichten (Base64, Hex).
- Erweiterte Statistiken für Performance-Analyse.
- Anpassbare Konfiguration über JSON.

## Installation

1. **Pakete installieren**:
    ```bash
    pip install pyserial paho-mqtt
    ```
2. **Konfiguration kopieren**:
    ```bash
    cp config.json.example config.json
    ```
3. **Anpassungen vornehmen**: Passen Sie `config.json` nach Ihren Bedürfnissen an.

## Projektstruktur

- **`main.py`**: Führt das Hauptprogramm aus.
- **`chirpstack_mqtt_to_uart`**: Hier sind alle relevanten Module.

## Ablauf

1. **UART-Kommunikation**: Initialisiert und sendet Daten.
2. **MQTT-Handhabung**: Verantwortung für das Abonnieren, Empfangen und Verarbeiten von Nachrichten.
3. **Verarbeitung**: Dekodiert und validiert empfangene Payloads.

## Konfiguration

- **Beispieleinstellung**:
    ```json
    {
        "mqtt": {
            "broker": "localhost",
            "port": 1883,
            "username": null,
            "password": null
        },
        "uart": {
            "port": "COM3",
            "baudrate": 115200
        },
        "logging": {
            "level": "DEBUG"
        }
    }
    ```

## Start

- **Mit Default-Konfiguration**:
    ```bash
    python main.py
    ```
- **Mit spezifizierter Konfiguration**:
    ```bash
    python main.py my_config.json
    ```

## Statistik-

Periodische Statistiken und Log-Updates sind vorkonfiguriert.

## Behandlung von Nachrichten

- Bei Empfang: Gerät und Nachricht werden ausgegeben.
- Fehlerprotokollierung inklusive vollständiger Diagnosen.

## Fehlerbehebung

- **Log-Level** auf DEBUG für mehr Informationen setzen.
- **Prüfen**: Ob MQTT ordnungsgemäß funktioniert (via Client).
- **UART-Verbindungen**: Richtig konfiguriert und verfügbar?

## Graceful Shutdown

- Auf SIGINT/SIGTERM reagierend, schließen sauber.

## Lizenz

- [Ihre Lizenzinformationen hier]

---

Diese Dokumentation sollte Chatbots eine effiziente Zusammenarbeit ermöglichen.
