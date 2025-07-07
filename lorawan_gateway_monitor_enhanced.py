#!/usr/bin/env python3
"""
Enhanced LoRaWAN Gateway Monitor
- Zeigt Spreading-Faktor und Datenrate an
- Speichert alle Daten in CSV-Datei
- Überprüft, ob der Forwarder und ChirpStack laufen
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
CSV_FILENAME = "lorawan_data.csv"

# Logging einrichten
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedLoRaWANGatewayMonitor:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.csv_file = None
        self.csv_writer = None
        self.init_csv()

    def init_csv(self):
        """Initialisiert die CSV-Datei mit Headers"""
        try:
            file_exists = os.path.isfile(CSV_FILENAME)
            
            self.csv_file = open(CSV_FILENAME, 'a', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.csv_file)
            
            if not file_exists:
                headers = [
                    'timestamp', 'application_id', 'device_eui', 'event_type',
                    'frame_count', 'port', 'raw_data_base64', 'raw_data_hex',
                    'data_size_bytes', 'spreading_factor', 'bandwidth',
                    'frequency', 'code_rate', 'gateway_id', 'rssi', 'snr',
                    'channel', 'ascii_data'
                ]
                self.csv_writer.writerow(headers)
                self.csv_file.flush()
                print(f"✅ CSV-Datei erstellt: {CSV_FILENAME}")
            else:
                print(f"📄 Verwende bestehende CSV-Datei: {CSV_FILENAME}")
                
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der CSV-Datei: {e}")
            self.csv_file = None
            self.csv_writer = None

    def write_to_csv(self, data_row):
        """Schreibt eine Datenzeile in die CSV-Datei"""
        if self.csv_writer:
            try:
                self.csv_writer.writerow(data_row)
                self.csv_file.flush()
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
            print(f"💾 CSV-Datei: {CSV_FILENAME}")
            print("\n" + "="*60)
            print("📊 ENHANCED DATA MONITOR - Warte auf LoRa-Nachrichten...")
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
            topic_parts = msg.topic.split('/')
            application_id = topic_parts[1] if len(topic_parts) > 1 else "unknown"
            device_eui = topic_parts[3] if len(topic_parts) > 3 else "unknown"
            event_type = topic_parts[5] if len(topic_parts) > 5 else "unknown"
            
            payload = json.loads(msg.payload.decode())
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"\n{'='*60}")
            print(f"🕐 {timestamp}")
            print(f"📱 App: {application_id} | 🔷 Device: {device_eui} | 📊 Type: {event_type}")
            print(f"{'='*60}")
            
            if event_type == "up":
                self.handle_uplink(payload, timestamp, application_id, device_eui, event_type)
            elif event_type == "join":
                self.handle_join(payload, timestamp, application_id, device_eui, event_type)
            elif event_type == "status":
                self.handle_status(payload, timestamp, application_id, device_eui, event_type)
            else:
                print("📝 Raw Data:")
                print(json.dumps(payload, indent=2))
                self.save_generic_event(payload, timestamp, application_id, device_eui, event_type)
                
        except Exception as e:
            print(f"❌ Fehler beim Verarbeiten der Nachricht: {e}")
            print(f"Raw Topic: {msg.topic}")
            print(f"Raw Payload: {msg.payload}")

    def handle_uplink(self, data, timestamp, application_id, device_eui, event_type):
        """Behandelt Uplink-Nachrichten mit verbesserter Analyse"""
        print("📈 UPLINK DATA:")
        
        # CSV-Daten initialisieren
        csv_data = [timestamp, application_id, device_eui, event_type, '', '', '', '', '', '', '', '', '', '', '', '', '', '']
        
        # Frame Info
        frame_count = data.get('fCnt', '')
        port = data.get('fPort', '')
        csv_data[4] = frame_count
        csv_data[5] = port
        
        if frame_count:
            print(f"   📊 Frame Count: {frame_count}")
        if port:
            print(f"   🚪 Port: {port}")
        
        # Payload dekodieren
        if 'data' in data:
            raw_data = data['data']
            csv_data[6] = raw_data
            print(f"   📦 Raw (Base64): {raw_data}")
            
            try:
                decoded_bytes = base64.b64decode(raw_data)
                hex_data = decoded_bytes.hex().upper()
                data_size = len(decoded_bytes)
                
                csv_data[7] = hex_data
                csv_data[8] = data_size
                
                print(f"   🔢 Hex: {hex_data}")
                print(f"   📏 Größe: {data_size} Bytes")
                
                # ASCII versuchen
                try:
                    ascii_data = decoded_bytes.decode('ascii')
                    csv_data[17] = ascii_data
                    print(f"   📝 ASCII: '{ascii_data}'")
                except:
                    pass
                    
            except Exception as e:
                print(f"   ❌ Dekodierung fehlgeschlagen: {e}")
        
        # Transmission Info (txInfo) - Spreading Factor und weitere Parameter
        if 'txInfo' in data:
            tx_info = data['txInfo']
            print("   📡 Transmission Info:")
            
            if 'modulation' in tx_info:
                mod = tx_info['modulation']
                if 'lora' in mod:
                    lora_info = mod['lora']
                    
                    # Spreading Factor
                    if 'spreadingFactor' in lora_info:
                        sf = lora_info['spreadingFactor']
                        csv_data[9] = sf
                        print(f"      🔀 Spreading Factor: SF{sf}")
                    
                    # Bandwidth
                    if 'bandwidth' in lora_info:
                        bw = lora_info['bandwidth']
                        csv_data[10] = bw
                        print(f"      📶 Bandwidth: {bw} Hz")
                    
                    # Code Rate
                    if 'codeRate' in lora_info:
                        cr = lora_info['codeRate']
                        csv_data[12] = cr
                        print(f"      📊 Code Rate: {cr}")
            
            # Frequency
            if 'frequency' in tx_info:
                freq = tx_info['frequency']
                csv_data[11] = freq
                print(f"      🎵 Frequency: {freq} Hz")
        
        # Gateway Info
        if 'rxInfo' in data and data['rxInfo']:
            print("   📡 Gateway Info:")
            rx = data['rxInfo'][0]  # Erste Gateway-Info verwenden
            
            gateway_id = rx.get('gatewayId', '')
            rssi = rx.get('rssi', '')
            snr = rx.get('snr', '')
            channel = rx.get('channel', '')
            
            csv_data[13] = gateway_id
            csv_data[14] = rssi
            csv_data[15] = snr
            csv_data[16] = channel
            
            gateway_short = gateway_id[:16] + "..." if len(gateway_id) > 16 else gateway_id
            print(f"      📶 {gateway_short}")
            print(f"      📊 RSSI: {rssi}dBm | SNR: {snr}dB")
            if channel:
                print(f"      📻 Channel: {channel}")
        
        # In CSV speichern
        self.write_to_csv(csv_data)

    def handle_join(self, data, timestamp, application_id, device_eui, event_type):
        """Behandelt Join-Events"""
        print("🔗 JOIN EVENT:")
        
        if 'devEui' in data:
            print(f"   🆔 Device EUI: {data['devEui']}")
        if 'devAddr' in data:
            print(f"   📍 Device Addr: {data['devAddr']}")
        print("   ✅ Gerät erfolgreich dem Netzwerk beigetreten!")
        
        csv_data = [timestamp, application_id, device_eui, event_type, '', '', '', '', '', '', '', '', '', '', '', '', '', '']
        self.write_to_csv(csv_data)

    def handle_status(self, data, timestamp, application_id, device_eui, event_type):
        """Behandelt Status-Updates"""
        print("📊 STATUS UPDATE:")
        
        if 'batteryLevel' in data:
            battery = data['batteryLevel']
            battery_icon = "🔋" if battery > 50 else "🪫" if battery > 20 else "⚠️"
            print(f"   {battery_icon} Batterie: {battery}%")
        if 'margin' in data:
            margin = data['margin']
            print(f"   📶 Signal Margin: {margin} dB")
        
        csv_data = [timestamp, application_id, device_eui, event_type, '', '', '', '', '', '', '', '', '', '', '', '', '', '']
        self.write_to_csv(csv_data)

    def save_generic_event(self, data, timestamp, application_id, device_eui, event_type):
        """Speichert generische Events in CSV"""
        csv_data = [timestamp, application_id, device_eui, event_type, '', '', '', '', '', '', '', '', '', '', '', '', '', '']
        self.write_to_csv(csv_data)

    def start(self):
        """Startet den Enhanced Gateway Monitor"""
        try:
            print("🚀 Enhanced LoRaWAN Gateway Monitor gestartet")
            print("Features:")
            print("  ✅ Zeigt Spreading-Faktor und Datenrate an")
            print("  ✅ Speichert alle Daten in CSV-Datei")
            print("  ✅ Erweiterte Gateway-Informationen")
            print("="*60)
            
            if not self.system_check():
                print("\n⚠️  Warnung: Nicht alle Services konnten gestartet werden")
                print("Monitor läuft trotzdem weiter...")
            
            time.sleep(2)
            
            print("\n📡 Starte MQTT Listener...")
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            print("\n\n👋 Monitor gestoppt durch Benutzer")
        except Exception as e:
            print(f"\n❌ Fehler: {e}")
        finally:
            self.client.disconnect()
            if self.csv_file:
                self.csv_file.close()
            print("🔌 MQTT-Verbindung getrennt")
            print(f"💾 CSV-Datei gespeichert: {CSV_FILENAME}")

def main():
    monitor = EnhancedLoRaWANGatewayMonitor()
    monitor.start()

if __name__ == "__main__":
    main()
