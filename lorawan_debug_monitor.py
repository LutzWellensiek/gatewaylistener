#!/usr/bin/env python3
"""
Debug-Version des LoRaWAN Monitors
Zeigt alle empfangenen MQTT-Daten im Detail an
"""

import json
import base64
import paho.mqtt.client as mqtt
from datetime import datetime
import logging

# Konfiguration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "application/+/device/+/event/+"

# Logging einrichten
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LoRaWANDebugMonitor:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("✅ Erfolgreich mit MQTT Broker verbunden!")
            client.subscribe(MQTT_TOPIC)
            logger.info(f"📡 Lausche auf Topic: {MQTT_TOPIC}")
        else:
            logger.error(f"❌ MQTT-Verbindung fehlgeschlagen mit Code: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        logger.warning("🔌 Verbindung zum MQTT Broker getrennt")
    
    def print_nested_dict(self, data, indent=0):
        """Druckt verschachtelte Dictionaries übersichtlich"""
        spaces = "  " * indent
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    print(f"{spaces}{key}:")
                    self.print_nested_dict(value, indent + 1)
                else:
                    print(f"{spaces}{key}: {value}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                print(f"{spaces}[{i}]:")
                self.print_nested_dict(item, indent + 1)
        else:
            print(f"{spaces}{data}")

    def on_message(self, client, userdata, msg):
        try:
            # Topic parsen
            topic_parts = msg.topic.split('/')
            application_id = topic_parts[1]
            device_eui = topic_parts[3]
            event_type = topic_parts[5]
            
            # Payload dekodieren
            payload = json.loads(msg.payload.decode())
            
            # Timestamp hinzufügen
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"\n{'='*80}")
            print(f"🕐 Zeit: {timestamp}")
            print(f"📱 Application ID: {application_id}")
            print(f"🔷 Device EUI: {device_eui}")
            print(f"📊 Event Type: {event_type}")
            print(f"📡 Full Topic: {msg.topic}")
            print(f"{'='*80}")
            
            print("📝 VOLLSTÄNDIGE PAYLOAD-STRUKTUR:")
            print("-" * 50)
            self.print_nested_dict(payload)
            
            # Zusätzlich: Nach GPS-relevanten Feldern suchen
            print("\n🔍 SUCHE NACH GPS-RELEVANTEN FELDERN:")
            print("-" * 50)
            self.search_gps_fields(payload)
            
            # Payload auch als JSON ausgeben
            print("\n📄 RAW JSON:")
            print("-" * 50)
            print(json.dumps(payload, indent=2))
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Verarbeiten der Nachricht: {e}")
            print(f"Raw message: {msg.payload}")

    def search_gps_fields(self, data, path=""):
        """Sucht rekursiv nach GPS-relevanten Feldern"""
        gps_keywords = ['latitude', 'longitude', 'lat', 'lon', 'lng', 'location', 'position', 'gps', 'coordinates', 'altitude', 'alt']
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                
                # Prüfe ob der Schlüssel GPS-relevant ist
                if key.lower() in gps_keywords:
                    print(f"🌍 GPS-Feld gefunden: {current_path} = {value}")
                
                # Rekursiv weitersuchen
                if isinstance(value, (dict, list)):
                    self.search_gps_fields(value, current_path)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                self.search_gps_fields(item, current_path)

    def start(self):
        """Startet den Debug Monitor"""
        try:
            logger.info("🚀 Starte LoRaWAN Debug Monitor...")
            logger.info("📝 Dieser Monitor zeigt alle empfangenen Daten im Detail an")
            logger.info("⚠️  Drücke Ctrl+C zum Beenden")
            
            # MQTT Listener starten
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            logger.info("\n👋 Debug Monitor gestoppt durch Benutzer")
        except Exception as e:
            logger.error(f"❌ Fehler: {e}")
        finally:
            self.client.disconnect()

def main():
    monitor = LoRaWANDebugMonitor()
    monitor.start()

if __name__ == "__main__":
    main()
