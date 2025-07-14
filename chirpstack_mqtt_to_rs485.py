#!/usr/bin/env python3
"""
ChirpStack MQTT to RS485 Bridge - Nur Sensordaten
Sendet nur die Sensordaten (d-Array) über RS485
"""

import serial
import paho.mqtt.client as mqtt
import json
import time
import base64
from datetime import datetime

class ChirpStackMQTTtoRS485:
    def __init__(self, mqtt_broker="localhost", mqtt_port=1883, 
                 rs485_port='/dev/ttyUSB0', rs485_baudrate=115200):
        # RS485 Setup
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
        
    def on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"Erfolgreich mit MQTT Broker verbunden ({self.mqtt_broker}:{self.mqtt_port})")
            client.subscribe("application/+/device/+/event/up")
            print("Subscribed zu: application/+/device/+/event/up")
        else:
            print(f"MQTT Verbindung fehlgeschlagen. Return code: {rc}")
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        print(f"MQTT Verbindung getrennt. Return code: {rc}")
        if rc != 0:
            print("Unerwartete Trennung. Versuche erneut zu verbinden...")
    
    def on_mqtt_message(self, client, userdata, msg):
        try:
            self.messages_received += 1
            
            # Decode payload
            payload = json.loads(msg.payload.decode('utf-8'))
            
            # Prüfe ob es sich um echte Uplink-Daten handelt
            if not self.is_valid_uplink_data(payload):
                print(f"Überspringe Nachricht ohne Nutzdaten")
                return
            
            # Extrahiere nur Sensordaten (d-Array)
            sensor_data = self.extract_sensor_data(payload)
            
            if sensor_data is None:
                print("Keine Sensordaten (d-Array) verfügbar")
                return
            
            # Sende nur Sensordaten über RS485
            self.send_rs485(sensor_data)
            
            # Log
            timestamp = datetime.now().isoformat()
            print(f"\n[{timestamp}] Sensordaten empfangen:")
            device_info = payload.get('deviceInfo', {})
            print(f"  Device: {device_info.get('devEui', 'unknown')}")
            print(f"  Sensordaten: {sensor_data}")
            
        except Exception as e:
            print(f"Fehler beim Verarbeiten der MQTT Nachricht: {e}")
    
    def is_valid_uplink_data(self, payload):
        if not payload.get('deviceInfo'):
            return False
        if not payload.get('rxInfo'):
            return False
        if not payload.get('data'):
            return False
        
        try:
            data_bytes = base64.b64decode(payload['data'])
            if len(data_bytes) == 0:
                return False
        except:
            return False
        
        return True
    
    def extract_sensor_data(self, payload):
        if 'object' in payload and payload['object']:
            decoded_obj = payload['object']
            
            if 'd' in decoded_obj and isinstance(decoded_obj['d'], list):
                return decoded_obj['d']
        
        if 'data' in payload:
            try:
                data_bytes = base64.b64decode(payload['data'])
                data_str = data_bytes.decode('utf-8')
                decoded_data = json.loads(data_str)
                
                if 'd' in decoded_data and isinstance(decoded_data['d'], list):
                    return decoded_data['d']
                    
            except:
                pass
        
        return None
    
    def send_rs485(self, data):
        try:
            json_data = json.dumps(data, separators=(',', ':'))
            message = json_data + '\n'
            
            self.ser.write(message.encode('utf-8'))
            self.ser.flush()
            
            self.messages_sent += 1
            print(f"  -\u003e RS485 gesendet ({len(message)} bytes): {json_data}")
            
        except Exception as e:
            print(f"Fehler beim Senden über RS485: {e}")
    
    def run(self):
        print("\nChirpStack MQTT to RS485 Bridge (Nur Sensordaten)")
        print("=" * 50)
        print(f"MQTT Broker: {self.mqtt_broker}:{self.mqtt_port}")
        print(f"RS485 Port: {self.ser.port}")
        print("Filter: Nur 'd' Array aus Sensordaten")
        print("=" * 50)
        
        try:
            self.client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            print("\n\nShutdown...")
            self.shutdown()
        except Exception as e:
            print(f"Fehler: {e}")
            self.shutdown()
    
    def shutdown(self):
        print(f"\nStatistik:")
        print(f"  MQTT Nachrichten empfangen: {self.messages_received}")
        print(f"  RS485 Nachrichten gesendet: {self.messages_sent}")
        
        self.client.disconnect()
        self.ser.close()
        print("Verbindungen geschlossen.")

def main():
    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
    RS485_PORT = '/dev/ttyAMA0'
    RS485_BAUDRATE = 115200
    
    bridge = ChirpStackMQTTtoRS485(
        mqtt_broker=MQTT_BROKER,
        mqtt_port=MQTT_PORT,
        rs485_port=RS485_PORT,
        rs485_baudrate=RS485_BAUDRATE
    )
    
    bridge.run()

if __name__ == "__main__":
    main()
