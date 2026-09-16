"""Couleurs ANSI et petits helpers d'affichage (centrage, boîtes, écran) partagés
par le menu, l'écran de démarrage et la veille."""
from __future__ import annotations

import re
import shutil
import sys
from typing import Iterable, Optional

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


def _centrer_avec_largeur(texte: str, largeur: int) -> str:
    pad = max((largeur - largeur_visible(texte)) // 2, 0)
    return " " * pad + texte


def centrer_ligne(texte: str) -> str:
    return _centrer_avec_largeur(texte, largeur_terminal())


def centrer_avec_couleur(texte: str, couleur: str = "", largeur: Optional[int] = None) -> str:
    """Centre (et colore) un texte, éventuellement multi-lignes, sans l'écrire.
    Permet d'assembler plusieurs blocs et de les envoyer en une seule
    écriture (voir effects.py)."""
    if largeur is None:
        largeur = largeur_terminal()
    lignes = [
        _centrer_avec_largeur(couleur + ligne + RESET if couleur else ligne, largeur)
        for ligne in texte.split("\n")
    ]
    return "\n".join(lignes)


def print_centre(texte: str, couleur: str = "") -> None:
    sys.stdout.write(centrer_avec_couleur(texte, couleur) + "\n")
    sys.stdout.flush()


def afficher_bloc_centre(lignes: Iterable[str], effacer: bool = True) -> None:
    """Dessine un bloc de lignes centré en une seule écriture (au lieu d'un
    print() par ligne) : sur un Pi Zero, notamment via une console série, ça
    évite une rafale d'appels système à chaque rafraîchissement de menu.
    """
    lignes = list(lignes)
    taille = shutil.get_terminal_size((80, 24))  # un seul appel pour largeur + hauteur
    marge_haut = max((taille.lines - len(lignes)) // 2, 0)
    parties = ["\033[2J\033[H"] if effacer else []
    parties.append("\n" * marge_haut)
    for ligne in lignes:
        parties.append(_centrer_avec_largeur(ligne, taille.columns))
        parties.append("\n")
    sys.stdout.write("".join(parties))
    sys.stdout.flush()


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
