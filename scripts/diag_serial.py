#!/usr/bin/env python3
"""Diagnostic bas niveau de l'adaptateur ELM327, sans passer par l'appli.

Envoie quelques commandes AT brutes et affiche les réponses telles quelles :
utile pour savoir si le blocage vient de l'adaptateur lui-même (ATZ ne
répond rien/du charabia -> mauvais port/débit/câble) ou du véhicule (0100
répond "NO DATA"/"UNABLE TO CONNECT" -> la voiture ne dialogue pas, même si
l'adaptateur va bien).

Usage :
    python3 scripts/diag_serial.py [port] [baudrate]

Par défaut : /dev/ttyUSB0 à 38400 bauds.
"""
import sys
import time

import serial

port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
baudrate = int(sys.argv[2]) if len(sys.argv) > 2 else 38400


def envoyer(ser: serial.Serial, commande: str, attente_s: float) -> None:
    ser.write((commande + "\r").encode())
    time.sleep(attente_s)
    reponse = ser.read(500)
    print(f"{commande} -> {reponse!r}")


print(f"Port : {port}  Baudrate : {baudrate}")
try:
    ser = serial.Serial(port, baudrate, timeout=2)
except Exception as exc:
    print(f"Impossible d'ouvrir le port : {exc}")
    sys.exit(1)

envoyer(ser, "ATZ", 1.0)
envoyer(ser, "ATSP0", 0.5)
envoyer(ser, "0100", 2.0)
ser.close()

print()
print("ATZ vide/charabia      -> problème adaptateur/câble/débit (pas la voiture)")
print("0100 = NO DATA / UNABLE TO CONNECT -> adaptateur OK, la voiture ne répond pas")
print("0100 = suite d'octets hexa          -> tout va bien à ce niveau")
