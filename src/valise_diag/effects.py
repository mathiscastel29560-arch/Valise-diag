"""Effets visuels purement cosmétiques : démarrage, veille. Rien ici ne touche
au véhicule — en cas de terminal trop petit ou de sortie non-interactive, ces
fonctions peuvent échouer sans risque, elles sont donc systématiquement
appelées depuis des contextes qui tolèrent l'échec."""
from __future__ import annotations

import os
import random
import select
import sys
import time

from .theme import BOLD, GREEN, RESET, centrer_avec_couleur, clear_screen, hauteur_terminal, largeur_terminal

_SYMBOLES_GLITCH = "!@#$%^&*<>/\\|[]{}=+~01"
_CARACTERES_MATRIX = "01ABCDEFGHIJKLMNOPQRSTUVWXYZ$%#@&*+=<>?"


def touche_en_attente() -> str | None:
    """Lecture clavier non-bloquante (nécessite un terminal en mode cbreak).

    Lit directement sur le descripteur de fichier plutôt que via
    sys.stdin.read() : ce dernier bufferise en interne (TextIOWrapper), ce
    qui peut laisser un octet coincé dans ce buffer Python après un flush
    termios et voler la lecture suivante ailleurs dans l'appli."""
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    if dr:
        return os.read(sys.stdin.fileno(), 1).decode(errors="replace")
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
        seuil = i / iterations
        bloc = ["\n" * 2]
        for ligne in lignes:
            symboles = random.choices(_SYMBOLES_GLITCH, k=len(ligne))
            affichage = "".join(
                " " if char == " " else (char if random.random() < seuil else symbole)
                for char, symbole in zip(ligne, symboles)
            )
            bloc.append(centrer_avec_couleur(affichage, couleur))
        sys.stdout.write("\033[2J\033[H" + "\n".join(bloc) + "\n")
        sys.stdout.flush()
        time.sleep(delai)

    sys.stdout.write("\033[2J\033[H" + "\n" * 2 + centrer_avec_couleur(texte_final, couleur + BOLD) + "\n")
    sys.stdout.flush()


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


def effet_matrix(duree: float = 5.0, largeur_max: int = 80, fps: float = 11.0) -> bool:
    """"Pluie" façon Matrix. Deux optimisations pour rester fluide sur un Pi
    Zero (mono-cœur) : on ne calcule l'état que des ~7 cellules "actives" par
    colonne au lieu de balayer toute la hauteur (les autres restent des
    espaces), et chaque ligne regroupe ses caractères consécutifs de même
    style en un seul bloc de code couleur au lieu d'un par caractère — moins
    de travail Python, et surtout beaucoup moins d'octets à envoyer à la
    console à chaque image.

    Renvoie True si interrompu par une touche, False si la durée s'est
    écoulée normalement — l'appelant (screensaver.py) en a besoin : la touche
    est déjà consommée ici, il ne pourra pas la revoir lui-même.
    """
    largeur = min(largeur_terminal(), largeur_max)
    hauteur = max(hauteur_terminal() - 1, 10)
    colonnes = [random.randint(-hauteur, 0) for _ in range(largeur)]
    vitesses = [random.choice([1, 1, 2]) for _ in range(largeur)]
    delai = 1.0 / fps

    fin = time.time() + duree
    clear_screen()
    while time.time() < fin:
        if touche_en_attente():
            return True

        # 0 = traînée, 1 = tête, None = case vide. Ne remplit que les
        # cellules réellement visibles pour cette image.
        grille = [[None] * largeur for _ in range(hauteur)]
        for x in range(largeur):
            pos = colonnes[x]
            for y in range(max(pos - 6, 0), min(pos + 1, hauteur)):
                if 0 <= y < hauteur:
                    grille[y][x] = 1 if y == pos else 0

        lignes = [_ligne_matrix(grille[y], largeur) for y in range(hauteur)]
        sys.stdout.write("\033[H" + "\n".join(lignes))
        sys.stdout.flush()

        for x in range(largeur):
            colonnes[x] += vitesses[x]
            if colonnes[x] - 6 > hauteur and random.random() < 0.05:
                colonnes[x] = random.randint(-10, 0)
        time.sleep(delai)
    return False


def _ligne_matrix(etats: list, largeur: int) -> str:
    """Construit une ligne en regroupant les cases consécutives de même état
    (vide / traînée / tête) en un seul segment coloré, plutôt qu'un code
    ANSI par caractère."""
    parties = []
    x = 0
    while x < largeur:
        etat = etats[x]
        debut = x
        while x < largeur and etats[x] == etat:
            x += 1
        longueur = x - debut
        if etat is None:
            parties.append(" " * longueur)
        else:
            texte = "".join(random.choices(_CARACTERES_MATRIX, k=longueur))
            style = GREEN + BOLD if etat == 1 else GREEN
            parties.append(style + texte + RESET)
    return "".join(parties)


def galerie_citations(citations: list, couleur: str, duree: float = 3.5) -> bool:
    """Renvoie True si interrompu par une touche (voir effet_matrix)."""
    citation = random.choice(citations)
    decrypt_reveal_centre(citation, couleur, iterations=8, delai=0.03)
    fin = time.time() + duree
    while time.time() < fin:
        if touche_en_attente():
            return True
        time.sleep(0.05)
    return False


def glitch_flash(passes: int = 2, largeur_max: int = 80) -> bool:
    """Renvoie True si interrompu par une touche (voir effet_matrix)."""
    from .theme import RED, CYAN, MAGENTA

    largeur = min(largeur_terminal(), largeur_max)
    hauteur = hauteur_terminal()
    couleurs = [RED, CYAN, MAGENTA, GREEN]
    for _ in range(passes):
        if touche_en_attente():
            return True
        lignes = []
        for _ in range(hauteur - 1):
            couleur = random.choice(couleurs)
            texte = "".join(random.choices(_SYMBOLES_GLITCH, k=largeur))
            lignes.append(couleur + texte + RESET)
        sys.stdout.write("\033[2J\033[H" + "\n".join(lignes))
        sys.stdout.flush()
        time.sleep(0.05)
    clear_screen()
    return False
