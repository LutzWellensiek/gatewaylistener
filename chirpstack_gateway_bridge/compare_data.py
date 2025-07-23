#!/usr/bin/env python3
"""
Vergleicht gesendete und empfangene Daten
"""

import base64

# Deine gesendeten Daten
sent_hex = "54 9C E3 3D 41 C6 90 75 43 44 00 00 00 00 50 00 00 00 00 53 1F E0 19 C2"
sent_bytes = bytes.fromhex(sent_hex.replace(" ", ""))

# Empfangene Base64-Daten aus verschiedenen Nachrichten
received_base64_samples = [
    "VKQQPkHQl3VDRAAAAABQAAAAAFMf4BnC",  # Erste Nachricht
    "VJzjPUGYk3VDRAAAAABQAAAAAFMf4BnC",  # Zweite Nachricht
    "VJzjPUFolnVDRAAAAABQAAAAAFMf4BnC",  # Dritte Nachricht
    "VJzjPUE2mXVDRAAAAABQAAAAAFMf4BnC",  # Vierte Nachricht
]

print("=== Datenvergleich ===\n")
print(f"Gesendete Daten (Hex): {sent_hex}")
print(f"Gesendete Daten (Bytes): {len(sent_bytes)} Bytes\n")

for i, b64_data in enumerate(received_base64_samples, 1):
    # Dekodiere Base64
    decoded_bytes = base64.b64decode(b64_data)
    decoded_hex = decoded_bytes.hex()
    
    print(f"Nachricht {i}:")
    print(f"  Base64: {b64_data}")
    print(f"  Hex: {' '.join([decoded_hex[j:j+2] for j in range(0, len(decoded_hex), 2)])}")
    print(f"  Bytes: {len(decoded_bytes)} Bytes")
    
    # Vergleiche mit gesendeten Daten
    if decoded_bytes == sent_bytes:
        print("  ✅ Identisch mit gesendeten Daten!")
    else:
        print("  ❌ Unterschiede gefunden:")
        for j, (sent_byte, recv_byte) in enumerate(zip(sent_bytes, decoded_bytes)):
            if sent_byte != recv_byte:
                print(f"    Position {j}: Gesendet 0x{sent_byte:02X}, Empfangen 0x{recv_byte:02X}")
    print()

# Analysiere die Struktur
print("\n=== Datenstruktur-Analyse ===")
if len(sent_bytes) >= 24:
    print("Die 24-Byte Payload scheint folgende Struktur zu haben:")
    print(f"Bytes 0-3:   {sent_hex[:11]}  (Float?)")
    print(f"Bytes 4-7:   {sent_hex[12:23]}  (Float?)")
    print(f"Bytes 8-11:  {sent_hex[24:35]}  (Float?)")
    print(f"Bytes 12-15: {sent_hex[36:47]}  (Nullen)")
    print(f"Bytes 16-19: {sent_hex[48:59]}  (0x50 = 80 dezimal)")
    print(f"Bytes 20-23: {sent_hex[60:71]}  (Konstante?)") 
