"""UART communication module for ChirpStack MQTT to UART Bridge."""

import time
import serial
import logging
from typing import Dict, Any, Optional


class UARTCommunicator:
    """Handles UART communication."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialisiert den UART Communicator.
        
        Parameter:
        config (dict): Die UART-Konfiguration
        logger (logging.Logger): Der Logger für Ausgaben
        """
        self.config = config
        self.logger = logger
        self.ser = None
        self._setup_uart()
    
    def _setup_uart(self) -> None:
        """
        Initialisiert die UART-Schnittstelle mit Support für mehrere Versuche.
        """
        uart_config = self.config.get("uart", {})
        system_config = self.config.get("system", {})
        
        max_retries = system_config.get("retry_attempts", 3)
        retry_delay = system_config.get("retry_delay", 0.5)
        
        # Mapping für Parity-Optionen
        parity_map = {
            "none": serial.PARITY_NONE,
            "even": serial.PARITY_EVEN,
            "odd": serial.PARITY_ODD
        }
        
        for attempt in range(max_retries):
            try:
                self.ser = serial.Serial(
                    port=uart_config.get("port", "/dev/ttyAMA0"),
                    baudrate=uart_config.get("baudrate", 115200),
                    bytesize=uart_config.get("bytesize", 8),
                    parity=parity_map.get(uart_config.get("parity", "none"), serial.PARITY_NONE),
                    stopbits=uart_config.get("stopbits", 1),
                    timeout=uart_config.get("timeout", 1),
                    xonxoff=uart_config.get("xonxoff", False),
                    rtscts=uart_config.get("rtscts", False),
                    dsrdtr=uart_config.get("dsrdtr", False)
                )
                self.logger.info(f"UART initialisiert auf {uart_config.get('port')} mit {uart_config.get('baudrate')} baud")
                return
            except serial.SerialException as e:
                self.logger.error(f"UART Setup Fehler (Versuch {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise
    
    def send(self, message: bytes) -> bool:
        """
        Sendet eine Nachricht über UART.
        
        Parameter:
        message (bytes): Die zu sendende Nachricht
        
        Rückgabewert:
        bool: True bei Erfolg, False bei Fehler
        """
        system_config = self.config.get("system", {})
        max_retries = system_config.get("retry_attempts", 3)
        retry_delay = system_config.get("retry_delay", 0.5)
        
        for attempt in range(max_retries):
            try:
                if not self.ser or not self.ser.is_open:
                    self.logger.warning("UART nicht verfügbar, versuche Wiederverbindung...")
                    self._setup_uart()
                
                bytes_written = self.ser.write(message)
                self.ser.flush()
                
                if bytes_written == len(message):
                    self.logger.info(f"{bytes_written} Bytes erfolgreich an UART gesendet")
                    # Log hex representation of sent data
                    hex_data = ' '.join([f'{b:02X}' for b in message])
                    self.logger.debug(f"UART Hex gesendet: {hex_data}")
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
                    self._setup_uart()
                else:
                    return False
            except Exception as e:
                self.logger.error(f"Unerwarteter Fehler beim UART-Senden: {e}")
                return False
        
        return False
    
    def close(self) -> None:
        """Schließt die UART-Verbindung."""
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
                self.logger.info("UART-Verbindung geschlossen")
        except Exception as e:
            self.logger.debug(f"Fehler beim Schließen der UART-Verbindung: {e}")
