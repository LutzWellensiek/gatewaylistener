# Gateway Listener - LoRaWAN Endnode Verbindungsanleitung

## Übersicht
Dieses Repository enthält Tools und Anleitungen für die Verbindung von LoRaWAN-Endnodes mit einem ChirpStack-Gateway.

## Inhalt
- `chirpstack_mqtt_listener.py` - Python-Skript zum Überwachen von MQTT-Nachrichten vom ChirpStack

## Endnode Verbindungsanleitung

### 1. Voraussetzungen
- ChirpStack Gateway Bridge läuft auf dem Gateway
- ChirpStack Server ist konfiguriert und läuft
- Endnode (z.B. ESP32 mit LoRa-Modul) ist programmiert

### 2. ChirpStack Konfiguration

#### Application erstellen
1. Öffnen Sie die ChirpStack Web-Oberfläche (normalerweise http://gateway-ip:8080)
2. Gehen Sie zu "Applications"
3. Klicken Sie auf "Create" um eine neue Application zu erstellen
4. Geben Sie einen Namen ein (z.B. "IoT-Sensoren")
5. Speichern Sie die Application

#### Device Profile erstellen
1. Gehen Sie zu "Device profiles"
2. Klicken Sie auf "Create"
3. Konfigurieren Sie das Profil:
   - Name: z.B. "ESP32-LoRa-Profile"
   - LoRaWAN MAC version: 1.0.3 (oder entsprechend Ihrem Endnode)
   - Regional Parameters revision: A
   - Uplink interval: je nach Bedarf (z.B. 60 Sekunden)
   - ADR enabled: aktivieren für adaptive Datenrate
4. Speichern Sie das Profil

#### Device hinzufügen
1. Gehen Sie zu Ihrer Application
2. Klicken Sie auf "Create" unter Devices
3. Geben Sie die Device-Informationen ein:
   - Name: Beschreibender Name für Ihr Gerät
   - Device EUI: 64-bit Identifier Ihres Endnodes
   - Application key: 128-bit AES Key (wird auf dem Endnode verwendet)
4. Wählen Sie das zuvor erstellte Device Profile
5. Speichern Sie das Device

### 3. Endnode Programmierung

#### Beispiel-Konfiguration für ESP32 mit LMIC Library:
```cpp
// Device EUI (8 bytes, little-endian)
static const u1_t PROGMEM DEVEUI[8] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };

// Application EUI (8 bytes, little-endian) 
static const u1_t PROGMEM APPEUI[8] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };

// Application Key (16 bytes)
static const u1_t PROGMEM APPKEY[16] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
```

**Wichtig:** Ersetzen Sie die Null-Werte mit den tatsächlichen Werten aus ChirpStack!

### 4. Verbindung testen

#### Gateway Status prüfen:
```bash
# ChirpStack Gateway Bridge Status
sudo systemctl status chirpstack-gateway-bridge

# ChirpStack Server Status  
sudo systemctl status chirpstack

# MQTT Nachrichten überwachen
python3 chirpstack_mqtt_listener.py
```

#### Logs überprüfen:
```bash
# Gateway Bridge Logs
sudo journalctl -u chirpstack-gateway-bridge -f

# ChirpStack Server Logs
sudo journalctl -u chirpstack -f
```

### 5. Troubleshooting

#### Häufige Probleme:
1. **Endnode sendet, aber wird nicht empfangen:**
   - Prüfen Sie die Frequenz-Einstellungen (EU868, US915, etc.)
   - Überprüfen Sie die Reichweite zwischen Gateway und Endnode
   - Kontrollieren Sie die Spreading Factor (SF) Einstellungen

2. **Join-Request schlägt fehl:**
   - Überprüfen Sie DevEUI, AppEUI und AppKey
   - Stellen Sie sicher, dass das Device in ChirpStack aktiviert ist
   - Prüfen Sie die LoRaWAN-Version Kompatibilität

3. **Keine Nachrichten in ChirpStack:**
   - Überprüfen Sie die Gateway-Verbindung
   - Kontrollieren Sie die MQTT-Broker Konfiguration
   - Prüfen Sie die Firewall-Einstellungen

### 6. Monitoring

Das beiliegende Python-Skript `chirpstack_mqtt_listener.py` kann verwendet werden, um:
- MQTT-Nachrichten vom ChirpStack zu überwachen
- Join-Requests und Uplink-Nachrichten zu protokollieren
- Debugging-Informationen zu sammeln

#### Verwendung:
```bash
python3 chirpstack_mqtt_listener.py
```

### 7. Nützliche Befehle

```bash
# Gateway Bridge Konfiguration anzeigen
cat /etc/chirpstack-gateway-bridge/chirpstack-gateway-bridge.toml

# ChirpStack Konfiguration anzeigen
cat /etc/chirpstack/chirpstack.toml

# MQTT Topics anzeigen
mosquitto_sub -h localhost -t "gateway/+/event/+"
```

## Support
Bei Problemen überprüfen Sie die offiziellen ChirpStack Dokumentation: https://www.chirpstack.io/docs/

## Lizenz
Dieses Projekt steht unter der MIT-Lizenz.
