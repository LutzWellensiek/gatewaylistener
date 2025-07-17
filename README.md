# ChirpStack MQTT to UART Bridge

Der ChirpStack MQTT to UART Bridge ist eine Python-basierte Lösung, die MQTT-Nachrichten abhört und dekodierte Payload-Daten zusammen mit dem Device-Namen über UART sendet. Diese Bridge ist besonders nützlich für Anwendungen mit LoRaWAN-Geräten, die über UART-Schnittstellen kommunizieren.

## Features

- Hört auf konfigurierte MQTT-Topics
- Extrahiert Device-Namen aus MQTT-Topics
- Dekodiert Payload von Base64, optional auch von ASCII-Hex
- Formatiert Nachrichten als `DEVICE_NAME:PAYLOAD_HEX\n` vor dem Senden über UART
- Protokolliert Nachrichten und Fehler in rotierende Log-Dateien
- Robuste Fehlerbehandlung und Wiederverbindung

## Datenformat

### MQTT Topic Format
```
application/{app_id}/device/{device_id}/event/up
```

### UART Output Format
```
DEVICE_NAME:PAYLOAD_HEX\n
```

## Beispiele

### Beispiel 1: Einfache Textnachricht
**MQTT Topic:** `application/1/device/sensor_01/event/up`
**Payload (Base64):** `SGVsbG8gV29ybGQ=` (dekodiert: "Hello World")
**UART Output:** `sensor_01:48656c6c6f20576f726c64`

### Beispiel 2: Temperatur-Sensor
**MQTT Topic:** `application/weather/device/temp_sensor_kitchen/event/up`
**Payload (Base64):** `MTIzNA==` (dekodiert: "1234")
**UART Output:** `temp_sensor_kitchen:31323334`

### Beispiel 3: Binäre Daten
**MQTT Topic:** `application/iot/device/device_123/event/up`
**Payload (Hex als ASCII):** `1a2b3c4d`
**UART Output:** `device_123:1a2b3c4d`

## Empfangen der Daten

### Arduino/ESP32 Beispiel

```cpp
#include <SoftwareSerial.h>

SoftwareSerial uart(2, 3); // RX, TX pins

void setup() {
    Serial.begin(115200);
    uart.begin(115200);
    Serial.println("Waiting for UART messages...");
}

void loop() {
    if (uart.available()) {
        String message = uart.readStringUntil('\n');
        
        // Parse device name and payload
        int colonIndex = message.indexOf(':');
        if (colonIndex > 0) {
            String deviceName = message.substring(0, colonIndex);
            String payloadHex = message.substring(colonIndex + 1);
            
            Serial.println("Device: " + deviceName);
            Serial.println("Payload (Hex): " + payloadHex);
            
            // Convert hex to bytes
            processHexPayload(payloadHex);
        }
    }
}

void processHexPayload(String hexString) {
    // Beispiel: Hex-String in Bytes konvertieren
    for (int i = 0; i < hexString.length(); i += 2) {
        String byteString = hexString.substring(i, i + 2);
        byte b = (byte) strtol(byteString.c_str(), NULL, 16);
        Serial.print("Byte: 0x");
        Serial.println(b, HEX);
    }
}
```

### Python Empfänger Beispiel

```python
import serial
import binascii
import time

def parse_uart_message(message):
    """Parse UART message: DEVICE_NAME:PAYLOAD_HEX"""
    try:
        parts = message.strip().split(':', 1)
        if len(parts) == 2:
            device_name = parts[0]
            payload_hex = parts[1]
            
            # Convert hex to bytes
            payload_bytes = binascii.unhexlify(payload_hex)
            
            return device_name, payload_bytes
    except Exception as e:
        print(f"Error parsing message: {e}")
    
    return None, None

def main():
    # UART Setup
    ser = serial.Serial('/dev/ttyAMA0', 115200, timeout=1)
    
    print("Listening for UART messages...")
    
    try:
        while True:
            if ser.in_waiting > 0:
                message = ser.readline().decode('utf-8')
                
                device_name, payload = parse_uart_message(message)
                if device_name and payload:
                    print(f"Device: {device_name}")
                    print(f"Payload (Hex): {payload.hex()}")
                    print(f"Payload (ASCII): {payload.decode('ascii', errors='ignore')}")
                    print("---")
                    
                    # Process based on device name
                    if device_name.startswith('temp_'):
                        process_temperature_data(payload)
                    elif device_name.startswith('sensor_'):
                        process_sensor_data(payload)
                    
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        ser.close()

def process_temperature_data(payload):
    """Process temperature sensor data"""
    if len(payload) >= 2:
        temp = int.from_bytes(payload[:2], byteorder='big')
        print(f"Temperature: {temp/10}°C")

def process_sensor_data(payload):
    """Process generic sensor data"""
    print(f"Sensor data: {payload}")

if __name__ == "__main__":
    main()
```

### Node.js Empfänger Beispiel

```javascript
const SerialPort = require('serialport');
const Readline = require('@serialport/parser-readline');

const port = new SerialPort('/dev/ttyAMA0', { baudRate: 115200 });
const parser = port.pipe(new Readline({ delimiter: '\n' }));

parser.on('data', (data) => {
    const message = data.toString().trim();
    
    // Parse message: DEVICE_NAME:PAYLOAD_HEX
    const [deviceName, payloadHex] = message.split(':', 2);
    
    if (deviceName && payloadHex) {
        console.log(`Device: ${deviceName}`);
        console.log(`Payload (Hex): ${payloadHex}`);
        
        // Convert hex to buffer
        const payload = Buffer.from(payloadHex, 'hex');
        console.log(`Payload (ASCII): ${payload.toString('ascii')}`);
        
        // Process based on device type
        processDeviceData(deviceName, payload);
    }
});

function processDeviceData(deviceName, payload) {
    if (deviceName.includes('temp')) {
        // Temperature sensor
        if (payload.length >= 2) {
            const temp = payload.readInt16BE(0) / 10;
            console.log(`Temperature: ${temp}°C`);
        }
    } else if (deviceName.includes('humidity')) {
        // Humidity sensor
        if (payload.length >= 1) {
            const humidity = payload.readUInt8(0);
            console.log(`Humidity: ${humidity}%`);
        }
    }
    
    console.log('---');
}

port.on('open', () => {
    console.log('UART connection opened');
});

port.on('error', (err) => {
    console.error('Error:', err);
});
```

## Installation und Verwendung

1. **Abhängigkeiten installieren:**
   ```bash
   pip install paho-mqtt pyserial
   ```

2. **Konfiguration anpassen:**
   Bearbeiten Sie `config.json` entsprechend Ihrer MQTT- und UART-Einstellungen.

3. **Bridge starten:**
   ```bash
   python3 chirpstack_mqtt_to_uart.py config.json
   ```

4. **Logs überwachen:**
   ```bash
   tail -f chirpstack_bridge.log
   ```

## Konfiguration

Beispiel `config.json`:

```json
{
    "mqtt": {
        "broker": "localhost",
        "port": 1883,
        "username": null,
        "password": null,
        "topic": "application/+/device/+/event/up",
        "keepalive": 60
    },
    "uart": {
        "port": "/dev/ttyAMA0",
        "baudrate": 115200,
        "bytesize": 8,
        "parity": "none",
        "stopbits": 1,
        "timeout": 1,
        "max_payload_size": 255
    },
    "logging": {
        "level": "INFO",
        "file": "chirpstack_bridge.log",
        "max_file_size": "10MB",
        "backup_count": 5
    },
    "system": {
        "stats_interval": 300,
        "retry_attempts": 3,
        "retry_delay": 0.5
    }
}
```

## Payload-Dekodierung

Die Bridge unterstützt verschiedene Payload-Formate:

1. **Base64**: Standard-Kodierung für MQTT-Nachrichten
2. **ASCII-Hex**: Doppelt kodierte Hex-Strings
3. **Binäre Daten**: Direkte Byte-Daten

### Beispiel Payload-Verarbeitung

```python
# Base64 -> Bytes
base64_payload = "SGVsbG8gV29ybGQ="  # "Hello World"
decoded = base64.b64decode(base64_payload)
hex_output = decoded.hex()  # "48656c6c6f20576f726c64"

# ASCII-Hex -> Bytes
ascii_hex = "48656c6c6f20576f726c64"
bytes_data = binascii.unhexlify(ascii_hex)
text = bytes_data.decode('ascii')  # "Hello World"
```

## Fehlerbehandlung

Die Bridge implementiert robuste Fehlerbehandlung:

- **MQTT-Verbindungsfehler**: Automatische Wiederverbindung
- **UART-Fehler**: Retry-Mechanismus mit konfigurierbarer Anzahl
- **Payload-Dekodierungsfehler**: Überspringen fehlerhafter Nachrichten
- **Logging**: Alle Fehler werden protokolliert

## Monitoring

Statistiken werden regelmäßig geloggt:

```
Statistiken - Uptime: 01:23:45, Empfangen: 156, Gesendet: 154, Fehler: 2
```

## Systemd Service

Für den Produktivbetrieb können Sie einen systemd-Service erstellen:

```ini
[Unit]
Description=ChirpStack MQTT to UART Bridge
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/gatewaylistener
ExecStart=/usr/bin/python3 /home/pi/gatewaylistener/chirpstack_mqtt_to_uart.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

### Häufige Probleme

1. **UART-Zugriff verweigert**: Benutzer zur `dialout`-Gruppe hinzufügen
2. **MQTT-Verbindung fehlgeschlagen**: Broker-Einstellungen überprüfen
3. **Payload-Dekodierung fehlgeschlagen**: Base64-Format der Eingangsdaten prüfen

### Debug-Modus

Setzen Sie den Log-Level auf `DEBUG` für detaillierte Ausgaben:

```json
{
    "logging": {
        "level": "DEBUG"
    }
}
```
