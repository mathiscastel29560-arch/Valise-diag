"""Trois petits jeux texte pour patienter pendant un diagnostic."""
from __future__ import annotations

import random
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
