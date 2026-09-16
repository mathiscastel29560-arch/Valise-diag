"""Verrou par code PIN au démarrage — un simple filtre d'accès physique à
l'appareil, pas une protection contre un attaquant réseau. Le PIN est salé
avant hachage pour éviter un lookup dans une table précalculée triviale."""
from __future__ import annotations

import getpass
import hashlib
import secrets
import time

from .theme import CYAN, RED, RESET


def generer_sel() -> str:
    return secrets.token_hex(16)


def hash_pin(pin: str, sel: str) -> str:
    return hashlib.sha256((sel + pin).encode()).hexdigest()


def pin_valide(pin: str, sel: str, hash_attendu: str) -> bool:
    return hash_pin(pin, sel) == hash_attendu


def demander_pin(sel: str, hash_attendu: str, tentatives: int = 3, delai_blocage_s: float = 10.0) -> None:
    """Bloque tant que le bon PIN n'est pas saisi (avec un délai de pénalité entre
    chaque série de tentatives). Prévu pour être appelé une seule fois au démarrage."""
    while True:
        essais = tentatives
        while essais > 0:
            saisie = getpass.getpass(CYAN + "Code PIN requis : " + RESET)
            if pin_valide(saisie, sel, hash_attendu):
                return
            essais -= 1
            print(RED + f"Code incorrect. Tentatives restantes : {essais}" + RESET)
        print(RED + f"Trop de tentatives. Nouvelle chance dans {int(delai_blocage_s)}s..." + RESET)
        time.sleep(delai_blocage_s)
