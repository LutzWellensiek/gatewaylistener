#!/usr/bin/env python3
"""
Enhanced ChirpStack System Monitor
- Überwacht alle LoRaWAN-Services 
- Startet Services automatisch bei Bedarf
- Empfängt MQTT-Nachrichten von ChirpStack
- Zeigt GPS-Daten an falls verfügbar (Gateway und Device)
- Erstellt CSV-Dateien mit Session-Daten
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
import csv
import uuid
import re

# Konfiguration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "application/+/device/+/event/+"
PACKET_FORWARDER_PATH = "/home/pi/sx1302_hal/packet_forwarder"
CSV_OUTPUT_DIR = "Lora_Sesion_Data"

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
        
        # CSV-Session Setup
        self.session_id = str(uuid.uuid4())[:8]
        self.session_start_time = datetime.now()
        self.csv_file_path = self.setup_csv_file()
        
        # CSV-Datei erstellen und Header schreiben
        self.init_csv_file()

    def setup_csv_file(self):
        """Erstellt CSV-Ordner und bestimmt Dateiname"""
        # Ordner erstellen falls nicht vorhanden
        os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)
        
        # Dateiname mit Zeitstempel und Session-ID
        timestamp = self.session_start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"lorawan_session_{timestamp}_{self.session_id}.csv"
        return os.path.join(CSV_OUTPUT_DIR, filename)

    def init_csv_file(self):
        """Initialisiert CSV-Datei mit Header"""
        headers = [
            'timestamp', 'session_id', 'application_id', 'device_eui', 
            'event_type', 'fcnt', 'fport', 'raw_data_hex', 'raw_data_ascii',
            'decoded_payload', 'gateway_id', 'rssi_dbm', 'snr_db', 'spreading_factor', 
            'bandwidth', 'frequency', 'gateway_lat', 'gateway_lon', 'gateway_alt',
            'device_lat', 'device_lon', 'device_alt', 'battery_level', 'margin_db', 
            'acknowledged', 'gps_source', 'gps_format'
        ]
        
        with open(self.csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
        
        logger.info(f"📊 CSV-Datei erstellt: {self.csv_file_path}")

    def write_to_csv(self, data_dict):
        """Schreibt Daten in CSV-Datei"""
        try:
            with open(self.csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
                headers = [
                    'timestamp', 'session_id', 'application_id', 'device_eui', 
                    'event_type', 'fcnt', 'fport', 'raw_data_hex', 'raw_data_ascii',
                    'decoded_payload', 'gateway_id', 'rssi_dbm', 'snr_db', 'spreading_factor', 
                    'bandwidth', 'frequency', 'gateway_lat', 'gateway_lon', 'gateway_alt',
                    'device_lat', 'device_lon', 'device_alt', 'battery_level', 'margin_db', 
                    'acknowledged', 'gps_source', 'gps_format'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writerow(data_dict)
        except Exception as e:
            logger.error(f"❌ Fehler beim Schreiben in CSV: {e}")

    def decode_payload_data(self, base64_data):
        """Dekodiert Base64-Nutzdaten und prüft auf GPS-Koordinaten"""
        try:
            decoded_bytes = base64.b64decode(base64_data)
            
            # Versuche verschiedene Dekodierungsarten
            results = {
                'hex': decoded_bytes.hex(),
                'ascii': None,
                'json': None,
                'coordinates': None
            }
            
            # ASCII-Dekodierung
            try:
                results['ascii'] = decoded_bytes.decode('ascii')
            except:
                pass
            
            # JSON-Dekodierung
            try:
                results['json'] = json.loads(decoded_bytes.decode('utf-8'))
            except:
                pass
            
            # GPS-Koordinaten suchen
            results['coordinates'] = self.extract_coordinates_from_payload(results)
            
            return results
            
        except Exception as e:
            logger.debug(f"Fehler beim Dekodieren der Nutzdaten: {e}")
            return None

    def extract_coordinates_from_payload(self, decoded_data):
        """Extrahiert GPS-Koordinaten aus dekodierten Nutzdaten"""
        coordinates = {'lat': None, 'lon': None, 'alt': None, 'source': None, 'format': None}
        
        # JSON-Struktur prüfen
        if decoded_data.get('json'):
            json_data = decoded_data['json']
            
            # Standard GPS-Felder
            if 'latitude' in json_data and 'longitude' in json_data:
                coordinates['lat'] = json_data['latitude']
                coordinates['lon'] = json_data['longitude']
                coordinates['alt'] = json_data.get('altitude')
                coordinates['source'] = 'payload_json'
                coordinates['format'] = 'standard'
            
            # Kurze Feld-Namen
            elif 'lat' in json_data and 'lon' in json_data:
                coordinates['lat'] = json_data['lat']
                coordinates['lon'] = json_data['lon']
                coordinates['alt'] = json_data.get('alt')
                coordinates['source'] = 'payload_json'
                coordinates['format'] = 'short'
            
            # Array-Format: [lat, lon] oder [lat, lon, alt]
            elif 'd' in json_data and isinstance(json_data['d'], list):
                coords = json_data['d']
                if len(coords) >= 2:
                    # Prüfe ob es GPS-Koordinaten sein könnten (Lat: -90 bis 90, Lon: -180 bis 180)
                    if (-90 <= coords[0] <= 90) and (-180 <= coords[1] <= 180):
                        coordinates['lat'] = coords[0]
                        coordinates['lon'] = coords[1]
                        coordinates['alt'] = coords[2] if len(coords) > 2 else None
                        coordinates['source'] = 'payload_json'
                        coordinates['format'] = 'array_d'
            
            # Koordinaten-Array
            elif 'coordinates' in json_data and isinstance(json_data['coordinates'], list):
                coords = json_data['coordinates']
                if len(coords) >= 2:
                    coordinates['lat'] = coords[0]
                    coordinates['lon'] = coords[1]
                    coordinates['alt'] = coords[2] if len(coords) > 2 else None
                    coordinates['source'] = 'payload_json'
                    coordinates['format'] = 'coordinates_array'
        
        # ASCII-String prüfen (z.B. "lat:52.5200,lon:13.4050")
        elif decoded_data.get('ascii'):
            ascii_data = decoded_data['ascii']
            
            # Regex für verschiedene GPS-Formate
            patterns = [
                r'lat:([+-]?\d+\.?\d*),lon:([+-]?\d+\.?\d*)',
                r'latitude:([+-]?\d+\.?\d*),longitude:([+-]?\d+\.?\d*)',
                r'([+-]?\d+\.?\d*),([+-]?\d+\.?\d*)',  # Einfaches Format
            ]
            
            for pattern in patterns:
                match = re.search(pattern, ascii_data.lower())
                if match:
                    lat, lon = float(match.group(1)), float(match.group(2))
                    if (-90 <= lat <= 90) and (-180 <= lon <= 180):
                        coordinates['lat'] = lat
                        coordinates['lon'] = lon
                        coordinates['source'] = 'payload_ascii'
                        coordinates['format'] = 'string'
                        break
        
        return coordinates if coordinates['lat'] is not None else None

    def extract_gateway_gps(self, payload):
        """Extrahiert GPS-Daten vom Gateway"""
        gps_data = {'lat': None, 'lon': None, 'alt': None}
        
        try:
            if 'rxInfo' in payload:
                for rx in payload['rxInfo']:
                    if 'location' in rx and isinstance(rx['location'], dict):
                        location = rx['location']
                        if location:  # Prüfe ob nicht leer
                            gps_data['lat'] = location.get('latitude')
                            gps_data['lon'] = location.get('longitude')
                            gps_data['alt'] = location.get('altitude')
                            if gps_data['lat'] is not None:
                                break
        except Exception as e:
            logger.debug(f"Fehler beim Extrahieren von Gateway-GPS: {e}")
        
        return gps_data

    def display_gps_data(self, gateway_gps, device_gps):
        """Zeigt GPS-Daten an falls verfügbar"""
        gps_found = False
        
        # Gateway-GPS
        if any(gateway_gps.values()):
            print("🌍 GATEWAY-GPS:")
            if gateway_gps['lat'] is not None:
                print(f"   📍 Latitude: {gateway_gps['lat']}")
            if gateway_gps['lon'] is not None:
                print(f"   📍 Longitude: {gateway_gps['lon']}")
            if gateway_gps['alt'] is not None:
                print(f"   📍 Altitude: {gateway_gps['alt']} m")
            gps_found = True
        
        # Device-GPS
        if device_gps:
            print("🌍 DEVICE-GPS:")
            if device_gps['lat'] is not None:
                print(f"   📍 Latitude: {device_gps['lat']}")
            if device_gps['lon'] is not None:
                print(f"   📍 Longitude: {device_gps['lon']}")
            if device_gps['alt'] is not None:
                print(f"   📍 Altitude: {device_gps['alt']} m")
            print(f"   📊 Quelle: {device_gps['source']}")
            print(f"   📋 Format: {device_gps['format']}")
            gps_found = True
        
        if not gps_found:
            print("🌍 GPS-DATEN: Keine verfügbar")
        
        return gps_found

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
            logger.info(f"📊 Session ID: {self.session_id}")
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
            
            # Basis-CSV-Daten vorbereiten
            csv_data = {
                'timestamp': timestamp,
                'session_id': self.session_id,
                'application_id': application_id,
                'device_eui': device_eui,
                'event_type': event_type,
                'fcnt': None,
                'fport': None,
                'raw_data_hex': None,
                'raw_data_ascii': None,
                'decoded_payload': None,
                'gateway_id': None,
                'rssi_dbm': None,
                'snr_db': None,
                'spreading_factor': None,
                'bandwidth': None,
                'frequency': None,
                'gateway_lat': None,
                'gateway_lon': None,
                'gateway_alt': None,
                'device_lat': None,
                'device_lon': None,
                'device_alt': None,
                'battery_level': None,
                'margin_db': None,
                'acknowledged': None,
                'gps_source': None,
                'gps_format': None
            }
            
            # Gateway-GPS extrahieren
            gateway_gps = self.extract_gateway_gps(payload)
            csv_data['gateway_lat'] = gateway_gps['lat']
            csv_data['gateway_lon'] = gateway_gps['lon']
            csv_data['gateway_alt'] = gateway_gps['alt']
            
            # Device-GPS und andere Daten aus Event-spezifischer Behandlung
            device_gps = None
            if event_type == "up":
                csv_data, device_gps = self.handle_uplink(payload, csv_data)
            elif event_type == "join":
                csv_data = self.handle_join(payload, csv_data)
            elif event_type == "status":
                csv_data = self.handle_status(payload, csv_data)
            elif event_type == "ack":
                csv_data = self.handle_ack(payload, csv_data)
            else:
                print(f"📝 Rohdaten: {json.dumps(payload, indent=2)}")
            
            # Device-GPS in CSV-Daten aufnehmen
            if device_gps:
                csv_data['device_lat'] = device_gps['lat']
                csv_data['device_lon'] = device_gps['lon']
                csv_data['device_alt'] = device_gps['alt']
                csv_data['gps_source'] = device_gps['source']
                csv_data['gps_format'] = device_gps['format']
            
            # GPS-Daten anzeigen
            self.display_gps_data(gateway_gps, device_gps)
            
            # In CSV schreiben
            self.write_to_csv(csv_data)
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Verarbeiten der Nachricht: {e}")
            print(f"Raw message: {msg.payload}")

    def handle_uplink(self, data, csv_data):
        """Behandelt Uplink-Nachrichten (Daten von Geräten)"""
        print("📈 UPLINK-DATEN:")
        device_gps = None
        
        # Basis-Informationen
        if 'devEui' in data:
            print(f"   Device EUI: {data['devEui']}")
        if 'fCnt' in data:
            print(f"   Frame Counter: {data['fCnt']}")
            csv_data['fcnt'] = data['fCnt']
        if 'fPort' in data:
            print(f"   Port: {data['fPort']}")
            csv_data['fport'] = data['fPort']
        
        # Nutzdaten dekodieren
        if 'data' in data:
            raw_data = data['data']
            print(f"   Raw Data (Base64): {raw_data}")
            
            # Payload dekodieren
            decoded_payload = self.decode_payload_data(raw_data)
            if decoded_payload:
                print(f"   Raw Data (Hex): {decoded_payload['hex']}")
                csv_data['raw_data_hex'] = decoded_payload['hex']
                
                if decoded_payload['ascii']:
                    print(f"   Als ASCII: {decoded_payload['ascii']}")
                    csv_data['raw_data_ascii'] = decoded_payload['ascii']
                
                if decoded_payload['json']:
                    print(f"   Als JSON: {json.dumps(decoded_payload['json'])}")
                    csv_data['decoded_payload'] = json.dumps(decoded_payload['json'])
                
                # GPS-Koordinaten aus Payload
                if decoded_payload['coordinates']:
                    device_gps = decoded_payload['coordinates']
                    print(f"   🌍 GPS in Payload gefunden!")
        
        # Gateway-Informationen
        if 'rxInfo' in data:
            print(f"   📡 Gateway Info:")
            for i, rx in enumerate(data['rxInfo']):
                if 'gatewayId' in rx:
                    gateway_id = rx['gatewayId']
                    print(f"      Gateway {i+1}: {gateway_id}")
                    if i == 0:  # Erste Gateway-Info für CSV
                        csv_data['gateway_id'] = gateway_id
                if 'rssi' in rx:
                    rssi = rx['rssi']
                    print(f"      RSSI: {rssi} dBm")
                    if i == 0:
                        csv_data['rssi_dbm'] = rssi
                if 'snr' in rx:
                    snr = rx['snr']
                    print(f"      SNR: {snr} dB")
                    if i == 0:
                        csv_data['snr_db'] = snr
        
        # TX-Info (Spreading Factor, Bandwidth, etc.)
        if 'txInfo' in data:
            tx_info = data['txInfo']
            if 'modulation' in tx_info:
                modulation = tx_info['modulation']
                if 'lora' in modulation:
                    lora_info = modulation['lora']
                    if 'spreadingFactor' in lora_info:
                        sf = lora_info['spreadingFactor']
                        print(f"   📶 Spreading Factor: SF{sf}")
                        csv_data['spreading_factor'] = f"SF{sf}"
                    if 'bandwidth' in lora_info:
                        bw = lora_info['bandwidth']
                        print(f"   📊 Bandwidth: {bw} Hz")
                        csv_data['bandwidth'] = bw
            if 'frequency' in tx_info:
                freq = tx_info['frequency']
                print(f"   📻 Frequency: {freq} Hz")
                csv_data['frequency'] = freq
        
        return csv_data, device_gps

    def handle_join(self, data, csv_data):
        """Behandelt Join-Events"""
        print("🔗 JOIN-EVENT:")
        if 'devEui' in data:
            print(f"   Device EUI: {data['devEui']}")
        if 'devAddr' in data:
            print(f"   Device Address: {data['devAddr']}")
        print("   ✅ Gerät erfolgreich dem Netzwerk beigetreten!")
        return csv_data

    def handle_status(self, data, csv_data):
        """Behandelt Status-Updates"""
        print("📊 STATUS-UPDATE:")
        if 'batteryLevel' in data:
            battery = data['batteryLevel']
            print(f"   🔋 Batterie: {battery}%")
            csv_data['battery_level'] = battery
        if 'margin' in data:
            margin = data['margin']
            print(f"   📶 Signal Margin: {margin} dB")
            csv_data['margin_db'] = margin
        return csv_data

    def handle_ack(self, data, csv_data):
        """Behandelt ACK-Messages"""
        print("✅ ACK-NACHRICHT:")
        if 'acknowledged' in data:
            ack = data['acknowledged']
            print(f"   Bestätigt: {ack}")
            csv_data['acknowledged'] = ack
        return csv_data

    def start(self):
        """Startet den Enhanced System Monitor"""
        try:
            logger.info("🚀 Starte Enhanced LoRaWAN System Monitor...")
            logger.info(f"📊 Session ID: {self.session_id}")
            logger.info(f"📊 CSV-Datei: {self.csv_file_path}")
            
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
            logger.info(f"📊 Session-Daten gespeichert in: {self.csv_file_path}")
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
