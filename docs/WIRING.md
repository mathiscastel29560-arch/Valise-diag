# Câblage matériel

## Adaptateur OBD

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
