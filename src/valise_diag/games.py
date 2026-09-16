"""Petits jeux pour patienter pendant un diagnostic."""
from __future__ import annotations

import curses
import random
import time
from typing import Optional

_MOTS_PENDU = ["MOTEUR", "CAPTEUR", "INJECTEUR", "ALLUMAGE", "EMBRAYAGE", "TURBOCOMPRESSEUR", "RADIATEUR"]

_COMBINAISONS_MORPION = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)


def jouer_pendu() -> None:
    mot = random.choice(_MOTS_PENDU)
    lettres_trouvees: set = set()
    essais_restants = 8
    while essais_restants > 0:
        affichage = " ".join(l if l in lettres_trouvees else "_" for l in mot)
        print(f"\n{affichage}   (essais restants : {essais_restants})")
        if "_" not in affichage:
            print("Gagné !")
            return
        lettre = input("Proposer une lettre : ").strip().upper()
        if len(lettre) != 1 or not lettre.isalpha():
            print("Entrez une seule lettre.")
            continue
        if lettre in lettres_trouvees:
            print("Déjà proposée.")
            continue
        lettres_trouvees.add(lettre)
        if lettre not in mot:
            essais_restants -= 1
    print(f"Perdu. Le mot était : {mot}")


def jouer_morpion() -> None:
    plateau = [" "] * 9
    joueur_courant = "X"

    def afficher() -> None:
        lignes = [" | ".join(plateau[i:i + 3]) for i in (0, 3, 6)]
        print("\n" + "\n---------\n".join(lignes) + "\n")

    def gagnant() -> Optional[str]:
        for a, b, c in _COMBINAISONS_MORPION:
            if plateau[a] != " " and plateau[a] == plateau[b] == plateau[c]:
                return plateau[a]
        return None

    afficher()
    for _ in range(9):
        case = input(f"Joueur {joueur_courant}, choisissez une case (1-9) : ").strip()
        if not case.isdigit() or not (1 <= int(case) <= 9) or plateau[int(case) - 1] != " ":
            print("Coup invalide.")
            continue
        plateau[int(case) - 1] = joueur_courant
        afficher()
        if gagnant():
            print(f"Le joueur {joueur_courant} gagne !")
            return
        joueur_courant = "O" if joueur_courant == "X" else "X"
    print("Match nul.")


def jouer_plus_ou_moins() -> None:
    nombre_secret = random.randint(1, 100)
    essais = 0
    print("\nJe pense à un nombre entre 1 et 100.")
    while True:
        essais += 1
        try:
            proposition = int(input("Votre proposition : ").strip())
        except ValueError:
            print("Entrez un nombre.")
            essais -= 1
            continue
        if proposition < nombre_secret:
            print("Plus grand !")
        elif proposition > nombre_secret:
            print("Plus petit !")
        else:
            print(f"Gagné en {essais} essai(s) !")
            return


def _boucle_serpent(stdscr) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(120)
    hauteur, largeur = stdscr.getmaxyx()
    fenetre = curses.newwin(hauteur, largeur, 0, 0)
    fenetre.keypad(True)

    serpent = [[hauteur // 2, largeur // 4], [hauteur // 2, largeur // 4 - 1], [hauteur // 2, largeur // 4 - 2]]
    nourriture = [hauteur // 2, largeur // 2]
    fenetre.addch(nourriture[0], nourriture[1], ord("@"))

    direction = curses.KEY_RIGHT
    score = 0

    while True:
        fenetre.border(0)
        fenetre.addstr(0, 2, f" SERPENT - q pour quitter | score: {score} ")
        touche = fenetre.getch()
        direction = touche if touche != -1 else direction
        if direction == ord("q"):
            break

        y, x = serpent[0]
        if direction == curses.KEY_DOWN:
            y += 1
        elif direction == curses.KEY_UP:
            y -= 1
        elif direction == curses.KEY_LEFT:
            x -= 1
        elif direction == curses.KEY_RIGHT:
            x += 1
        serpent.insert(0, [y, x])

        if [y, x] == nourriture:
            score += 1
            nourriture = None
            while nourriture is None:
                candidat = [random.randint(1, hauteur - 2), random.randint(1, largeur - 2)]
                if candidat not in serpent:
                    nourriture = candidat
            fenetre.addch(nourriture[0], nourriture[1], ord("@"))
        else:
            queue = serpent.pop()
            fenetre.addch(queue[0], queue[1], ord(" "))

        if y in (0, hauteur - 1) or x in (0, largeur - 1) or serpent[0] in serpent[1:]:
            break
        fenetre.addch(serpent[0][0], serpent[0][1], ord("#"))

    fenetre.addstr(hauteur // 2, max(largeur // 2 - 6, 0), f" GAME OVER ({score}) ")
    fenetre.refresh()
    time.sleep(2)


def jouer_serpent() -> None:
    try:
        curses.wrapper(_boucle_serpent)
    except curses.error:
        print("Le jeu nécessite un terminal plus grand ou n'est pas pris en charge ici.")
