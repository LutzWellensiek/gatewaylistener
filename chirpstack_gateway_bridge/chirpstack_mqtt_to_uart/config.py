"""Configuration management module for ChirpStack MQTT to UART Bridge."""

import json
import logging
from typing import Dict, Any


def load_config(config_file: str) -> Dict[str, Any]:
    """
    Lädt die Konfiguration aus einer JSON-Datei.
    Falls die Datei nicht vorhanden ist, werden Standardwerte verwendet.
    
    Parameter:
    config_file (str): Pfad zur Konfigurationsdatei
    
    Rückgabewert:
    dict: Die geladenen Konfigurationsparameter
    """
    temp_logger = logging.getLogger(__name__)
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            temp_logger.info(f"Konfiguration geladen aus {config_file}")
            return config
    except FileNotFoundError:
        temp_logger.warning(f"Konfigurationsdatei {config_file} nicht gefunden, verwende Standardwerte")
        return get_default_config()
    except json.JSONDecodeError as e:
        temp_logger.error(f"Fehler beim Parsen der Konfiguration: {e}")
        return get_default_config()


def get_default_config() -> Dict[str, Any]:
    """Gibt die Standardkonfiguration zurück."""
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
