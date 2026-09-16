# Valise de diagnostic OBD/UDS — Raspberry Pi

Boîtier de diagnostic automobile basé sur un Raspberry Pi Zero, avec **deux
lecteurs interchangeables** :

- **OBD2** : adaptateur ELM327/STN11xx générique (CAN), pour les véhicules
  récents, tous constructeurs.
- **KKL** : câble K-line type "VAG-COM 409.1", pour les ECU VAG (VW/Audi/Seat/
  Skoda) en KWP2000 ou en KW1281 (protocole historique par blocs) sur les
  véhicules pré-CAN.

Basculez entre les deux avec `interface: obd2|kkl` dans `config/app.yaml`,
`--interface obd2|kkl` en ligne de commande, ou l'onglet **Paramètres** du
menu.

Fonctions (identiques quelle que soit l'interface, quand le profil véhicule
la couvre) :

- lire et effacer les codes défauts (DTC) et les valeurs temps réel standard ;
- **tests actionneurs** (électrovannes, relais...) via
  `InputOutputControlByIdentifier` (UDS 0x2F sur CAN, KWP2000 0x30 sur K-line) ;
- **lecture/écriture de paramètres ECU** via `ReadDataByIdentifier`/
  `WriteDataByIdentifier` (0x22/0x2E en UDS, 0x21/0x3B en KWP2000).

Le menu est organisé en onglets : **Diagnostic**, **Programmation** (lecture/
écriture de paramètres + doc rapide sur le vocabulaire de codage),
**Internet** (statut réseau, Wi-Fi), **Paramètres** (réglages de
l'application) et **Jeux** (Pendu, Morpion, Plus ou moins) pour patienter
pendant un diagnostic. Un écran de démarrage s'affiche avant le menu.

**⚠️ Lisez [`docs/SECURITE.md`](docs/SECURITE.md) avant toute utilisation sur
un véhicule réel.** Ce projet n'embarque volontairement aucune base de
données d'identifiants constructeur, aucun numéro de bloc KW1281 vérifié, ni
aucun algorithme de déverrouillage `SecurityAccess` — vous devez fournir ces
informations vous-même, à partir d'une documentation que vous détenez
légitimement, dans `config/vehicle_profile.yaml`.

Limite connue : le mode `--simulate` ne couvre que l'interface OBD2 ; il n'y
a pas encore de simulateur K-line pour l'interface KKL. Les tests
actionneurs / écriture de paramètres ne sont pour l'instant câblés que pour
les protocoles `uds_can` et `kwp2000_kline` ; le protocole `kw1281` (ECU VAG
les plus anciens) ne couvre que la lecture/effacement des codes défauts en
hexadécimal brut.

## Matériel

- Raspberry Pi Zero / Zero W / Zero 2 W
- Adaptateur ELM327 (USB) et/ou câble KKL K-line (USB)
- Voir [`docs/WIRING.md`](docs/WIRING.md) pour le câblage et l'alimentation.

## Installation

```bash
git clone <ce dépôt>
cd valise-diag
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp config/vehicle_profile.example.yaml config/vehicle_profile.yaml
cp config/app.example.yaml config/app.yaml
```

Éditez ensuite `config/vehicle_profile.yaml` avec les identifiants réels de
votre véhicule (voir les commentaires dans le fichier).

## Utilisation

```bash
python3 -m valise_diag --config config/app.yaml
```

Mode simulation (aucun matériel requis, pratique pour découvrir le menu ou
développer) :

```bash
python3 -m valise_diag --config config/app.yaml --simulate
```

## Structure du projet

```
src/valise_diag/
  elm327.py      # driver série bas niveau, interface OBD2 (commandes AT d'un ELM327 réel)
  kkl.py         # driver série bas niveau, interface KKL (init 5-baud K-line)
  simulator.py   # adaptateur ELM327 simulé pour --simulate et les tests unitaires
  uds.py         # client UDS (ISO 14229) générique sur CAN : sessions, sécurité, I/O, routines
  kwp2000.py     # client KWP2000 (ISO 14230) sur K-line — même API que uds.py
  kwp1281.py     # client KW1281 (VAG, protocole par blocs) sur K-line
  transport.py   # choisit/construit le bon client selon l'interface + le profil véhicule
  dtc.py         # OBD-II standard (DTC, PIDs temps réel) via python-obd — interface OBD2 uniquement
  safety.py      # garde-fous obligatoires avant toute action
  actuators.py   # tests actionneurs, retour de contrôle à l'ECU garanti (UDS et KWP2000)
  parameters.py  # lecture/écriture de paramètres ECU avec vérification (UDS et KWP2000)
  config.py      # chargement/sauvegarde de la config app + du profil véhicule (YAML)
  boot.py        # écran de démarrage (œuvre ASCII + séquence de chargement)
  coding_doc.py  # doc rapide : vocabulaire de codage/programmation (onglet Programmation)
  netinfo.py     # statut réseau, liste et connexion Wi-Fi (onglet Internet)
  games.py       # Pendu, Morpion, Plus ou moins (onglet Jeux)
  cli.py         # menu interactif à onglets (Diagnostic / Programmation / Internet / Paramètres / Jeux)
tests/           # tests unitaires (encodage de trames, garde-fous) — sans matériel
config/          # exemples de configuration à copier/adapter
docs/            # câblage, sécurité
systemd/         # unité systemd optionnelle
```

## Tests

```bash
pip install -e ".[dev]"
pytest
```

## Licence

À définir par le dépôt propriétaire.
