#!/usr/bin/env python3
"""
ChirpStack MQTT to UART Bridge
Empfängt LoRaWAN-Daten vom ChirpStack MQTT Forwarder und leitet sie über UART weiter
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
            
            # Subscribe zu ChirpStack Topics
            # Gateway Events
            client.subscribe("gateway/+/event/+")
            print("Subscribed zu: gateway/+/event/+")
            
            # Application Events (uplink messages)
            client.subscribe("application/+/device/+/event/up")
            print("Subscribed zu: application/+/device/+/event/up")
            
            # Device Status
            client.subscribe("application/+/device/+/event/status")
            print("Subscribed zu: application/+/device/+/event/status")
            
            # Join Events
            client.subscribe("application/+/device/+/event/join")
            print("Subscribed zu: application/+/device/+/event/join")
            
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
            
            # Zeitstempel hinzufügen
            timestamp = datetime.now().isoformat()
            
            # Erstelle UART Nachricht
            uart_message = {
                'timestamp': timestamp,
                'topic': msg.topic,
                'message_type': self.get_message_type(msg.topic),
                'data': self.process_chirpstack_data(payload, msg.topic)
            }
            
            # Sende über UART
            self.send_uart(uart_message)
            
            # Log
            print(f"\n[{timestamp}] MQTT Nachricht empfangen:")
            print(f"  Topic: {msg.topic}")
            print(f"  Typ: {uart_message['message_type']}")
            
            # Zeige relevante Daten
            if 'deviceInfo' in payload:
                print(f"  Device: {payload['deviceInfo'].get('devEui', 'unknown')}")
            if 'rxInfo' in payload and payload['rxInfo']:
                print(f"  RSSI: {payload['rxInfo'][0].get('rssi', 'N/A')} dBm")
                print(f"  SNR: {payload['rxInfo'][0].get('snr', 'N/A')} dB")
            
        except Exception as e:
            print(f"Fehler beim Verarbeiten der MQTT Nachricht: {e}")
    
    def get_message_type(self, topic):
        """Ermittelt den Nachrichtentyp aus dem Topic"""
        if '/event/up' in topic:
            return 'uplink'
        elif '/event/join' in topic:
            return 'join'
        elif '/event/status' in topic:
            return 'status'
        elif '/event/stats' in topic:
            return 'gateway_stats'
        elif '/event/ack' in topic:
            return 'ack'
        else:
            return 'unknown'
    
    def process_chirpstack_data(self, payload, topic):
        """Verarbeitet ChirpStack-spezifische Daten"""
        processed = {}
        
        # Device Info
        if 'deviceInfo' in payload:
            processed['device'] = {
                'dev_eui': payload['deviceInfo'].get('devEui'),
                'device_name': payload['deviceInfo'].get('deviceName'),
                'application_id': payload['deviceInfo'].get('applicationId'),
                'application_name': payload['deviceInfo'].get('applicationName')
            }
        
        # RX Info (Empfangsqualität)
        if 'rxInfo' in payload and payload['rxInfo']:
            rx = payload['rxInfo'][0]  # Erste Gateway-Info
            processed['rx_info'] = {
                'gateway_id': rx.get('gatewayId'),
                'rssi': rx.get('rssi'),
                'snr': rx.get('snr'),
                'channel': rx.get('channel'),
                'rf_chain': rx.get('rfChain')
            }
        
        # TX Info (Sendeeinstellungen)
        if 'txInfo' in payload:
            processed['tx_info'] = {
                'frequency': payload['txInfo'].get('frequency'),
                'modulation': payload['txInfo'].get('modulation', {}).get('lora', {}),
                'data_rate': payload['txInfo'].get('dr')
            }
        
        # Uplink-spezifische Daten
        if '/event/up' in topic:
            # Frame Counter
            processed['f_cnt'] = payload.get('fCnt')
            processed['f_port'] = payload.get('fPort')
            
            # Payload-Daten
            if 'data' in payload:
                # Base64 decodierte Daten
                processed['data_base64'] = payload['data']
                try:
                    decoded_bytes = base64.b64decode(payload['data'])
                    processed['data_hex'] = decoded_bytes.hex()
                    processed['data_size'] = len(decoded_bytes)
                except:
                    pass
            
            # Object (falls vorhanden - decoded payload)
            if 'object' in payload:
                processed['decoded_object'] = payload['object']
        
        # Gateway Stats
        if '/stats' in topic:
            if 'rxPacketsReceived' in payload:
                processed['gateway_stats'] = {
                    'rx_packets': payload.get('rxPacketsReceived'),
                    'rx_packets_ok': payload.get('rxPacketsReceivedOk'),
                    'tx_packets': payload.get('txPacketsEmitted')
                }
        
        return processed
    
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
            
        except Exception as e:
            print(f"Fehler beim Senden über UART: {e}")
    
    def run(self):
        """Hauptschleife"""
        print("\nChirpStack MQTT to UART Bridge")
        print("=" * 50)
        print(f"MQTT Broker: {self.mqtt_broker}:{self.mqtt_port}")
        print(f"UART Port: {self.ser.port}")
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
