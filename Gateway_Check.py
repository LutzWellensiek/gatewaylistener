import subprocess
import socket
import time
import threading
from paho.mqtt import client as mqtt_client

# Dienste, die geprüft werden
services = [
    "chirpstack-gateway-bridge",
    "chirpstack-network-server",
    "chirpstack-application-server",
    "mosquitto"
]

# MQTT-Einstellungen
broker = 'localhost'
port = 1883
topic = "application/+/device/+/event/up"
client_id = f'check-script-{int(time.time())}'

def check_service_status(service):
    try:
        output = subprocess.check_output(["systemctl", "is-active", service])
        status = output.decode().strip()
        print(f"[OK] Service '{service}' ist aktiv.")
        return status == "active"
    except subprocess.CalledProcessError:
        print(f"[FEHLER] Service '{service}' ist NICHT aktiv.")
        return False

def check_port(host, port, udp=False):
    sock_type = socket.SOCK_DGRAM if udp else socket.SOCK_STREAM
    with socket.socket(socket.AF_INET, sock_type) as sock:
        sock.settimeout(2)
        try:
            if udp:
                sock.sendto(b"ping", (host, port))
                print(f"[OK] UDP-Port {port} scheint erreichbar.")
                return True
            else:
                sock.connect((host, port))
                print(f"[OK] TCP-Port {port} (MQTT) ist offen.")
                return True
        except Exception as e:
            print(f"[FEHLER] Port {port} nicht erreichbar: {e}")
            return False

def mqtt_test():
    def on_message(client, userdata, msg):
        print(f"[OK] MQTT Nachricht empfangen: {msg.topic}")
        client.disconnect()

    client = mqtt_client.Client(client_id)
    client.on_message = on_message
    try:
        client.connect(broker, port)
        client.subscribe(topic)
        print(f"[INFO] Warte auf MQTT-Nachricht (Timeout 10s) …")
        client.loop_start()
        time.sleep(10)
        client.loop_stop()
    except Exception as e:
        print(f"[FEHLER] MQTT-Verbindung fehlgeschlagen: {e}")

def main():
    print("=== LoRaWAN Systemcheck auf Raspberry Pi ===\n")
    
    print("1. Prüfe Dienste:")
    for service in services:
        check_service_status(service)

    print("\n2. Prüfe Ports:")
    check_port("localhost", 1700, udp=True)  # Semtech UDP
    check_port("localhost", 1883)            # MQTT Broker

    print("\n3. Teste MQTT Empfang:")
    mqtt_test()

if __name__ == "__main__":
    main()
