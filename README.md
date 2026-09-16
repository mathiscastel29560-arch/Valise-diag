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

Le menu se présente comme un tableau de bord (heure, IP, CPU/température/RAM/
disque/Wi-Fi, style cyberdeck) avec un écran de démarrage animé, organisé en
onglets :

- **Diagnostic** — codes défauts, lecture temps réel, tests actionneurs,
  identification ECU, historique des actions effectuées sur le véhicule.
- **Programmation** — lecture/écriture de paramètres ECU + doc rapide sur le
  vocabulaire de codage.
- **Internet** — statut réseau, Wi-Fi (liste/connexion/`nmtui`), ping, test de
  débit, navigateur texte (`w3m`).
- **Système** — outils Raspberry Pi (shell, console Python, éditeur, infos
  système, mise à jour) : distinct de Programmation, qui ne touche qu'au
  véhicule.
- **Paramètres** — tous les réglages : interface/port/profil véhicule,
  sécurité, apparence (titre, veille, police console), démarrage automatique,
  code PIN.
- **Jeux** — Pendu, Morpion, Plus ou moins, Serpent (`curses`).

Sur un vrai terminal, les touches sont prises en compte immédiatement (pas
besoin d'Entrée) et un écran de veille (matrix / citations / glitch) se
déclenche après une période d'inactivité configurable. Deux easter eggs sont
cachés dans le tableau de bord : tapez `serpent` ou `hack`. Sur une entrée non
interactive (script, pipe), le menu retombe automatiquement sur un mode
ligne par ligne classique.

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
votre véhicule (voir les commentaires dans le fichier). Pour un véhicule du
groupe VAG (VW/Audi/Seat/Skoda) sur interface KKL, partez plutôt de
`config/vehicle_profile.vag.example.yaml`, qui préremplit les adresses de
module standard et explique où trouver les vraies valeurs de codage
(wiki Ross-Tech).

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
  boot.py        # écran de démarrage (logo en reveal, scroll de logs, barre de progression)
  coding_doc.py  # doc rapide : vocabulaire de codage/programmation (onglet Programmation)
  netinfo.py     # statut réseau, Wi-Fi, ping, débit, navigation (onglet Internet)
  system_tools.py # shell/Python/éditeur, infos système, maj, police, autostart (onglet Système)
  system_status.py # lecture CPU/température/RAM/disque/Wi-Fi pour le tableau de bord
  pin_lock.py    # verrou par code PIN au démarrage (salé)
  history.py     # journal des actions de diagnostic (traçabilité)
  theme.py       # couleurs ANSI, centrage, boîtes — utilisés par tout le menu
  effects.py     # effets visuels cosmétiques (frappe, reveal, matrix, glitch)
  screensaver.py # écran de veille après inactivité (Paramètres > veille)
  easter_eggs.py # mise en scène cachée ("hack") — aucune action réelle
  games.py       # Pendu, Morpion, Plus ou moins, Serpent (onglet Jeux)
  cli.py         # tableau de bord + menu à onglets (Diagnostic/Programmation/Internet/Système/Paramètres/Jeux)
tests/           # tests unitaires (encodage de trames, garde-fous, PIN) — sans matériel
config/          # exemples de configuration à copier/adapter
docs/            # câblage, sécurité
systemd/         # démarrage automatique sur la console (autologin tty1 + .bashrc)
```

## Démarrage automatique

Le menu est un programme interactif (clavier, veille) : il ne se lance pas
comme un service systemd classique en tâche de fond, mais à la connexion sur
la console physique du Pi (tty1). Voir `systemd/getty-autologin-tty1.conf`
(connexion automatique) et `systemd/autostart.bashrc.snippet` (à coller dans
le `~/.bashrc` de l'utilisateur) — l'onglet Paramètres > "Démarrage
automatique" active/désactive ce mécanisme sans rien réinstaller.

## Tests

```bash
pip install -e ".[dev]"
pytest
```

## Licence

À définir par le dépôt propriétaire.
