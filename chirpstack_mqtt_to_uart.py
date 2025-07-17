#!/usr/bin/env python3
"""
ChirpStack MQTT to UART Bridge - Config-basierte Version
Sendet Payload-Daten inklusive Device Name über UART
"""

import serial
import paho.mqtt.client as mqtt
import json
import time
import base64
import binascii
import logging
import signal
import sys
import os
from typing import Optional, Dict, Any
import threading
from logging.handlers import RotatingFileHandler

class ChirpStackMQTTtoUART:
    def __init__(self, config_file: str = "config.json"):
        # Konfiguration laden
        self.config = self.load_config(config_file)
        
        # Logging Setup
        self.setup_logging()
        
        # Threading für graceful shutdown
        self.shutdown_event = threading.Event()
        self.setup_signal_handlers()
        
        # UART Setup
        self.ser = None
        self.setup_uart()
        
        # MQTT Setup
        self.client = None
        self.setup_mqtt()
        
        # Statistiken
        self.stats = {
            'messages_received': 0,
            'messages_sent': 0,
            'errors': 0,
            'last_message_time': None,
            'start_time': time.time()
        }

    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Lade Konfiguration aus JSON-Datei"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                print(f"Konfiguration geladen aus {config_file}")
                return config
        except FileNotFoundError:
            print(f"Konfigurationsdatei {config_file} nicht gefunden, verwende Standardwerte")
            return self.get_default_config()
        except json.JSONDecodeError as e:
            print(f"Fehler beim Parsen der Konfiguration: {e}")
            return self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        """Standardkonfiguration"""
        return {
            "mqtt": {
                "broker": "localhost",
                "port": 1883,
                "username": None,
                "password": None,
                "topic": "application/+/device/+/event/up",
                "keepalive": 60,
                "reconnect_delay_min": 1,
                "reconnect_delay_max": 120
            },
            "uart": {
                "port": "/dev/ttyAMA0",
                "baudrate": 115200,
                "bytesize": 8,
                "parity": "none",
                "stopbits": 1,
                "timeout": 1,
                "xonxoff": False,
                "rtscts": False,
                "dsrdtr": False,
                "max_payload_size": 255
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "chirpstack_bridge.log",
                "max_file_size": "10MB",
                "backup_count": 5
            },
            "system": {
                "stats_interval": 300,
                "retry_attempts": 3,
                "retry_delay": 0.5,
                "graceful_shutdown_timeout": 5
            }
        }

    def setup_logging(self):
        """Setup strukturiertes Logging mit Rotation"""
        log_config = self.config["logging"]
        
        # Parse file size
        max_size = log_config.get("max_file_size", "10MB")
        if max_size.endswith("MB"):
            max_bytes = int(max_size[:-2]) * 1024 * 1024
        else:
            max_bytes = 10 * 1024 * 1024
        
        # Setup handlers
        handlers = [logging.StreamHandler(sys.stdout)]
        
        if log_config.get("file"):
            file_handler = RotatingFileHandler(
                log_config["file"],
                maxBytes=max_bytes,
                backupCount=log_config.get("backup_count", 5)
            )
            handlers.append(file_handler)
        
        logging.basicConfig(
            level=getattr(logging, log_config["level"].upper()),
            format=log_config["format"],
            handlers=handlers
        )
        self.logger = logging.getLogger(__name__)

    def setup_signal_handlers(self):
        """Setup Signal Handler für graceful shutdown"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.shutdown_event.set()

    def setup_uart(self):
        """Setup UART mit Retry-Mechanismus"""
        uart_config = self.config["uart"]
        system_config = self.config["system"]
        
        max_retries = system_config["retry_attempts"]
        retry_delay = system_config["retry_delay"]
        
        # Parity mapping
        parity_map = {
            "none": serial.PARITY_NONE,
            "even": serial.PARITY_EVEN,
            "odd": serial.PARITY_ODD
        }
        
        for attempt in range(max_retries):
            try:
                self.ser = serial.Serial(
                    port=uart_config["port"],
                    baudrate=uart_config["baudrate"],
                    bytesize=uart_config["bytesize"],
                    parity=parity_map.get(uart_config["parity"], serial.PARITY_NONE),
                    stopbits=uart_config["stopbits"],
                    timeout=uart_config["timeout"],
                    xonxoff=uart_config["xonxoff"],
                    rtscts=uart_config["rtscts"],
                    dsrdtr=uart_config["dsrdtr"]
                )
                self.logger.info(f"UART initialisiert auf {uart_config['port']} mit {uart_config['baudrate']} baud")
                return
            except serial.SerialException as e:
                self.logger.error(f"UART Setup Fehler (Versuch {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise

    def setup_mqtt(self):
        """Setup MQTT mit Wiederverbindung"""
        mqtt_config = self.config["mqtt"]
        
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        # Authentifizierung wenn konfiguriert
        if mqtt_config.get("username") and mqtt_config.get("password"):
            self.client.username_pw_set(mqtt_config["username"], mqtt_config["password"])
        
        # Automatische Wiederverbindung aktivieren
        self.client.reconnect_delay_set(
            min_delay=mqtt_config["reconnect_delay_min"],
            max_delay=mqtt_config["reconnect_delay_max"]
        )

    def on_connect(self, client, userdata, flags, rc):
        """MQTT Connect Callback"""
        mqtt_config = self.config["mqtt"]
        
        if rc == 0:
            self.logger.info(f"Verbunden mit MQTT-Broker {mqtt_config['broker']}:{mqtt_config['port']}")
            client.subscribe(mqtt_config["topic"])
            self.logger.info(f"Subscribed to {mqtt_config['topic']}")
        else:
            self.logger.error(f"MQTT Verbindung fehlgeschlagen, Code: {rc}")

    def on_disconnect(self, client, userdata, rc):
        """MQTT Disconnect Callback"""
        if rc != 0:
            self.logger.warning(f"Unerwartete MQTT Trennung, Code: {rc}")

    def extract_device_name(self, topic: str) -> str:
        """Extrahiere Device Name aus MQTT Topic"""
        try:
            topic_parts = topic.split('/')
            # Format: application/{app_id}/device/{device_id}/event/up
            if len(topic_parts) >= 4:
                return topic_parts[3]
            else:
                return "unknown"
        except Exception as e:
            self.logger.warning(f"Fehler beim Extrahieren des Device Names: {e}")
            return "unknown"

    def validate_payload(self, payload: bytes) -> bool:
        """Validiere Payload vor dem Senden"""
        uart_config = self.config["uart"]
        max_size = uart_config["max_payload_size"]
        
        if not payload:
            self.logger.warning("Leere Payload empfangen")
            return False
        
        if len(payload) > max_size:
            self.logger.warning(f"Payload zu groß: {len(payload)} Bytes (max: {max_size})")
            return False
        
        return True

    def decode_payload(self, json_data: dict) -> Optional[bytes]:
        """Dekodiere Payload mit robuster Fehlerbehandlung"""
        try:
            # Base64 dekodieren
            decoded_payload = base64.b64decode(json_data['data'])
            self.logger.debug(f"Base64 dekodiert ({len(decoded_payload)} Bytes): {decoded_payload.hex()}")
            
            # Prüfe ob es ASCII-Hex ist (doppelte Kodierung)
            try:
                ascii_hex = decoded_payload.decode('ascii')
                if all(c in '0123456789abcdefABCDEF' for c in ascii_hex):
                    self.logger.debug(f"ASCII-Hex String erkannt: {ascii_hex}")
                    final_payload = binascii.unhexlify(ascii_hex)
                    self.logger.debug(f"Final Payload ({len(final_payload)} Bytes): {final_payload.hex()}")
                    return final_payload
                else:
                    # Nicht alle Zeichen sind Hex, nutze direkte Daten
                    return decoded_payload
            except (UnicodeDecodeError, ValueError):
                # Falls nicht ASCII-Hex, nutze direkte Daten
                self.logger.debug(f"Direkte Payload ({len(decoded_payload)} Bytes): {decoded_payload.hex()}")
                return decoded_payload
                
        except Exception as e:
            self.logger.error(f"Fehler beim Dekodieren der Payload: {e}")
            return None

    def create_uart_message(self, device_name: str, payload: bytes) -> bytes:
        """Erstelle UART-Nachricht mit Device Name und Payload"""
        try:
            # Format: DEVICE_NAME:PAYLOAD_HEX\n
            message = f"{device_name}:{payload.hex()}\n"
            return message.encode('utf-8')
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen der UART-Nachricht: {e}")
            return None

    def send_to_uart(self, message: bytes) -> bool:
        """Sende Nachricht an UART mit Retry-Mechanismus"""
        system_config = self.config["system"]
        max_retries = system_config["retry_attempts"]
        retry_delay = system_config["retry_delay"]
        
        for attempt in range(max_retries):
            try:
                if not self.ser or not self.ser.is_open:
                    self.logger.warning("UART nicht verfügbar, versuche Wiederverbindung...")
                    self.setup_uart()
                
                bytes_written = self.ser.write(message)
                self.ser.flush()
                
                if bytes_written == len(message):
                    self.logger.info(f"{bytes_written} Bytes erfolgreich an UART gesendet")
                    self.stats['messages_sent'] += 1
                    return True
                else:
                    self.logger.warning(f"Nur {bytes_written}/{len(message)} Bytes gesendet")
                    
            except serial.SerialException as e:
                self.logger.error(f"UART Fehler (Versuch {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    try:
                        self.ser.close()
                    except:
                        pass
                    self.setup_uart()
                else:
                    self.stats['errors'] += 1
                    return False
            except Exception as e:
                self.logger.error(f"Unerwarteter Fehler beim UART-Senden: {e}")
                self.stats['errors'] += 1
                return False
        
        return False

    def on_message(self, client, userdata, msg):
        """MQTT Message Callback mit Device Name Integration"""
        try:
            self.stats['messages_received'] += 1
            self.stats['last_message_time'] = time.time()
            
            self.logger.info(f"MQTT Nachricht erhalten: {msg.topic}")
            
            # Extrahiere Device Name aus Topic
            device_name = self.extract_device_name(msg.topic)
            self.logger.info(f"Device Name: {device_name}")
            
            # JSON parsen
            json_data = json.loads(msg.payload)
            
            # Payload dekodieren
            payload = self.decode_payload(json_data)
            if payload is None:
                self.logger.error("Payload konnte nicht dekodiert werden")
                self.stats['errors'] += 1
                return
            
            # UART-Nachricht erstellen (Device Name + Payload)
            uart_message = self.create_uart_message(device_name, payload)
            if uart_message is None:
                self.logger.error("UART-Nachricht konnte nicht erstellt werden")
                self.stats['errors'] += 1
                return
            
            # Nachricht validieren
            if not self.validate_payload(uart_message):
                self.logger.error("UART-Nachricht-Validierung fehlgeschlagen")
                self.stats['errors'] += 1
                return
            
            # An UART senden
            self.logger.info(f"Sende an UART: {uart_message.decode('utf-8').strip()}")
            if not self.send_to_uart(uart_message):
                self.logger.error("Fehler beim Senden an UART")
                self.stats['errors'] += 1
                
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON Parse Fehler: {e}")
            self.stats['errors'] += 1
        except Exception as e:
            self.logger.error(f"Unerwarteter Fehler in on_message: {e}")
            self.stats['errors'] += 1

    def print_stats(self):
        """Drucke erweiterte Statistiken"""
        uptime = time.time() - self.stats['start_time']
        uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime))
        
        self.logger.info(f"Statistiken - Uptime: {uptime_str}, "
                        f"Empfangen: {self.stats['messages_received']}, "
                        f"Gesendet: {self.stats['messages_sent']}, "
                        f"Fehler: {self.stats['errors']}")

    def connect_mqtt(self):
        """Verbinde mit MQTT-Broker"""
        mqtt_config = self.config["mqtt"]
        
        try:
            self.client.connect(
                mqtt_config["broker"], 
                mqtt_config["port"], 
                mqtt_config["keepalive"]
            )
            return True
        except Exception as e:
            self.logger.error(f"MQTT Verbindung fehlgeschlagen: {e}")
            return False

    def run(self):
        """Hauptlauf mit verbesserter Fehlerbehandlung"""
        self.logger.info("ChirpStack MQTT to UART Bridge mit Device Name gestartet...")
        
        # MQTT verbinden
        if not self.connect_mqtt():
            self.logger.error("Kann nicht mit MQTT-Broker verbinden")
            return
        
        # Statistik-Timer
        last_stats_time = time.time()
        stats_interval = self.config["system"]["stats_interval"]
        
        try:
            while not self.shutdown_event.is_set():
                # MQTT Loop mit Timeout
                self.client.loop(timeout=1.0)
                
                # Periodische Statistiken
                current_time = time.time()
                if current_time - last_stats_time > stats_interval:
                    self.print_stats()
                    last_stats_time = current_time
                
        except Exception as e:
            self.logger.error(f"Fehler in Hauptschleife: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup-Routine für graceful shutdown"""
        self.logger.info("Cleanup wird ausgeführt...")
        
        timeout = self.config["system"]["graceful_shutdown_timeout"]
        
        try:
            if self.client:
                self.client.disconnect()
                self.client.loop_stop()
        except:
            pass
        
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except:
            pass
        
        self.print_stats()
        self.logger.info("Bridge gestoppt")

if __name__ == "__main__":
    # Config-Datei über Kommandozeile oder Standard
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    
    bridge = ChirpStackMQTTtoUART(config_file)
    bridge.run()
