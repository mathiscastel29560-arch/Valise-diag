"""Effets visuels purement cosmétiques : démarrage, veille. Rien ici ne touche
au véhicule — en cas de terminal trop petit ou de sortie non-interactive, ces
fonctions peuvent échouer sans risque, elles sont donc systématiquement
appelées depuis des contextes qui tolèrent l'échec."""
from __future__ import annotations

import random
import select
import sys
import time

from .theme import (
    BOLD,
    GREEN,
    RESET,
    clear_screen,
    hauteur_terminal,
    largeur_terminal,
    print_centre,
)

_SYMBOLES_GLITCH = "!@#$%^&*<>/\\|[]{}=+~01"
_CARACTERES_MATRIX = "01ABCDEFGHIJKLMNOPQRSTUVWXYZ$%#@&*+=<>?"


def touche_en_attente() -> str | None:
    """Lecture clavier non-bloquante (nécessite un terminal en mode cbreak)."""
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    if dr:
        return sys.stdin.read(1)
    return None


def effet_frappe(texte: str, couleur: str = GREEN, delai: float = 0.02) -> None:
    for char in texte:
        sys.stdout.write(couleur + char + RESET)
        sys.stdout.flush()
        time.sleep(delai)
    print()


def defilement_logs(lignes_possibles: list, duree: float = 1.8) -> None:
    from .theme import CYAN, YELLOW

    fin = time.time() + duree
    while time.time() < fin:
        ligne = random.choice(lignes_possibles)
        couleur = random.choice([GREEN, CYAN, YELLOW])
        print(couleur + "[  OK  ] " + RESET + ligne)
        time.sleep(0.04)


def decrypt_reveal_centre(texte_final: str, couleur: str, iterations: int = 10, delai: float = 0.045) -> None:
    lignes = texte_final.strip("\n").split("\n")

    for i in range(iterations):
        clear_screen()
        print("\n" * 2)
        for ligne in lignes:
            affichage = "".join(
                " " if char == " " else (char if random.random() < (i / iterations) else random.choice(_SYMBOLES_GLITCH))
                for char in ligne
            )
            print_centre(affichage, couleur)
        time.sleep(delai)

    clear_screen()
    print("\n" * 2)
    print_centre(texte_final, couleur + BOLD)


def barre_progression(duree: float = 1.5, largeur_barre: int = 36, couleur: str = "") -> None:
    largeur = largeur_terminal()
    for pct in range(0, 101, 4):
        rempli = int((pct / 100) * largeur_barre)
        barre = "#" * rempli + "-" * (largeur_barre - rempli)
        ligne = f"[{barre}] {pct}%"
        pad = max((largeur - len(ligne)) // 2, 0)
        sys.stdout.write("\r" + " " * pad + couleur + ligne + RESET)
        sys.stdout.flush()
        time.sleep(duree / 25)
    print("\n")


def effet_matrix(duree: float = 5.0) -> None:
    largeur = min(largeur_terminal(), 120)
    hauteur = max(hauteur_terminal() - 1, 10)
    colonnes = [random.randint(-hauteur, 0) for _ in range(largeur)]
    vitesses = [random.choice([1, 1, 2]) for _ in range(largeur)]

    fin = time.time() + duree
    clear_screen()
    while time.time() < fin:
        if touche_en_attente():
            return
        sys.stdout.write("\033[H")
        lignes = []
        for y in range(hauteur):
            ligne_chars = []
            for x in range(largeur):
                pos = colonnes[x]
                if y == pos:
                    ligne_chars.append(GREEN + BOLD + random.choice(_CARACTERES_MATRIX) + RESET)
                elif 0 <= pos - y <= 6:
                    ligne_chars.append(GREEN + random.choice(_CARACTERES_MATRIX) + RESET)
                else:
                    ligne_chars.append(" ")
            lignes.append("".join(ligne_chars))
        sys.stdout.write("\n".join(lignes))
        sys.stdout.flush()
        for x in range(largeur):
            colonnes[x] += vitesses[x]
            if colonnes[x] - 6 > hauteur and random.random() < 0.05:
                colonnes[x] = random.randint(-10, 0)
        time.sleep(0.06)


def galerie_citations(citations: list, couleur: str, duree: float = 3.5) -> None:
    citation = random.choice(citations)
    decrypt_reveal_centre(citation, couleur, iterations=8, delai=0.03)
    fin = time.time() + duree
    while time.time() < fin:
        if touche_en_attente():
            return
        time.sleep(0.05)


def glitch_flash(passes: int = 2) -> None:
    from .theme import RED, CYAN, MAGENTA

    largeur = largeur_terminal()
    hauteur = hauteur_terminal()
    for _ in range(passes):
        clear_screen()
        for _ in range(hauteur - 1):
            couleur = random.choice([RED, CYAN, MAGENTA, GREEN])
            print(couleur + "".join(random.choice(_SYMBOLES_GLITCH) for _ in range(largeur)) + RESET)
        time.sleep(0.05)
    clear_screen()
