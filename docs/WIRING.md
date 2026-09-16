# Câblage matériel

## Deux lecteurs, une seule valise

Le logiciel bascule entre les deux via `interface: obd2|kkl` dans
`config/app.yaml` (ou `--interface` en ligne de commande / onglet
Paramètres). Ne branchez qu'un seul câble à la fois sur le port OBD-II du
véhicule.

## Interface OBD2 (ELM327/CAN)

Deux options :

1. **ELM327 USB** (recommandé pour débuter) : se branche directement sur le
   port USB du Raspberry Pi Zero (via un adaptateur micro-USB OTG). Le plus
   simple et le plus tolérant côté câblage.
2. **Module ELM327/STN11xx en UART TTL** : relié aux broches GPIO14 (TXD) /
   GPIO15 (RXD) du Pi. Plus compact, ne monopolise pas le seul port USB du Pi
   Zero, mais nécessite d'activer l'UART matériel :
   - `sudo raspi-config` → *Interface Options* → *Serial Port* → désactiver la
     console série sur ce port, activer le matériel UART.
   - Réglez `port: "/dev/serial0"` dans `config/app.yaml`.

Pour un usage sérieux de l'UDS (tests actionneurs, écriture de paramètres), un
adaptateur basé sur une puce **STN11xx** gère nettement mieux le CAN Auto
Formatting (`AT CAF1`) et le multi-frame ISO-TP que les clones ELM327 bas de
gamme, qui décrochent parfois sur les réponses longues.

## Interface KKL (câble K-line type VAG-COM 409.1)

Un câble KKL classique embarque une puce USB-série (FTDI/PL2303/CH340) reliée
à un transceiver K-line — pas de CAN, pas de fast-init : uniquement l'init
5-baud gérée par `kkl.py`. Branchez-le en USB sur le Pi (`port:
"/dev/ttyUSB0"` en général ; vérifiez avec `dmesg` après branchement, le nom
peut varier si les deux adaptateurs sont branchés en même temps).

Le débit de liaison après l'initialisation (`baudrate` dans `config/app.yaml`)
dépend de l'ECU : 10400 bauds est courant pour KWP2000, certains ECU KW1281
utilisent 9600. Si l'initialisation échoue (timeout), essayez l'autre valeur.

## Alimentation du Raspberry Pi Zero

Le connecteur OBD-II fournit du 12V (broche 16) et une masse (broches 4/5),
pas de 5V régulé. Ne branchez jamais directement le 12V sur le Pi. Utilisez
soit :

- un adaptateur secteur 12V→5V USB dédié automobile, câblé sur le connecteur
  OBD, ou
- une alimentation externe classique (batterie USB, secteur) pendant les
  phases de développement/tests, le Pi et l'adaptateur OBD étant alors deux
  éléments indépendants reliés uniquement par les lignes de données CAN et une
  masse commune.

## Connecteur OBD-II (broches utiles)

| Broche | Signal            |
|-------:|-------------------|
| 4      | Masse châssis     |
| 5      | Masse signal      |
| 6      | CAN High (J-2284) |
| 14     | CAN Low           |
| 16     | +12V batterie     |

## Avant de démarrer

Consultez [`SECURITE.md`](SECURITE.md) avant de connecter quoi que ce soit à
un véhicule.
