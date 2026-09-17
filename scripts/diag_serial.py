#!/usr/bin/env python3
"""Diagnostic bas niveau de l'adaptateur ELM327, sans passer par l'appli.

Envoie quelques commandes AT brutes et affiche les réponses telles quelles :
utile pour savoir si le blocage vient de l'adaptateur lui-même (ATZ ne
répond rien/du charabia -> mauvais port/débit/câble) ou du véhicule (0100
répond "NO DATA"/"UNABLE TO CONNECT" -> la voiture ne dialogue pas, même si
l'adaptateur va bien).

La même vérification est aussi disponible dans le menu (Diagnostic >
Diagnostic bas niveau adaptateur) une fois que le code est à jour sur le
Pi — ce script existe pour pouvoir la lancer sans même avoir fait
`git pull` au préalable.

Usage :
    python3 scripts/diag_serial.py [port] [baudrate]

Par défaut : /dev/ttyUSB0 à 38400 bauds.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from valise_diag.elm327 import diagnostiquer_port  # noqa: E402

port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
baudrate = int(sys.argv[2]) if len(sys.argv) > 2 else 38400

print(f"Port : {port}  Baudrate : {baudrate}")
resultat = diagnostiquer_port(port, baudrate)

if resultat.erreur_ouverture:
    print(f"Impossible d'ouvrir le port : {resultat.erreur_ouverture}")
    sys.exit(1)

print(f"ATZ   -> {resultat.reponse_atz!r}")
print(f"ATSP0 -> {resultat.reponse_atsp0!r}")
print(f"0100  -> {resultat.reponse_0100!r}")
print()
if not resultat.adaptateur_repond:
    print("-> L'adaptateur ne répond pas : problème port/débit/câble, pas la voiture.")
elif not resultat.vehicule_repond:
    print("-> Adaptateur OK, mais le véhicule ne répond pas (contact mis ? câble bien enfoncé ?).")
else:
    print("-> Adaptateur et véhicule répondent correctement.")
