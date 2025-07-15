#!/usr/bin/env python3
"""
ChirpStack MQTT to UART Bridge - Sendet unformatierte Payload-Daten direkt über UART
"""

import serial
import paho.mqtt.client as mqtt
import json
import time
import base64
import binascii

class ChirpStackMQTTtoUART:
    def __init__(self, mqtt_broker="localhost", mqtt_port=1883, 
                 uart_port='/dev/ttyAMA0', uart_baudrate=115200):
        # UART Setup mit erweiterten Optionen
        self.ser = serial.Serial(
            port=uart_port,
            baudrate=uart_baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        )
        print(f"UART initialisiert auf {uart_port} mit {uart_baudrate} baud")
        
        # MQTT Setup
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.connect(mqtt_broker, mqtt_port, 60)
        print(f"Verbunden mit MQTT-Broker {mqtt_broker}:{mqtt_port}")

    def on_connect(self, client, userdata, flags, rc):
        print("Verbunden mit MQTT Broker, Code: ", rc)
        client.subscribe("application/+/device/+/event/up")

    def on_message(self, client, userdata, msg):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] MQTT Nachricht erhalten: {msg.topic}")
        
        try:
            json_data = json.loads(msg.payload)
            
            # Dekodiere Base64-Payload
            decoded_payload = base64.b64decode(json_data['data'])
            print(f"[{timestamp}] Base64 dekodiert ({len(decoded_payload)} Bytes): {decoded_payload.hex()}")
            
            # Prüfe ob es ASCII-Hex ist (doppelte Kodierung)
            try:
                # Versuche ASCII-Hex zu dekodieren
                ascii_hex = decoded_payload.decode('ascii')
                print(f"[{timestamp}] ASCII-Hex String: {ascii_hex}")
                
                # Konvertiere Hex-String zu Binärdaten
                final_payload = binascii.unhexlify(ascii_hex)
                print(f"[{timestamp}] Final Payload ({len(final_payload)} Bytes): {final_payload.hex()}")
                
            except (UnicodeDecodeError, ValueError):
                # Falls nicht ASCII-Hex, nutze direkte Daten
                final_payload = decoded_payload
                print(f"[{timestamp}] Direkte Payload ({len(final_payload)} Bytes): {final_payload.hex()}")
            
            # Sende unformatiertes Final-Payload direkt an UART
            bytes_written = self.ser.write(final_payload)
            self.ser.flush()  # Stelle sicher, dass Daten gesendet werden
            print(f"[{timestamp}] {bytes_written} Bytes an UART gesendet und geleert.")
            
        except Exception as e:
            print(f"[{timestamp}] Fehler beim Verarbeiten der Nachricht: {e}")
            import traceback
            traceback.print_exc()

    def run(self):
        print("ChirpStack MQTT to UART Bridge gestartet...")
        print("Warte auf MQTT-Nachrichten...")
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("\nStopping bridge...")
            self.client.disconnect()
            self.ser.close()

if __name__ == "__main__":
    bridge = ChirpStackMQTTtoUART()
    bridge.run()
