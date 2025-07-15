#!/usr/bin/env python3
"""
ChirpStack MQTT to UART Bridge - Binäre Sensordaten
Sendet Sensordaten (d-Array) als binäre 4-Byte-Pakete über UART
Format: [Input-ID, High-Byte, Low-Byte, CRC8]
"""

import serial
import paho.mqtt.client as mqtt
import json
import time
import base64
from datetime import datetime
import struct

class ChirpStackMQTTtoUART:
    def __init__(self, mqtt_broker="localhost", mqtt_port=1883, 
                 uart_port='/dev/ttyAMA0', uart_baudrate=115200):
        # UART Setup
        self.ser = serial.Serial(uart_port, uart_baudrate, timeout=1)
        print(f"UART initialisiert auf {uart_port} mit {uart_baudrate} baud")
        
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
            
            # Sende nur Sensordaten über UART
            self.send_uart(sensor_data)
            
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
        # Prüfe ob dekodierte Daten vorhanden sind
        if 'object' in payload and payload['object']:
            decoded_obj = payload['object']
            
            # Suche nach "d" Array in dekodierten Daten
            if 'd' in decoded_obj and isinstance(decoded_obj['d'], list):
                return decoded_obj['d']
        
        # Fallback: Versuche Rohdaten zu dekodieren
        if 'data' in payload:
            try:
                data_bytes = base64.b64decode(payload['data'])
                data_str = data_bytes.decode('utf-8')
                decoded_data = json.loads(data_str)
                
                # Suche nach "d" Array
                if 'd' in decoded_data and isinstance(decoded_data['d'], list):
                    return decoded_data['d']
                    
            except:
                pass
        
        return None
    
    def calculate_crc8(self, data):
        """
        CRC8 Berechnung mit Dallas/Maxim Polynom 0x31
        """
        crc = 0x00
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc = crc << 1
                crc &= 0xFF
        return crc
    
    def create_sensor_packet(self, input_id, sensor_value):
        """
        Erstellt ein 4-Byte-Paket für einen Sensorwert
        Format: [Input-ID, High-Byte, Low-Byte, CRC8]
        """
        # Sensor-Wert auf 12 Bit begrenzen
        sensor_value = sensor_value & 0x0FFF
        
        # Aufteilen in High- und Low-Byte
        high_byte = (sensor_value >> 8) & 0xFF
        low_byte = sensor_value & 0xFF
        
        # CRC8 über die ersten 3 Bytes berechnen
        data_bytes = [input_id, high_byte, low_byte]
        crc8 = self.calculate_crc8(data_bytes)
        
        # 4-Byte-Paket erstellen
        packet = bytes([input_id, high_byte, low_byte, crc8])
        
        return packet
    
    def send_uart(self, data):
        try:
            total_bytes_sent = 0
            packets_sent = 0
            
            # Für jeden Wert im d-Array ein separates 4-Byte-Paket senden
            for index, sensor_value in enumerate(data):
                # Input-ID: 1-basiert (1 für ersten Wert, 2 für zweiten, etc.)
                input_id = index + 1
                
                # Stelle sicher, dass der Wert ein Integer ist
                if isinstance(sensor_value, (int, float)):
                    sensor_value = int(sensor_value)
                else:
                    print(f"Warnung: Ungültiger Sensorwert an Index {index}: {sensor_value}")
                    continue
                
                # Erstelle 4-Byte-Paket
                packet = self.create_sensor_packet(input_id, sensor_value)
                
                # Sende Paket über UART
                self.ser.write(packet)
                self.ser.flush()
                
                total_bytes_sent += 4
                packets_sent += 1
                
                # Debug-Ausgabe
                print(f"  -> Paket {packets_sent}: ID={input_id}, Wert={sensor_value} (0x{sensor_value:03X}), "
                      f"Bytes=[{packet[0]:02X} {packet[1]:02X} {packet[2]:02X} {packet[3]:02X}]")
                
                # Kleine Verzögerung zwischen Paketen (optional)
                time.sleep(0.001)
            
            self.messages_sent += packets_sent
            print(f"  -> UART: {packets_sent} Pakete gesendet ({total_bytes_sent} bytes total)")
            
        except Exception as e:
            print(f"Fehler beim Senden über UART: {e}")
    
    def run(self):
        print("\nChirpStack MQTT to UART Bridge (Binäre Sensordaten)")
        print("=" * 55)
        print(f"MQTT Broker: {self.mqtt_broker}:{self.mqtt_port}")
        print(f"UART Port: {self.ser.port}")
        print("Filter: 'd' Array aus Sensordaten")
        print("Format: 4-Byte-Pakete [Input-ID, High-Byte, Low-Byte, CRC8]")
        print("CRC8: Dallas/Maxim Polynom 0x31")
        print("=" * 55)
        
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
        print(f"  UART Nachrichten gesendet: {self.messages_sent}")
        
        self.client.disconnect()
        self.ser.close()
        print("Verbindungen geschlossen.")

def main():
    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
    UART_PORT = '/dev/ttyAMA0'
    UART_BAUDRATE = 115200
    
    bridge = ChirpStackMQTTtoUART(
        mqtt_broker=MQTT_BROKER,
        mqtt_port=MQTT_PORT,
        uart_port=UART_PORT,
        uart_baudrate=UART_BAUDRATE
    )
    
    bridge.run()

if __name__ == "__main__":
    main()
