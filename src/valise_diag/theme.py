"""Couleurs ANSI et petits helpers d'affichage (centrage, boîtes, écran) partagés
par le menu, l'écran de démarrage et la veille."""
from __future__ import annotations

import re
import shutil
import sys
from typing import Iterable

CYAN = "\033[96m"
MAGENTA = "\033[95m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def largeur_terminal() -> int:
    return shutil.get_terminal_size((80, 24)).columns


def hauteur_terminal() -> int:
    return shutil.get_terminal_size((80, 24)).lines


def largeur_visible(texte: str) -> int:
    """Longueur d'une chaîne une fois les codes couleur ANSI retirés."""
    return len(_ANSI_RE.sub("", texte))


def clear_screen() -> None:
    # Séquence ANSI directe : plus rapide que de relancer un sous-processus `clear`.
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def centrer_ligne(texte: str) -> str:
    pad = max((largeur_terminal() - largeur_visible(texte)) // 2, 0)
    return " " * pad + texte


def print_centre(texte: str, couleur: str = "") -> None:
    for ligne in texte.split("\n"):
        print(centrer_ligne(couleur + ligne + RESET if couleur else ligne))


def afficher_bloc_centre(lignes: Iterable[str]) -> None:
    lignes = list(lignes)
    marge_haut = max((hauteur_terminal() - len(lignes)) // 2, 0)
    sys.stdout.write("\n" * marge_haut)
    for ligne in lignes:
        print(centrer_ligne(ligne))


def construire_titre_boite(texte: str, largeur_interieure: int = 38) -> str:
    texte = texte.strip()[:largeur_interieure]
    pad_total = largeur_interieure - len(texte)
    gauche = pad_total // 2
    droite = pad_total - gauche
    return " " * gauche + texte + " " * droite


def boite_titre(titre: str, couleur_bordure: str = CYAN, couleur_texte: str = MAGENTA, largeur: int = 38) -> list:
    return [
        f"{couleur_bordure}{BOLD}+{'-' * largeur}+{RESET}",
        f"{couleur_bordure}{BOLD}|{RESET}{couleur_texte}{construire_titre_boite(titre, largeur)}{RESET}{couleur_bordure}{BOLD}|{RESET}",
        f"{couleur_bordure}{BOLD}+{'-' * largeur}+{RESET}",
    ]
