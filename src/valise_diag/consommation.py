"""Consommation instantanée (L/100km), calculée à partir de deux PID
standard déjà utilisés ailleurs dans la valise (FUEL_RATE, SPEED) — pas un
capteur direct, juste de l'arithmétique sur des valeurs réelles :
L/100km = débit horaire (L/h) / vitesse (km/h) * 100.
"""
from __future__ import annotations

import sys
import termios
import time
import tty
from typing import Optional

from . import effects
from .dtc import valeur_numerique
from .theme import CYAN, GREEN, MAGENTA, RESET, YELLOW, afficher_bloc_centre, boite_titre

INTERVALLE_RAFRAICHISSEMENT_S = 1.0


def calculer_l_100km(debit_l_h: Optional[float], vitesse_kmh: Optional[float]) -> Optional[float]:
    """None si une valeur manque ou si le véhicule est à l'arrêt (vitesse
    nulle) — la formule diviserait par zéro, et "consommation instantanée"
    n'a pas de sens à l'arrêt (ralenti) de toute façon."""
    if debit_l_h is None or vitesse_kmh is None or vitesse_kmh <= 0:
        return None
    return debit_l_h / vitesse_kmh * 100


def _lire(obd2, commande: str) -> Optional[float]:
    try:
        return valeur_numerique(obd2.live_value(commande))
    except Exception:  # noqa: BLE001 - matériel externe, une lecture ratée ne doit pas interrompre l'affichage
        return None


def boucle_consommation(obd2, intervalle_s: float = INTERVALLE_RAFRAICHISSEMENT_S) -> None:
    fd = sys.stdin.fileno()
    reglages = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    try:
        while True:
            if effects.touche_en_attente():
                return

            debit = _lire(obd2, "FUEL_RATE")
            vitesse = _lire(obd2, "SPEED")
            conso = calculer_l_100km(debit, vitesse)

            lignes = boite_titre("CONSOMMATION INSTANTANEE", MAGENTA, CYAN) + [""]
            lignes.append(f"Débit carburant      : {debit:.2f} L/h" if debit is not None else "Débit carburant      : non disponible")
            lignes.append(f"Vitesse               : {vitesse:.0f} km/h" if vitesse is not None else "Vitesse               : non disponible")
            lignes.append("")
            if conso is not None:
                lignes.append(GREEN + f"Consommation instantanée : {conso:.1f} L/100km" + RESET)
            elif vitesse is not None and vitesse <= 0:
                lignes.append(YELLOW + "Véhicule à l'arrêt — pas de consommation instantanée pertinente." + RESET)
            else:
                lignes.append(YELLOW + "Non disponible (débit ou vitesse non fourni par le véhicule)." + RESET)
            lignes.append("")
            lignes.append(YELLOW + "Appuyez sur une touche pour revenir au menu." + RESET)
            afficher_bloc_centre(lignes)
            time.sleep(intervalle_s)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, reglages)
