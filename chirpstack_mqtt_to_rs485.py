#!/usr/bin/env python3
"""
ChirpStack MQTT to RS485 Bridge
Empfängt LoRaWAN-Daten vom ChirpStack MQTT Forwarder 
und leitet sie über RS485 weiter (statt UART)
"""

import serial
import paho.mqtt.client as mqtt
import json
import time
import base64
import struct
from datetime import datetime

class ChirpStackMQTTtoRS485:
    def __init__(self, mqtt_broker="localhost", mqtt_port=1883, 
                 rs485_port='COM3', rs485_baudrate=115200):
        """
        Initialisiert die MQTT-zu-RS485 Bridge
        """
        # RS485 Setup (über USB-to-RS485 Adapter)
        self.ser = serial.Serial(rs485_port, rs485_baudrate, timeout=1)
        print(f"RS485 initialisiert auf {rs485_port} mit {rs485_baudrate} baud")
        
        # MQTT Setup
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.client = mqtt.Client()
        
        # MQTT Callbacks
        self.client.on_connect = self.on_mqtt_connect
        self.client.on_message = self.on_mqtt_message
        self.client.on_disconnect = self.on_mqtt_disconnect
        
        # Statistiken
        self.messages_received = 0
        self.messages_sent = 0
        
        # Frame-Sequenznummer für RS485
        self.frame_sequence = 0
        
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback wenn MQTT verbunden ist"""
        if rc == 0:
            print(f"Erfolgreich mit MQTT Broker verbunden ({self.mqtt_broker}:{self.mqtt_port})")
            
            # Subscribe NUR zu Uplink-Nachrichten (tatsächlich empfangene Daten)
            client.subscribe("application/+/device/+/event/up")
            print("Subscribed zu: application/+/device/+/event/up (nur Uplink-Daten)")
            
        else:
            print(f"MQTT Verbindung fehlgeschlagen. Return code: {rc}")
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """Callback wenn MQTT Verbindung getrennt wird"""
        print(f"MQTT Verbindung getrennt. Return code: {rc}")
        if rc != 0:
            print("Unerwartete Trennung. Versuche erneut zu verbinden...")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Callback wenn MQTT Nachricht empfangen wird"""
        try:
            self.messages_received += 1
            
            # Decode payload
            payload = json.loads(msg.payload.decode('utf-8'))
            
            # Prüfe ob es sich um echte Uplink-Daten handelt
            if not self.is_valid_uplink_data(payload):
                print(f"Überspringe Nachricht ohne Nutzdaten")
                return
            
            # Zeitstempel hinzufügen
            timestamp = datetime.now().isoformat()
            
            # Extrahiere Sensordaten aus LoRaWAN Payload
            sensor_data = self.extract_sensor_data(payload)
            
            if sensor_data:
                # Sende Sensordaten über RS485
                self.send_rs485_sensor_data(sensor_data)
                
                # Log
                print(f"\n[{timestamp}] LoRaWAN-Sensordaten empfangen und über RS485 gesendet:")
                print(f"  Device: {payload.get('deviceInfo', {}).get('devEui', 'unknown')}")
                print(f"  Sensordaten: {sensor_data}")
                print(f"  RSSI: {payload.get('rxInfo', [{}])[0].get('rssi', 'N/A')} dBm")
                print(f"  SNR: {payload.get('rxInfo', [{}])[0].get('snr', 'N/A')} dB")
            
        except Exception as e:
            print(f"Fehler beim Verarbeiten der MQTT Nachricht: {e}")
    
    def is_valid_uplink_data(self, payload):
        """Prüft ob die Nachricht tatsächlich Uplink-Daten enthält"""
        # Muss Uplink-Event sein
        if not payload.get('deviceInfo'):
            return False
        
        # Muss RX-Info haben (empfangen vom Gateway)
        if not payload.get('rxInfo'):
            return False
        
        # Muss Daten enthalten
        if not payload.get('data'):
            return False
        
        # Optional: Prüfe ob es sich um echte Sensordaten handelt
        try:
            data_bytes = base64.b64decode(payload['data'])
            if len(data_bytes) == 0:
                return False
        except:
            return False
        
        return True
    
    def extract_sensor_data(self, payload):
        """Extrahiert Sensordaten aus der LoRaWAN Payload"""
        try:
            # Dekodiere Base64 Payload
            data_bytes = base64.b64decode(payload['data'])
            
            # Versuche JSON-Format zu parsen (falls kompakte JSON-Übertragung)
            try:
                json_str = data_bytes.decode('utf-8')
                json_data = json.loads(json_str)
                
                # Erwarte Format: {"d":[temp1,temp2,deflection,pressure],"id":"device_id","t":timestamp}
                if 'd' in json_data and isinstance(json_data['d'], list):
                    sensor_values = json_data['d']
                    device_id = json_data.get('id', 'unknown')
                    
                    # Konvertiere in Struktur für RS485
                    sensor_data = {
                        'device_id': device_id,
                        'timestamp': int(time.time()),
                        'temp1': sensor_values[0] if len(sensor_values) > 0 else 0.0,
                        'temp2': sensor_values[1] if len(sensor_values) > 1 else 0.0,
                        'deflection': sensor_values[2] if len(sensor_values) > 2 else 0.0,
                        'pressure': sensor_values[3] if len(sensor_values) > 3 else 0.0,
                        'deflection_2': sensor_values[4] if len(sensor_values) > 4 else 0.0
                    }
                    
                    return sensor_data
                    
            except (UnicodeDecodeError, json.JSONDecodeError):
                pass
            
            # Falls kein JSON, versuche binäre Dekodierung
            if len(data_bytes) >= 16:  # Mindestens 4 float-Werte
                # Erwarte Little-Endian float-Werte
                values = struct.unpack('<ffff', data_bytes[:16])
                
                sensor_data = {
                    'device_id': payload.get('deviceInfo', {}).get('devEui', 'unknown'),
                    'timestamp': int(time.time()),
                    'temp1': values[0],
                    'temp2': values[1],
                    'deflection': values[2],
                    'pressure': values[3],
                    'deflection_2': 0.0
                }
                
                return sensor_data
                
        except Exception as e:
            print(f"Fehler beim Extrahieren der Sensordaten: {e}")
            
        return None
    
    def calculate_crc8(self, data):
        """Berechnet CRC8 für RS485-Frame (vereinfachte Version)"""
        crc = 0
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x07
                else:
                    crc <<= 1
                crc &= 0xFF
        return crc
    
    def send_rs485_sensor_data(self, sensor_data):
        """Sendet Sensordaten über RS485 im erwarteten Format"""
        try:
            # Sende verschiedene Sensorwerte als separate RS485-Frames
            # Format: [INPUT_ID][DATA_HIGH][DATA_LOW][CRC8]
            
            # Definiere Input-IDs (aus der C++-Datei)
            INPUT_IDS = {
                'IN1': 0x01,      # Temp1
                'IN2': 0x02,      # Temp2
                'IN3': 0x03,      # Deflection
                'IN4': 0x04,      # Pressure
                'IN9': 0x09       # Internal temp (für Tests)
            }
            
            # Sende Temp1
            self.send_rs485_frame(INPUT_IDS['IN1'], sensor_data['temp1'])
            time.sleep(0.05)  # Kurze Pause zwischen Frames
            
            # Sende Temp2
            self.send_rs485_frame(INPUT_IDS['IN2'], sensor_data['temp2'])
            time.sleep(0.05)
            
            # Sende Deflection
            self.send_rs485_frame(INPUT_IDS['IN3'], sensor_data['deflection'])
            time.sleep(0.05)
            
            # Sende Pressure (falls verfügbar)
            if sensor_data['pressure'] != 0.0:
                self.send_rs485_frame(INPUT_IDS['IN4'], sensor_data['pressure'])
                time.sleep(0.05)
            
            self.messages_sent += 1
            print(f"  -> RS485 Sensordaten gesendet")
            
        except Exception as e:
            print(f"Fehler beim Senden über RS485: {e}")
    
    def send_rs485_frame(self, input_id, value):
        """Sendet einen einzelnen RS485-Frame"""
        try:
            # Konvertiere float-Wert in 12-Bit-Wert (0-4095)
            # Skalierung je nach Sensor anpassen
            if input_id in [0x01, 0x02]:  # Temperatur
                # Temperatur: -40°C bis +85°C -> 0-4095
                scaled_value = int(((value + 40) / 125.0) * 4095)
            elif input_id == 0x03:  # Deflection
                # Deflection: -20° bis +20° -> 0-4095
                scaled_value = int(((value + 20) / 40.0) * 4095)
            elif input_id == 0x04:  # Pressure
                # Pressure: -1.0 bis +0.6 bar -> 0-4095
                scaled_value = int(((value + 1.0) / 1.6) * 4095)
            else:
                scaled_value = int(value) & 0x0FFF
            
            # Begrenze auf 12-Bit
            scaled_value = max(0, min(4095, scaled_value))
            
            # Erstelle Frame: [INPUT_ID][DATA_HIGH][DATA_LOW][CRC8]
            data_high = (scaled_value >> 4) & 0xFF
            data_low = (scaled_value & 0x0F) << 4
            
            frame = bytearray([input_id, data_high, data_low])
            
            # Berechne CRC8
            crc = self.calculate_crc8(frame)
            frame.append(crc)
            
            # Sende Frame
            self.ser.write(frame)
            self.ser.flush()
            
            print(f"    Frame gesendet: ID={input_id:02X}, Wert={value:.2f}, Skaliert={scaled_value}, Frame={frame.hex()}")
            
        except Exception as e:
            print(f"Fehler beim Senden des RS485-Frames: {e}")
    
    def run(self):
        """Hauptschleife"""
        print("\nChirpStack MQTT to RS485 Bridge")
        print("=" * 50)
        print(f"MQTT Broker: {self.mqtt_broker}:{self.mqtt_port}")
        print(f"RS485 Port: {self.ser.port}")
        print("Filter: Nur tatsächlich empfangene Sensor-Daten")
        print("Ausgabe: RS485-Frames für Mikrocontroller")
        print("=" * 50)
        
        try:
            # Verbinde zu MQTT Broker
            self.client.connect(self.mqtt_broker, self.mqtt_port, 60)
            
            # Starte MQTT Loop
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            print("\n\nShutdown...")
            self.shutdown()
        except Exception as e:
            print(f"Fehler: {e}")
            self.shutdown()
    
    def shutdown(self):
        """Beendet die Verbindungen sauber"""
        print(f"\nStatistik:")
        print(f"  MQTT Nachrichten empfangen: {self.messages_received}")
        print(f"  RS485 Nachrichten gesendet: {self.messages_sent}")
        
        self.client.disconnect()
        self.ser.close()
        print("Verbindungen geschlossen.")

def main():
    # Konfiguration
    MQTT_BROKER = "localhost"  # ChirpStack MQTT Broker
    MQTT_PORT = 1883
    RS485_PORT = 'COM3'  # Windows COM-Port für USB-to-RS485 Adapter
    RS485_BAUDRATE = 115200
    
    # Erstelle und starte Bridge
    bridge = ChirpStackMQTTtoRS485(
        mqtt_broker=MQTT_BROKER,
        mqtt_port=MQTT_PORT,
        rs485_port=RS485_PORT,
        rs485_baudrate=RS485_BAUDRATE
    )
    
    bridge.run()

if __name__ == "__main__":
    main()
