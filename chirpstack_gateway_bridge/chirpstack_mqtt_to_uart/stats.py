"""Statistics module for ChirpStack MQTT to UART Bridge."""

import time
import logging
from typing import Dict, Any


class StatsManager:
    """Manages statistics and performance monitoring."""

    def __init__(self, logger: logging.Logger):
        """
        Initialisiert den Stats Manager.

        Parameter:
        logger (logging.Logger): Der Logger für Ausgaben
        """
        self.logger = logger
        self.stats = {
            'messages_received': 0,
            'messages_sent': 0,
            'errors': 0,
            'last_message_time': None,
            'start_time': time.time()
        }

    def increment_received(self) -> None:
        """Erhöht den Zähler für empfangene Nachrichten."""
        self.stats['messages_received'] += 1
        self.stats['last_message_time'] = time.time()

    def increment_sent(self) -> None:
        """Erhöht den Zähler für gesendete Nachrichten."""
        self.stats['messages_sent'] += 1

    def increment_errors(self) -> None:
        """Erhöht den Fehlerzähler."""
        self.stats['errors'] += 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Gibt die aktuellen Statistiken zurück.

        Rückgabewert:
        dict: Die aktuellen Statistiken
        """
        return self.stats.copy()

    def print_stats(self) -> None:
        """Gibt die erweiterten Statistiken aus."""
        uptime = time.time() - self.stats['start_time']
        uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime))

        self.logger.info(
            f"Statistiken - Uptime: {uptime_str}, "
            f"Empfangen: {self.stats['messages_received']}, "
            f"Gesendet: {self.stats['messages_sent']}, "
            f"Fehler: {self.stats['errors']}"
        )

    def reset(self) -> None:
        """Setzt die Statistiken zurück."""
        self.stats = {
            'messages_received': 0,
            'messages_sent': 0,
            'errors': 0,
            'last_message_time': None,
            'start_time': time.time()
        }
