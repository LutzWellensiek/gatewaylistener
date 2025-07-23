"""MQTT handler module for ChirpStack MQTT to UART Bridge."""

import logging
import paho.mqtt.client as mqtt
from typing import Dict, Any, Callable, Optional


class MQTTHandler:
    """Manages MQTT connections and message handling."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger, message_callback: Callable):
        """
        Initialisiert den MQTT Handler.
        
        Parameter:
        config (dict): Die MQTT-Konfiguration
        logger (logging.Logger): Der Logger für Ausgaben
        message_callback (Callable): Callback-Funktion für empfangene Nachrichten
        """
        self.config = config
        self.logger = logger
        self.message_callback = message_callback
        self.client = None
        self._setup_mqtt()
    
    def _setup_mqtt(self) -> None:
        """Erstellt und konfiguriert den MQTT-Client."""
        mqtt_config = self.config.get("mqtt", {})
        
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        # Setze Benutzer und Passwort, falls vorhanden
        if mqtt_config.get("username") and mqtt_config.get("password"):
            self.client.username_pw_set(mqtt_config["username"], mqtt_config["password"])
        
        # Setze Wiederverbindungsstrategie
        self.client.reconnect_delay_set(
            min_delay=mqtt_config.get("reconnect_delay_min", 1),
            max_delay=mqtt_config.get("reconnect_delay_max", 120)
        )
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback für erfolgreiche MQTT-Verbindung."""
        mqtt_config = self.config.get("mqtt", {})
        
        if rc == 0:
            self.logger.info(f"Verbunden mit MQTT-Broker {mqtt_config.get('broker')}:{mqtt_config.get('port')}")
            topic = mqtt_config.get("topic", "application/+/device/+/event/up")
            client.subscribe(topic)
            self.logger.info(f"Subscribed to {topic}")
        else:
            self.logger.error(f"MQTT Verbindung fehlgeschlagen, Code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback für MQTT-Verbindungsverlust."""
        if rc != 0:
            self.logger.warning(f"Unerwartete MQTT Trennung, Code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """
        Callback für empfangene MQTT-Nachrichten.
        Leitet die Nachricht an die registrierte Callback-Funktion weiter.
        """
        try:
            self.logger.info(f"MQTT Nachricht erhalten: {msg.topic}")
            self.message_callback(msg.topic, msg.payload)
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten der MQTT-Nachricht: {e}")
    
    def connect(self) -> bool:
        """
        Verbindet mit dem MQTT-Broker.
        
        Rückgabewert:
        bool: True bei Erfolg, False bei Fehler
        """
        mqtt_config = self.config.get("mqtt", {})
        
        try:
            self.client.connect(
                mqtt_config.get("broker", "localhost"),
                mqtt_config.get("port", 1883),
                mqtt_config.get("keepalive", 60)
            )
            return True
        except Exception as e:
            self.logger.error(f"MQTT Verbindung fehlgeschlagen: {e}")
            return False
    
    def loop(self, timeout: float = 1.0) -> None:
        """
        Führt einen MQTT-Loop-Schritt aus.
        
        Parameter:
        timeout (float): Timeout in Sekunden
        """
        self.client.loop(timeout=timeout)
    
    def disconnect(self) -> None:
        """Trennt die MQTT-Verbindung."""
        try:
            if self.client:
                self.client.disconnect()
                self.client.loop_stop()
                self.logger.info("MQTT-Verbindung getrennt")
        except Exception as e:
            self.logger.debug(f"Fehler beim Trennen der MQTT-Verbindung: {e}")
    
    @staticmethod
    def extract_device_name(topic: str) -> str:
        """
        Extrahiert den Device-Namen aus einem MQTT-Topic.
        
        Parameter:
        topic (str): Das MQTT-Topic
        
        Rückgabewert:
        str: Der Device-Name oder "unknown"
        """
        try:
            topic_parts = topic.split('/')
            # Format: application/{app_id}/device/{device_id}/event/up
            if len(topic_parts) >= 4:
                return topic_parts[3]
            else:
                return "unknown"
        except Exception:
            return "unknown"
