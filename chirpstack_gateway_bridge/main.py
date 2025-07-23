"""
Main script for ChirpStack MQTT to UART Bridge.
"""

import sys
import json
import time
import logging
import signal
import threading
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
        
        try:
            # Log the raw payload
            logger.debug(f"Raw payload received: {payload}")
            
            # Extract device name
            device_name = MQTTHandler.extract_device_name(topic)
            logger.info(f"Device Name: {device_name}")
            
            # Parse JSON
            json_data = json.loads(payload)
            logger.debug(f"Parsed JSON data: {json.dumps(json_data, indent=2)}")
            
            # Decode payload
            decoded_payload = message_processor.decode_payload(json_data)
            if not decoded_payload:
                logger.error("Failed to decode payload")
                stats_manager.increment_errors()
                return
                
            # Validate payload
            if not message_processor.validate_payload(decoded_payload):
                logger.error("Payload validation failed")
                stats_manager.increment_errors()
                return
                
            # Create UART message
            uart_message = message_processor.create_uart_message(device_name, decoded_payload)
            if not uart_message:
                logger.error("Failed to create UART message")
                stats_manager.increment_errors()
                return
                
            # Send to UART
            if uart_comm.send(uart_message):
                stats_manager.increment_sent()
                logger.info(f"Successfully sent message for device {device_name}")
            else:
                stats_manager.increment_errors()
                logger.error("Failed to send message to UART")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"Invalid payload: {payload}")
            stats_manager.increment_errors()
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.exception("Full traceback:")
            stats_manager.increment_errors()

    mqtt_handler = MQTTHandler(config, logger, process_message)

    # Connect to MQTT
    if not mqtt_handler.connect():
        logger.error("Unable to connect to MQTT Broker")
        return

    # Setup for periodic statistics
    last_stats_time = time.time()
    stats_interval = config.get("system", {}).get("stats_interval", 300)
    
    # Setup signal handlers for graceful shutdown
    shutdown_event = threading.Event()
    
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("ChirpStack MQTT to UART Bridge started successfully")
    
    try:
        while not shutdown_event.is_set():
            mqtt_handler.loop(timeout=1.0)
            
            # Print statistics periodically
            current_time = time.time()
            if current_time - last_stats_time > stats_interval:
                stats_manager.print_stats()
                last_stats_time = current_time
                
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        logger.info("Shutting down...")
        mqtt_handler.disconnect()
        uart_comm.close()
        stats_manager.print_stats()  # Final statistics

if __name__ == "__main__":
    # Use the first command line argument as the config file name if available
    config_file = sys.argv[1] if len(sys.argv) >= 2 else "config.json"
    main(config_file)
