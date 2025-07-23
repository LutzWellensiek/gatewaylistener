"""Logger module for ChirpStack MQTT to UART Bridge."""

import sys
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, Any


def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    """
    Setzt das Logging-System auf.
    Verwendet eine Rotations-Strategie für Log-Dateien basierend auf der Konfiguration.
    
    Parameter:
    config (dict): Die Konfigurationsparameter für das Logging
    
    Rückgabewert:
    logging.Logger: Der konfigurierte Logger
    """
    log_config = config.get("logging", {})
    
    # Datei-Größe analysieren
    max_size = log_config.get("max_file_size", "10MB")
    if max_size.endswith("MB"):
        max_bytes = int(max_size[:-2]) * 1024 * 1024
    else:
        max_bytes = 10 * 1024 * 1024  # Standardgröße 10MB
    
    # Logging-Handler einrichten
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # Dateibasiertes Logging, wenn in Konfiguration angegeben
    if log_config.get("file"):
        file_handler = RotatingFileHandler(
            log_config["file"],
            maxBytes=max_bytes,
            backupCount=log_config.get("backup_count", 5)
        )
        handlers.append(file_handler)
    
    logging.basicConfig(
        level=getattr(logging, log_config.get("level", "INFO").upper()),
        format=log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
        handlers=handlers
    )
    
    return logging.getLogger(__name__)
