# Valise de diagnostic OBD/UDS — Raspberry Pi

Boîtier de diagnostic automobile basé sur un Raspberry Pi Zero et un
adaptateur OBD-II (ELM327/STN11xx), permettant de :

- lire et effacer les codes défauts (DTC) et les valeurs temps réel standard
  (régime moteur, vitesse, température...) via OBD-II (modes 01/03/04/09) ;
- exécuter des **tests actionneurs** (électrovannes, relais...) via le
  service UDS `InputOutputControlByIdentifier` (0x2F) ;
- **lire/écrire des paramètres ECU** avancés via `ReadDataByIdentifier` (0x22)
  / `WriteDataByIdentifier` (0x2E).

**⚠️ Lisez [`docs/SECURITE.md`](docs/SECURITE.md) avant toute utilisation sur
un véhicule réel.** Ce projet n'embarque volontairement aucune base de
données d'identifiants constructeur ni aucun algorithme de déverrouillage
`SecurityAccess` — vous devez fournir ces informations vous-même, à partir
d'une documentation que vous détenez légitimement, dans
`config/vehicle_profile.yaml`.

## Matériel

- Raspberry Pi Zero / Zero W / Zero 2 W
- Adaptateur ELM327 (USB) ou module ELM327/STN11xx en UART TTL
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
  elm327.py      # driver série bas niveau (commandes AT d'un ELM327 réel)
  simulator.py   # adaptateur simulé pour --simulate et les tests unitaires
  uds.py         # client UDS (ISO 14229) générique : sessions, sécurité, I/O, routines
  dtc.py         # OBD-II standard (DTC, PIDs temps réel) via python-obd
  safety.py      # garde-fous obligatoires avant toute action
  actuators.py   # tests actionneurs (UDS 0x2F), retour de contrôle à l'ECU garanti
  parameters.py  # lecture/écriture de paramètres ECU (UDS 0x22/0x2E) avec vérification
  config.py      # chargement de la config app + du profil véhicule (YAML)
  cli.py         # menu interactif
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
