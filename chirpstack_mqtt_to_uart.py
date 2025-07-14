#!/usr/bin/env python3
"""
ChirpStack MQTT to UART Bridge
Empfängt nur tatsächlich gesendete LoRaWAN-Daten vom ChirpStack MQTT Forwarder 
und leitet sie über UART weiter
"""

import serial
import paho.mqtt.client as mqtt
import json
import time
import base64
from datetime import datetime

class ChirpStackMQTTtoUART:
    def __init__(self, mqtt_broker="localhost", mqtt_port=1883, 
                 uart_port='/dev/ttyAMA0', uart_baudrate=9600):
        """
        Initialisiert die MQTT-zu-UART Bridge
        """
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
            
            # Erstelle UART Nachricht nur mit relevanten Daten
            uart_message = {
                'msg_id': self.messages_received,  # Eindeutige Message-ID für ACK
                'timestamp': timestamp,
                'type': 'uplink_data',
                'data': self.extract_uplink_data(payload)
            }
            
            # Sende über UART
            self.send_uart(uart_message)
            
            # Log
            print(f"\n[{timestamp}] Uplink-Daten empfangen:")
            data = uart_message['data']
            print(f"  Device: {data.get('dev_eui', 'unknown')}")
            print(f"  Payload: {data.get('data_hex', 'N/A')}")
            print(f"  RSSI: {data.get('rssi', 'N/A')} dBm")
            print(f"  SNR: {data.get('snr', 'N/A')} dB")
            
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
        # (nicht um leere Pakete oder Heartbeats)
        try:
            data_bytes = base64.b64decode(payload['data'])
            if len(data_bytes) == 0:
                return False
        except:
            return False
        
        return True
    
    def extract_uplink_data(self, payload):
        """Extrahiert nur die relevanten Uplink-Daten"""
        data = {}
        
        # Device Info
        if 'deviceInfo' in payload:
            data['dev_eui'] = payload['deviceInfo'].get('devEui')
            data['device_name'] = payload['deviceInfo'].get('deviceName')
            data['application_name'] = payload['deviceInfo'].get('applicationName')
        
        # Frame Info
        data['f_cnt'] = payload.get('fCnt')
        data['f_port'] = payload.get('fPort')
        
        # Payload-Daten
        if 'data' in payload:
            data['data_base64'] = payload['data']
            try:
                decoded_bytes = base64.b64decode(payload['data'])
                data['data_hex'] = decoded_bytes.hex()
                data['data_size'] = len(decoded_bytes)
            except:
                pass
        
        # Empfangsqualität (nur erste Gateway-Info)
        if 'rxInfo' in payload and payload['rxInfo']:
            rx = payload['rxInfo'][0]
            data['gateway_id'] = rx.get('gatewayId')
            data['rssi'] = rx.get('rssi')
            data['snr'] = rx.get('snr')
            data['channel'] = rx.get('channel')
        
        # Sendeeinstellungen
        if 'txInfo' in payload:
            data['frequency'] = payload['txInfo'].get('frequency')
            if 'modulation' in payload['txInfo'] and 'lora' in payload['txInfo']['modulation']:
                lora_mod = payload['txInfo']['modulation']['lora']
                data['spreading_factor'] = lora_mod.get('spreadingFactor')
                data['bandwidth'] = lora_mod.get('bandwidth')
                data['coding_rate'] = lora_mod.get('codeRate')
        
        # Dekodierte Daten (falls vorhanden)
        if 'object' in payload:
            data['decoded_object'] = payload['object']
        
        return data
    
    def send_uart(self, data):
        """Sendet Daten über UART"""
        try:
            # Konvertiere zu JSON
            json_data = json.dumps(data, separators=(',', ':'))
            message = json_data + '\n'
            
            # Sende über UART
            self.ser.write(message.encode('utf-8'))
            self.ser.flush()
            
            self.messages_sent += 1
            print(f"  -> UART gesendet ({len(message)} bytes)")
            
            # Warte kurz auf ACK (optional)
            time.sleep(0.1)
            if self.ser.in_waiting > 0:
                response = self.ser.readline().decode('utf-8').strip()
                if response.startswith("ACK:"):
                    print(f"  <- ACK empfangen: {response}")
                else:
                    print(f"  <- Antwort: {response}")
            
        except Exception as e:
            print(f"Fehler beim Senden über UART: {e}")
    
    def run(self):
        """Hauptschleife"""
        print("\nChirpStack MQTT to UART Bridge (Nur Uplink-Daten)")
        print("=" * 50)
        print(f"MQTT Broker: {self.mqtt_broker}:{self.mqtt_port}")
        print(f"UART Port: {self.ser.port}")
        print("Filter: Nur tatsächlich empfangene Sensor-Daten")
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
        print(f"  UART Nachrichten gesendet: {self.messages_sent}")
        
        self.client.disconnect()
        self.ser.close()
        print("Verbindungen geschlossen.")

def main():
    # Konfiguration
    MQTT_BROKER = "localhost"  # ChirpStack MQTT Broker
    MQTT_PORT = 1883
    UART_PORT = '/dev/ttyAMA0'  # GPIO14/15
    UART_BAUDRATE = 115200
    
    # Erstelle und starte Bridge
    bridge = ChirpStackMQTTtoUART(
        mqtt_broker=MQTT_BROKER,
        mqtt_port=MQTT_PORT,
        uart_port=UART_PORT,
        uart_baudrate=UART_BAUDRATE
    )
    
    bridge.run()

if __name__ == "__main__":
    main()
