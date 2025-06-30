#!/usr/bin/env python3
"""
ChirpStack MQTT Data Listener
Empfängt alle LoRa-Daten von ChirpStack über MQTT
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

class ChirpStackMQTTListener:
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
            logger.error(f"❌ Verbindung fehlgeschlagen mit Code: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        logger.warning("🔌 Verbindung zum MQTT Broker getrennt")
    
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
            
            print(f"\n{'='*60}")
            print(f"🕐 Zeit: {timestamp}")
            print(f"📱 Application ID: {application_id}")
            print(f"🔷 Device EUI: {device_eui}")
            print(f"📊 Event Type: {event_type}")
            print(f"{'='*60}")
            
            # Event-spezifische Behandlung
            if event_type == "up":
                self.handle_uplink(payload)
            elif event_type == "join":
                self.handle_join(payload)
            elif event_type == "status":
                self.handle_status(payload)
            elif event_type == "ack":
                self.handle_ack(payload)
            else:
                print(f"📝 Rohdaten: {json.dumps(payload, indent=2)}")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Verarbeiten der Nachricht: {e}")
            print(f"Raw message: {msg.payload}")
    
    def handle_uplink(self, data):
        """Behandelt Uplink-Nachrichten (Daten von Geräten)"""
        print("📈 UPLINK-DATEN:")
        
        # Basis-Informationen
        if 'devEui' in data:
            print(f"   Device EUI: {data['devEui']}")
        if 'fCnt' in data:
            print(f"   Frame Counter: {data['fCnt']}")
        if 'fPort' in data:
            print(f"   Port: {data['fPort']}")
        
        # Nutzdaten dekodieren
        if 'data' in data:
            raw_data = data['data']
            print(f"   Raw Data (Base64): {raw_data}")
            
            try:
                # Base64 dekodieren
                decoded_bytes = base64.b64decode(raw_data)
                print(f"   Raw Data (Hex): {decoded_bytes.hex()}")
                print(f"   Raw Data (Bytes): {list(decoded_bytes)}")
                
                # Als ASCII versuchen
                try:
                    ascii_data = decoded_bytes.decode('ascii')
                    print(f"   Als ASCII: {ascii_data}")
                except:
                    pass
                    
            except Exception as e:
                print(f"   ❌ Dekodierung fehlgeschlagen: {e}")
        
        # Gateway-Informationen
        if 'rxInfo' in data:
            print(f"   📡 Gateway Info:")
            for i, rx in enumerate(data['rxInfo']):
                if 'gatewayId' in rx:
                    print(f"      Gateway {i+1}: {rx['gatewayId']}")
                if 'rssi' in rx:
                    print(f"      RSSI: {rx['rssi']} dBm")
                if 'snr' in rx:
                    print(f"      SNR: {rx['snr']} dB")
        
        # TX-Informationen
        if 'txInfo' in data:
            tx = data['txInfo']
            if 'frequency' in tx:
                print(f"   📻 Frequenz: {tx['frequency']} Hz")
            if 'dr' in tx:
                print(f"   📊 Data Rate: {tx['dr']}")
    
    def handle_join(self, data):
        """Behandelt Join-Events"""
        print("🔗 JOIN-EVENT:")
        if 'devEui' in data:
            print(f"   Device EUI: {data['devEui']}")
        if 'devAddr' in data:
            print(f"   Device Address: {data['devAddr']}")
        print("   ✅ Gerät erfolgreich dem Netzwerk beigetreten!")
    
    def handle_status(self, data):
        """Behandelt Status-Updates"""
        print("📊 STATUS-UPDATE:")
        if 'batteryLevel' in data:
            print(f"   🔋 Batterie: {data['batteryLevel']}%")
        if 'margin' in data:
            print(f"   📶 Signal Margin: {data['margin']} dB")
    
    def handle_ack(self, data):
        """Behandelt ACK-Messages"""
        print("✅ ACK-NACHRICHT:")
        if 'acknowledged' in data:
            print(f"   Bestätigt: {data['acknowledged']}")
    
    def start(self):
        """Startet den MQTT Listener"""
        try:
            logger.info("🚀 Starte ChirpStack MQTT Listener...")
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_forever()
        except KeyboardInterrupt:
            logger.info("\n👋 Listener gestoppt durch Benutzer")
        except Exception as e:
            logger.error(f"❌ Fehler: {e}")
        finally:
            self.client.disconnect()

def main():
    listener = ChirpStackMQTTListener()
    listener.start()

if __name__ == "__main__":
    main()
