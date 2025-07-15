#!/usr/bin/env python3
"""
Raspberry Pi to AVR UART Bridge
Sendet Daten vom Raspberry Pi an das AVR-Board über UART
Kompatibel mit der RS485-Implementierung des AVR-Boards
"""

import serial
import json
import time
import threading
import struct
from datetime import datetime

class RaspberryToAVRUART:
    def __init__(self, uart_port='/dev/ttyAMA0', uart_baudrate=115200):
        """
        Initialisiert die UART-Verbindung zum AVR-Board
        
        Args:
            uart_port (str): UART-Port (z.B. '/dev/ttyAMA0' für Raspberry Pi)
            uart_baudrate (int): Baudrate (muss mit AVR-Board übereinstimmen)
        """
        try:
            # UART Setup - Konfiguration für RS485-Kompatibilität
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
            print(f"Konfiguration: 8N1, kompatibel mit AVR RS485")
            
            # Statistiken
            self.messages_sent = 0
            self.responses_received = 0
            
            # Flag für kontinuierlichen Betrieb
            self.running = False
            
            # Input-IDs für RS485-Frames (kompatibel mit AVR-Board)
            self.input_ids = {
                'temp1': 0x01,
                'temp2': 0x02,
                'deflection': 0x03,
                'pressure': 0x04,
                'deflection_2': 0x05,
                'internal_temp': 0x09
            }
            
            # Standardwerte für fehlende Sensordaten
            self.default_sensor_values = {
                'temp1': 20.0,      # °C
                'temp2': 20.0,      # °C
                'deflection': 0.0,  # °
                'pressure': 0.0,    # bar
                'deflection_2': 0.0, # °
                'internal_temp': 25.0  # °C
            }
            
        except Exception as e:
            print(f"Fehler beim Initialisieren der UART-Verbindung: {e}")
            raise
    
    def send_sensor_data(self, sensor_data):
        """
        Sendet Sensordaten an das AVR-Board im RS485-Frame-Format
        
        Args:
            sensor_data (dict oder list): Sensordaten als Dictionary oder Array
        """
        try:
            # Normalisiere Eingabedaten
            if isinstance(sensor_data, list):
                # Konvertiere Array in Dictionary
                normalized_data = {
                    'temp1': sensor_data[0] if len(sensor_data) > 0 else None,
                    'temp2': sensor_data[1] if len(sensor_data) > 1 else None,
                    'deflection': sensor_data[2] if len(sensor_data) > 2 else None,
                    'pressure': sensor_data[3] if len(sensor_data) > 3 else None,
                    'deflection_2': sensor_data[4] if len(sensor_data) > 4 else None
                }
            else:
                normalized_data = sensor_data
            
            # Fülle fehlende Sensordaten mit Platzhaltern
            complete_sensor_data = {}
            for key in self.default_sensor_values:
                if key in normalized_data and normalized_data[key] is not None:
                    complete_sensor_data[key] = normalized_data[key]
                else:
                    complete_sensor_data[key] = self.default_sensor_values[key]
                    print(f"  Platzhalter für {key}: {self.default_sensor_values[key]}")
            
            # Sende jeden Sensorwert als separaten RS485-Frame
            for sensor_type, value in complete_sensor_data.items():
                if sensor_type in self.input_ids:
                    self.send_rs485_frame(self.input_ids[sensor_type], value)
                    time.sleep(0.05)  # Kurze Pause zwischen Frames
            
            self.messages_sent += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Sensordaten gesendet: {complete_sensor_data}")
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Senden über UART: {e}")
            return False
    
    def send_raw_data(self, data):
        """
        Sendet rohe Daten an das AVR-Board
        
        Args:
            data (str): Rohe Daten als String
        """
        try:
            message = data + '\n'
            self.ser.write(message.encode('utf-8'))
            self.ser.flush()
            
            self.messages_sent += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Raw data gesendet: {data}")
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Senden roher Daten: {e}")
            return False
    
    def send_command(self, command, params=None):
        """
        Sendet einen Befehl an das AVR-Board
        
        Args:
            command (str): Befehlsname
            params (dict): Optionale Parameter
        """
        try:
            command_packet = {
                "timestamp": datetime.now().isoformat(),
                "type": "command",
                "command": command,
                "params": params or {}
            }
            
            json_data = json.dumps(command_packet, separators=(',', ':'))
            message = json_data + '\n'
            
            self.ser.write(message.encode('utf-8'))
            self.ser.flush()
            
            self.messages_sent += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Befehl gesendet: {command}")
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Senden des Befehls: {e}")
            return False
    
    def read_response(self, timeout=5):
        """
        Liest eine Antwort vom AVR-Board
        
        Args:
            timeout (int): Timeout in Sekunden
            
        Returns:
            str: Empfangene Antwort oder None bei Timeout
        """
        try:
            # Setze temporären Timeout
            original_timeout = self.ser.timeout
            self.ser.timeout = timeout
            
            # Lese Zeile
            response = self.ser.readline().decode('utf-8').strip()
            
            # Setze ursprünglichen Timeout zurück
            self.ser.timeout = original_timeout
            
            if response:
                self.responses_received += 1
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Antwort empfangen: {response}")
                return response
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Timeout beim Warten auf Antwort")
                return None
                
        except Exception as e:
            print(f"Fehler beim Lesen der Antwort: {e}")
            return None
    
    def start_monitoring(self):
        """
        Startet kontinuierliche Überwachung der UART-Verbindung
        """
        self.running = True
        monitor_thread = threading.Thread(target=self._monitor_uart)
        monitor_thread.daemon = True
        monitor_thread.start()
        print("UART-Überwachung gestartet")
    
    def stop_monitoring(self):
        """
        Stoppt die kontinuierliche Überwachung
        """
        self.running = False
        print("UART-Überwachung gestoppt")
    
    def _monitor_uart(self):
        """
        Überwacht eingehende UART-Daten (läuft in separatem Thread)
        """
        while self.running:
            try:
                if self.ser.in_waiting > 0:
                    data = self.ser.readline().decode('utf-8').strip()
                    if data:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] AVR -> Pi: {data}")
                        self.responses_received += 1
                else:
                    time.sleep(0.1)
            except Exception as e:
                if self.running:
                    print(f"Fehler beim Überwachen der UART: {e}")
                    time.sleep(1)
    
    def test_connection(self):
        """
        Testet die Verbindung zum AVR-Board
        """
        print("Teste Verbindung zum AVR-Board...")
        
        # Sende Test-Nachricht
        test_data = ["test", "connection", "avr"]
        if self.send_sensor_data(test_data):
            print("Test-Nachricht gesendet")
            
            # Warte auf Antwort
            response = self.read_response(timeout=3)
            if response:
                print("Verbindung erfolgreich getestet")
                return True
            else:
                print("Keine Antwort vom AVR-Board erhalten")
                return False
        else:
            print("Fehler beim Senden der Test-Nachricht")
            return False
    
    def get_statistics(self):
        """
        Gibt Statistiken über die UART-Kommunikation zurück
        """
        return {
            "messages_sent": self.messages_sent,
            "responses_received": self.responses_received,
            "port": self.ser.port,
            "baudrate": self.ser.baudrate,
            "is_open": self.ser.is_open
        }
    
    def close(self):
        """
        Schließt die UART-Verbindung
        """
        self.stop_monitoring()
        
        if self.ser.is_open:
            self.ser.close()
            
        stats = self.get_statistics()
        print(f"\nStatistik:")
        print(f"  Nachrichten gesendet: {stats['messages_sent']}")
        print(f"  Antworten empfangen: {stats['responses_received']}")
        print(f"  Port: {stats['port']}")
        print(f"  Baudrate: {stats['baudrate']}")
        print("UART-Verbindung geschlossen.")

def main():
    """
    Hauptfunktion für Testzwecke
    """
    # Konfiguration
    UART_PORT = '/dev/ttyAMA0'  # Raspberry Pi UART
    UART_BAUDRATE = 115200       # Muss mit AVR-Board übereinstimmen
    
    print("Raspberry Pi to AVR UART Bridge")
    print("=" * 40)
    
    try:
        # Initialisiere UART-Verbindung
        uart_bridge = RaspberryToAVRUART(
            uart_port=UART_PORT,
            uart_baudrate=UART_BAUDRATE
        )
        
        # Starte Überwachung
        uart_bridge.start_monitoring()
        
        # Teste Verbindung
        uart_bridge.test_connection()
        
        # Beispiel: Sende verschiedene Datentypen
        print("\nSende Beispieldaten...")
        
        # Sensordaten
        sensor_data = [23.5, 45.2, 78.9, 12.3]
        uart_bridge.send_sensor_data(sensor_data)
        
        time.sleep(1)
        
        # Befehl
        uart_bridge.send_command("set_mode", {"mode": "continuous", "interval": 1000})
        
        time.sleep(1)
        
        # Rohe Daten
        uart_bridge.send_raw_data("Hello AVR Board")
        
        # Warte auf Benutzereingabe
        print("\nDrücke Enter zum Beenden...")
        input()
        
    except KeyboardInterrupt:
        print("\nShutdown durch Benutzer...")
    except Exception as e:
        print(f"Fehler: {e}")
    finally:
        uart_bridge.close()

if __name__ == "__main__":
    main()
