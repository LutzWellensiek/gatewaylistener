"""
Main script for ChirpStack MQTT to UART Bridge.
"""

import sys
import logging
from chirpstack_mqtt_to_uart import (
    load_config, setup_logging, UARTCommunicator,
    MQTTHandler, MessageProcessor, StatsManager
)

def main(config_file="config.json"):
    """Main entry point for the ChirpStack MQTT to UART Bridge."""
    # Load configuration
    config = load_config(config_file)
    logger = setup_logging(config)
    
    # Initialize components
    stats_manager = StatsManager(logger)
    uart_comm = UARTCommunicator(config, logger)
    message_processor = MessageProcessor(config, logger)
    
    def process_message(topic, payload):
        """Callback to process incoming MQTT messages."""
        stats_manager.increment_received()
        device_name = MQTTHandler.extract_device_name(topic)
        json_data = json.loads(payload)
        decoded_payload = message_processor.decode_payload(json_data)
        if decoded_payload and message_processor.validate_payload(decoded_payload):
            uart_message = message_processor.create_uart_message(device_name, decoded_payload)
            if uart_message and uart_comm.send(uart_message):
                stats_manager.increment_sent()
            else:
                stats_manager.increment_errors()

    mqtt_handler = MQTTHandler(config, logger, process_message)

    # Connect to MQTT
    if not mqtt_handler.connect():
        logger.error("Unable to connect to MQTT Broker")
        return

    try:
        while True:
            mqtt_handler.loop()
            stats_manager.print_stats()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        mqtt_handler.disconnect()
        uart_comm.close()

if __name__ == "__main__":
    # Use the first command line argument as the config file name if available
    config_file = sys.argv[1] if len(sys.argv) >= 2 else "config.json"
    main(config_file)
