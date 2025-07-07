#!/usr/bin/env python3
"""
LoRaWAN Gateway Monitor mit SF-Logging
- Überprüft, ob der Forwarder und ChirpStack laufen
- Liest Daten über MQTT und gibt sie im Serial Monitor aus
- Loggt auch den Spreading Factor (sf) und speichert in CSV
- Startet Services automatisch bei Bedarf
"""

import json
import base64
import paho.mqtt.client as mqtt
from datetime import datetime
import subprocess
import os
import time
import logging
import csv

# Konfiguration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "application/+/device/+/event/+"
PACKET_FORWARDER_PATH = "/home/pi/sx1302_hal/packet_forwarder"
CSV_FILE = "lorawan_data.csv"

# Logging einrichten
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LoRaWANGatewayMonitor:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.init_csv()

    def init_csv(self):
        """Initialisiert die CSV-Datei mit Headern falls sie nicht existiert"""
        if not os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['timestamp', 'application_id', 'device_eui', 'event_type', 'data', 'sf', 'rssi', 'snr', 'gateway_id'])
            print(f"📊 CSV-Datei erstellt: {CSV_FILE}")

    def write_to_csv(self, timestamp, app_id, device_eui, event_type, data, sf, rssi, snr, gateway_id):
        """Schreibt Daten in die CSV-Datei"""
        try:
            with open(CSV_FILE, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([timestamp, app_id, device_eui, event_type, data, sf, rssi, snr, gateway_id])
        except Exception as e:
            print(f"❌ Fehler beim Schreiben in CSV: {e}")

    def check_service(self, name):
        """Prüft den Status eines systemd-Service"""
        try:
            result = subprocess.run(['systemctl', 'is-active', name], 
                                  capture_output=True, text=True)
            is_active = result.returncode == 0
            status = "✅ AKTIV" if is_active else "❌ INAKTIV"
            print(f"   {name}: {status}")
            return is_active
        except Exception as e:
            print(f"   {name}: ❌ FEHLER - {e}")
            return False

    def check_process(self, name):
        """Prüft, ob ein Prozess läuft"""
        try:
            result = subprocess.run(['pgrep', '-f', name], 
                                  capture_output=True, text=True)
            is_running = result.returncode == 0
            status = "✅ LÄUFT" if is_running else "❌ GESTOPPT"
            print(f"   {name}: {status}")
            return is_running
        except Exception as e:
            print(f"   {name}: ❌ FEHLER - {e}")
            return False

    def start_service(self, name):
        """Startet einen systemd-Service falls nicht aktiv"""
        if not self.check_service(name):
            print(f"🔄 Starte Service: {name}")
            try:
                result = subprocess.run(['sudo', 'systemctl', 'start', name], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ {name} erfolgreich gestartet")
                    return True
                else:
                    print(f"❌ Fehler beim Starten von {name}: {result.stderr}")
                    return False
            except Exception as e:
                print(f"❌ Exception beim Starten von {name}: {e}")
                return False
        return True

    def start_packet_forwarder(self):
        """Startet den Packet Forwarder falls nicht aktiv"""
        if not self.check_process('lora_pkt_fwd'):
            print("🔄 Starte Packet Forwarder...")
            try:
                if os.path.exists(PACKET_FORWARDER_PATH):
                    os.chdir(PACKET_FORWARDER_PATH)
                    subprocess.Popen(['sudo', './lora_pkt_fwd'], 
                                   stdout=subprocess.DEVNULL, 
                                   stderr=subprocess.DEVNULL)
                    time.sleep(3)
                    if self.check_process('lora_pkt_fwd'):
                        print("✅ Packet Forwarder erfolgreich gestartet")
                        return True
                    else:
                        print("❌ Packet Forwarder konnte nicht gestartet werden")
                        return False
                else:
                    print(f"❌ Packet Forwarder Pfad nicht gefunden: {PACKET_FORWARDER_PATH}")
                    return False
            except Exception as e:
                print(f"❌ Fehler beim Starten des Packet Forwarders: {e}")
                return False
        return True

    def system_check(self):
        """Führt kompletten System-Check durch"""
        print("\n" + "="*60)
        print("🔍 LoRaWAN SYSTEM CHECK")
        print("="*60)
        
        print("\n📋 Service Status:")
        services_ok = True
        services_ok &= self.start_service('mosquitto')
        services_ok &= self.start_service('chirpstack-gateway-bridge')
        services_ok &= self.start_packet_forwarder()
        
        print("\n🌐 Connectivity Check:")
        try:
            # MQTT Connectivity testen
            test_client = mqtt.Client()
            test_client.connect(MQTT_BROKER, MQTT_PORT, 10)
            test_client.disconnect()
            print("   MQTT Broker: ✅ ERREICHBAR")
        except Exception as e:
            print(f"   MQTT Broker: ❌ NICHT ERREICHBAR - {e}")
            services_ok = False
        
        if services_ok:
            print("\n🎉 Alle Services sind bereit!")
        else:
            print("\n⚠️  Einige Services haben Probleme")
        
        print("="*60)
        return services_ok

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"\n📡 Verbunden mit MQTT Broker ({MQTT_BROKER}:{MQTT_PORT})")
            print(f"🎯 Lausche auf Topic: {MQTT_TOPIC}")
            print(f"📊 CSV-Datei: {CSV_FILE}")
            print("\n" + "="*60)
            print("📊 LIVE DATA MONITOR - Warte auf LoRa-Nachrichten...")
            print("="*60)
            client.subscribe(MQTT_TOPIC)
        else:
            logger.error(f"❌ MQTT-Verbindung fehlgeschlagen mit Code: {rc}")

    def on_disconnect(self, client, userdata, rc):
        print("\n🔌 Verbindung zum MQTT Broker getrennt")
        print("🔄 Führe System-Check durch...")
        time.sleep(2)
        self.system_check()

    def on_message(self, client, userdata, msg):
        try:
            # Topic parsen
            topic_parts = msg.topic.split('/')
            application_id = topic_parts[1] if len(topic_parts) > 1 else "unknown"
            device_eui = topic_parts[3] if len(topic_parts) > 3 else "unknown"
            event_type = topic_parts[5] if len(topic_parts) > 5 else "unknown"
            
            # Payload dekodieren
            payload = json.loads(msg.payload.decode())
            
            # Timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Header ausgeben
            print(f"\n{'='*60}")
            print(f"🕐 {timestamp}")
            print(f"📱 App: {application_id} | 🔷 Device: {device_eui} | 📊 Type: {event_type}")
            print(f"{'='*60}")
            
            # Event-spezifische Behandlung
            if event_type == "up":
                self.handle_uplink(payload, timestamp, application_id, device_eui, event_type)
            elif event_type == "join":
                self.handle_join(payload)
            elif event_type == "status":
                self.handle_status(payload)
            else:
                print("📝 Raw Data:")
                print(json.dumps(payload, indent=2))
                
        except Exception as e:
            print(f"❌ Fehler beim Verarbeiten der Nachricht: {e}")
            print(f"Raw Topic: {msg.topic}")
            print(f"Raw Payload: {msg.payload}")

    def handle_uplink(self, data, timestamp, app_id, device_eui, event_type):
        """Behandelt Uplink-Nachrichten (Daten von Geräten)"""
        print("📈 UPLINK DATA:")
        
        # Frame Info
        if 'fCnt' in data:
            print(f"   📊 Frame Count: {data['fCnt']}")
        if 'fPort' in data:
            print(f"   🚪 Port: {data['fPort']}")
        
        # Spreading Factor extrahieren
        sf = "N/A"
        if 'txInfo' in data and 'modulation' in data['txInfo']:
            modulation = data['txInfo']['modulation']
            if 'lora' in modulation:
                sf = modulation['lora'].get('spreadingFactor', 'N/A')
                print(f"   📊 Spreading Factor: SF{sf}")
        
        # Payload dekodieren
        decoded_data = ""
        if 'data' in data:
            raw_data = data['data']
            print(f"   📦 Raw (Base64): {raw_data}")
            
            try:
                decoded_bytes = base64.b64decode(raw_data)
                decoded_data = decoded_bytes.hex().upper()
                print(f"   🔢 Hex: {decoded_data}")
                print(f"   📋 Bytes: {list(decoded_bytes)}")
                
                # Versuche JSON zu parsen (für strukturierte Daten wie {"d":[23.3,24.8],"sf":9,"t":18})
                try:
                    ascii_data = decoded_bytes.decode('ascii')
                    json_data = json.loads(ascii_data)
                    print(f"   📝 JSON Data: {json_data}")
                    
                    # Wenn SF im JSON enthalten ist, verwende diesen
                    if 'sf' in json_data:
                        sf = json_data['sf']
                        print(f"   🎯 SF aus Payload: SF{sf}")
                    
                    # Weitere Daten extrahieren
                    if 'd' in json_data:
                        print(f"   📊 Sensor Data: {json_data['d']}")
                    if 't' in json_data:
                        print(f"   🕐 Timestamp: {json_data['t']}")
                        
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # ASCII versuchen
                    try:
                        ascii_data = decoded_bytes.decode('ascii')
                        print(f"   📝 ASCII: '{ascii_data}'")
                    except:
                        pass
                    
            except Exception as e:
                print(f"   ❌ Dekodierung fehlgeschlagen: {e}")
        
        # Gateway Info
        gateway_id = "N/A"
        rssi = "N/A"
        snr = "N/A"
        
        if 'rxInfo' in data and data['rxInfo']:
            print("   📡 Gateway Info:")
            for i, rx in enumerate(data['rxInfo']):
                gateway_id = rx.get('gatewayId', 'unknown')[:16] + "..."
                rssi = rx.get('rssi', 'N/A')
                snr = rx.get('snr', 'N/A')
                print(f"      📶 {gateway_id} | RSSI: {rssi}dBm | SNR: {snr}dB")
                
                # Nur ersten Gateway für CSV verwenden
                if i == 0:
                    gateway_id = rx.get('gatewayId', 'unknown')
                    rssi = rx.get('rssi', 'N/A')
                    snr = rx.get('snr', 'N/A')
        
        # In CSV speichern
        self.write_to_csv(timestamp, app_id, device_eui, event_type, decoded_data, sf, rssi, snr, gateway_id)
        print(f"   💾 Daten in CSV gespeichert (SF: {sf})")

    def handle_join(self, data):
        """Behandelt Join-Events"""
        print("🔗 JOIN EVENT:")
        if 'devEui' in data:
            print(f"   🆔 Device EUI: {data['devEui']}")
        if 'devAddr' in data:
            print(f"   📍 Device Addr: {data['devAddr']}")
        print("   ✅ Gerät erfolgreich dem Netzwerk beigetreten!")

    def handle_status(self, data):
        """Behandelt Status-Updates"""
        print("📊 STATUS UPDATE:")
        if 'batteryLevel' in data:
            battery = data['batteryLevel']
            battery_icon = "🔋" if battery > 50 else "🪫" if battery > 20 else "⚠️"
            print(f"   {battery_icon} Batterie: {battery}%")
        if 'margin' in data:
            print(f"   📶 Signal Margin: {data['margin']} dB")

    def start(self):
        """Startet den Gateway Monitor"""
        try:
            print("🚀 LoRaWAN Gateway Monitor mit SF-Logging gestartet")
            print("="*60)
            
            # System Check
            if not self.system_check():
                print("\n⚠️  Warnung: Nicht alle Services konnten gestartet werden")
                print("Monitor läuft trotzdem weiter...")
            
            time.sleep(2)
            
            # MQTT Listener starten
            print("\n📡 Starte MQTT Listener...")
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            print("\n\n👋 Monitor gestoppt durch Benutzer")
        except Exception as e:
            print(f"\n❌ Fehler: {e}")
        finally:
            self.client.disconnect()
            print("🔌 MQTT-Verbindung getrennt")

def main():
    monitor = LoRaWANGatewayMonitor()
    monitor.start()

if __name__ == "__main__":
    main()
