#!/usr/bin/env python3
"""
Enhanced ChirpStack System Monitor
- Überwacht alle LoRaWAN-Services 
- Startet Services automatisch bei Bedarf
- Empfängt MQTT-Nachrichten von ChirpStack
"""

import json
import base64
import paho.mqtt.client as mqtt
from datetime import datetime
import logging
import subprocess
import time
import sys
import os

# Konfiguration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "application/+/device/+/event/+"
PACKET_FORWARDER_PATH = "/home/pi/sx1302_hal/packet_forwarder"

# Logging einrichten
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LoRaWANSystemMonitor:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.packet_forwarder_process = None

    def check_process_running(self, process_name):
        """Prüft ob ein Prozess läuft"""
        try:
            result = subprocess.run(['pgrep', '-f', process_name], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Fehler beim Prüfen von {process_name}: {e}")
            return False

    def check_service_status(self, service_name):
        """Prüft systemd Service Status"""
        try:
            result = subprocess.run(['systemctl', 'is-active', service_name], 
                                  capture_output=True, text=True)
            return result.stdout.strip() == 'active'
        except Exception as e:
            logger.error(f"Fehler beim Prüfen von Service {service_name}: {e}")
            return False

    def start_service(self, service_name):
        """Startet einen systemd Service"""
        try:
            logger.info(f"🔄 Starte Service: {service_name}")
            result = subprocess.run(['sudo', 'systemctl', 'start', service_name], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Service {service_name} erfolgreich gestartet")
                return True
            else:
                logger.error(f"❌ Fehler beim Starten von {service_name}: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"❌ Exception beim Starten von {service_name}: {e}")
            return False

    def start_packet_forwarder(self):
        """Startet den Packet Forwarder"""
        try:
            if self.check_process_running('lora_pkt_fwd'):
                logger.info("✅ Packet Forwarder läuft bereits")
                return True
                
            logger.info("🔄 Starte Packet Forwarder...")
            
            # Wechsle in das Packet Forwarder Verzeichnis
            os.chdir(PACKET_FORWARDER_PATH)
            
            # Starte den Packet Forwarder im Hintergrund
            self.packet_forwarder_process = subprocess.Popen(
                ['sudo', './lora_pkt_fwd'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Kurz warten und prüfen ob erfolgreich gestartet
            time.sleep(3)
            if self.check_process_running('lora_pkt_fwd'):
                logger.info("✅ Packet Forwarder erfolgreich gestartet")
                return True
            else:
                logger.error("❌ Packet Forwarder konnte nicht gestartet werden")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten des Packet Forwarders: {e}")
            return False

    def check_mqtt_connectivity(self):
        """Prüft MQTT-Verbindung"""
        try:
            test_client = mqtt.Client()
            test_client.connect(MQTT_BROKER, MQTT_PORT, 10)
            test_client.disconnect()
            return True
        except Exception as e:
            logger.error(f"❌ MQTT-Verbindung fehlgeschlagen: {e}")
            return False

    def check_chirpstack_api(self):
        """Prüft ChirpStack API"""
        try:
            result = subprocess.run(['curl', '-s', f'http://{MQTT_BROKER}:8080'], 
                                  capture_output=True, text=True, timeout=5)
            return "ChirpStack" in result.stdout
        except Exception as e:
            logger.error(f"❌ ChirpStack API nicht erreichbar: {e}")
            return False

    def system_health_check(self):
        """Führt kompletten System-Health-Check durch"""
        logger.info("🔍 Starte System-Health-Check...")
        
        checks = {
            "MQTT Broker (Mosquitto)": {
                "check": lambda: self.check_service_status('mosquitto'),
                "start": lambda: self.start_service('mosquitto')
            },
            "ChirpStack Gateway Bridge": {
                "check": lambda: self.check_service_status('chirpstack-gateway-bridge'),
                "start": lambda: self.start_service('chirpstack-gateway-bridge')
            },
            "ChirpStack Network Server": {
                "check": lambda: self.check_process_running('chirpstack'),
                "start": lambda: self.start_service('chirpstack')
            },
            "Packet Forwarder": {
                "check": lambda: self.check_process_running('lora_pkt_fwd'),
                "start": self.start_packet_forwarder
            }
        }

        all_ok = True
        
        for service_name, service_config in checks.items():
            if service_config["check"]():
                logger.info(f"✅ {service_name}: OK")
            else:
                logger.warning(f"⚠️  {service_name}: Nicht verfügbar - starte...")
                if service_config["start"]():
                    logger.info(f"✅ {service_name}: Erfolgreich gestartet")
                else:
                    logger.error(f"❌ {service_name}: Start fehlgeschlagen")
                    all_ok = False

        # Zusätzliche Connectivity-Checks
        logger.info("🔍 Prüfe Konnektivität...")
        
        if self.check_mqtt_connectivity():
            logger.info("✅ MQTT-Konnektivität: OK")
        else:
            logger.error("❌ MQTT-Konnektivität: Fehlgeschlagen")
            all_ok = False

        if self.check_chirpstack_api():
            logger.info("✅ ChirpStack API: OK")
        else:
            logger.warning("⚠️  ChirpStack API: Nicht erreichbar")

        if all_ok:
            logger.info("🎉 Alle Services laufen korrekt!")
        else:
            logger.warning("⚠️  Einige Services haben Probleme")
            
        return all_ok

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("✅ Erfolgreich mit MQTT Broker verbunden!")
            client.subscribe(MQTT_TOPIC)
            logger.info(f"📡 Lausche auf Topic: {MQTT_TOPIC}")
        else:
            logger.error(f"❌ MQTT-Verbindung fehlgeschlagen mit Code: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        logger.warning("🔌 Verbindung zum MQTT Broker getrennt")
        # Versuche Reconnect nach Service-Check
        logger.info("🔄 Führe System-Check durch...")
        time.sleep(2)
        self.system_health_check()
    
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
        """Startet den Enhanced System Monitor"""
        try:
            logger.info("🚀 Starte Enhanced LoRaWAN System Monitor...")
            
            # System Health Check
            self.system_health_check()
            
            # Kurz warten damit Services starten können
            time.sleep(2)
            
            # MQTT Listener starten
            logger.info("📡 Starte MQTT Listener...")
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            logger.info("\n👋 Monitor gestoppt durch Benutzer")
        except Exception as e:
            logger.error(f"❌ Fehler: {e}")
        finally:
            self.client.disconnect()
            # Packet Forwarder Process beenden falls gestartet
            if self.packet_forwarder_process:
                self.packet_forwarder_process.terminate()

def main():
    monitor = LoRaWANSystemMonitor()
    monitor.start()

if __name__ == "__main__":
    main()
