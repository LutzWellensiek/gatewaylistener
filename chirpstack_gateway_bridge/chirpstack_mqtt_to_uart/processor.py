"""Message processor module for ChirpStack MQTT to UART Bridge."""

import base64
import binascii
import logging
from typing import Optional, Dict, Any


class MessageProcessor:
    """Handles message processing including decoding and validation."""

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialisiert den Message Processor.

        Parameter:
        config (dict): Die Konfigurationsparameter
        logger (logging.Logger): Der Logger für Ausgaben
        """
        self.config = config
        self.logger = logger

    def validate_payload(self, payload: bytes) -> bool:
        """
        Validiert die Payload, bevor sie über UART gesendet wird.
        Überprüft auf maximale Größenbegrenzung.

        Parameter:
        payload (bytes): Die binäre Payload der Nachricht

        Rückgabewert:
        bool: True, wenn payload gültig ist, sonst False
        """
        uart_config = self.config.get("uart", {})
        max_size = uart_config.get("max_payload_size", 255)

        if not payload:
            self.logger.warning("Leere Payload empfangen")
            return False

        if len(payload) > max_size:
            self.logger.warning(f"Payload zu groß: {len(payload)} Bytes (max: {max_size})")
            return False

        return True

    def decode_payload(self, json_data: dict) -> Optional[bytes]:
        """
        Dekodiert die Payload einer MQTT-Nachricht.
        Unterstützt Base64- und optionale ASCII-Hex-Dekodierung.

        Parameter:
        json_data (dict): Das JSON-Datenfeld der empfangenen Nachricht

        Rückgabewert:
        Optional[bytes]: Die dekodierte Payload oder None bei Fehler
        """
        try:
            decoded_payload = base64.b64decode(json_data['data'])
            self.logger.debug(f"Base64 dekodiert ({len(decoded_payload)} Bytes)")

            final_payload = self._check_double_encoding(decoded_payload)
            return final_payload

        except Exception as e:
            self.logger.error(f"Fehler beim Dekodieren der Payload: {e}")
            return None

    def _check_double_encoding(self, decoded_payload: bytes) -> bytes:
        """
        Erkennung und Behandlung von doppelt kodierten Payloads.
        Fragt nach ASCII-Hex-Dekodierung, falls zutreffend.

        Parameter:
        decoded_payload (bytes): Bereits base64-dekodierte Daten

        Rückgabewert:
        bytes: Die endgültige dekodierte Payload
        """
        try:
            ascii_hex = decoded_payload.decode('ascii')
            if all(c in '0123456789abcdefABCDEF' for c in ascii_hex):
                self.logger.debug(f"ASCII-Hex String erkannt: {ascii_hex}")
                final_payload = binascii.unhexlify(ascii_hex)
                self.logger.debug(f"Final Payload ({len(final_payload)} Bytes): {final_payload.hex()}")
                return final_payload
            else:
                return decoded_payload
        except (UnicodeDecodeError, ValueError):
            self.logger.debug(f"Direkte Payload ({len(decoded_payload)} Bytes): {decoded_payload.hex()}")
            return decoded_payload

    def create_uart_message(self, device_name: str, payload: bytes) -> bytes:
        """
        Erstellt eine formatierte Nachricht für den Versand über UART.
        Fügt den Device-Namen als Präfix zur Payload hinzu.

        Parameter:
        device_name (str): Der Name des Geräts
        payload (bytes): Die binären Daten der Nachricht

        Rückgabewert:
        bytes: Die formatierte Nachricht oder None bei Fehler
        """
        try:
            device_prefix = f"{device_name}: ".encode('utf-8')
            message = device_prefix + payload
            return message
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen der UART-Nachricht: {e}")
            return None

