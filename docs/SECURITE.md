# Sécurité et cadre légal

Ce projet permet d'envoyer des commandes UDS/OBD qui peuvent **activer des
actionneurs physiques** (électrovannes, relais, moteurs pas à pas...) et
**modifier des paramètres stockés dans l'ECU**. Une mauvaise utilisation peut :

- endommager des actionneurs ou le moteur ;
- déclencher des codes défauts, un mode dégradé, voire immobiliser le véhicule ;
- rendre le véhicule non conforme aux normes anti-pollution si des paramètres
  liés aux émissions sont modifiés — **c'est illégal dans la plupart des pays**
  et peut invalider le contrôle technique et/ou l'assurance.

## Règles à respecter

1. **N'utilisez ce logiciel que sur un véhicule que vous possédez, ou que vous
   êtes explicitement autorisé à diagnostiquer/réparer.**
2. Ne renseignez jamais un identifiant (`did`, `control_parameter`, plage de
   valeurs...) dans `vehicle_profile.yaml` sans une source fiable (manuel
   d'atelier constructeur, documentation technique officielle). Ce dépôt ne
   fournit volontairement aucune base de données propriétaire ni aucun
   algorithme de déverrouillage de sécurité ECU (`SecurityAccess`) : c'est à
   vous de fournir une fonction `compute_key` uniquement si vous détenez
   légitimement cet algorithme pour le véhicule concerné.
3. **Tests actionneurs** : véhicule à l'arrêt, contact mis selon le besoin du
   test, frein à main serré, roues motrices surélevées si l'actionneur testé
   peut faire bouger le véhicule, personne à proximité des pièces mobiles
   (courroies, ventilateur, pales...).
4. **Écriture de paramètres moteur** : commencez toujours par une lecture pour
   connaître la valeur d'origine, ne sortez jamais des bornes `min_value` /
   `max_value` définies dans le profil, et gardez un moyen de revenir en
   arrière (valeur d'origine notée, ou réinitialisation usine de l'ECU).
5. Débranchez l'adaptateur OBD avant de conduire le véhicule.
6. Ne désactivez jamais les confirmations (`require_confirmation: false`) sur
   un véhicule réel — ce réglage n'existe que pour les tests en mode
   `--simulate`.
7. En cas de doute sur un identifiant ou un comportement, arrêtez-vous et
   vérifiez plutôt que d'essayer "pour voir".
8. **Interface KKL (câble K-line) : la vitesse du véhicule n'est PAS
   surveillée automatiquement**, contrairement à l'interface OBD2 (qui la lit
   en direct). Le logiciel affiche un avertissement avant chaque test
   actionneur / écriture de paramètre sur cette interface, mais c'est à vous
   de vérifier que le véhicule est à l'arrêt avant de confirmer.
9. Sur l'interface KKL, les codes défauts sont affichés en **hexadécimal
   brut, non décodé** (le décodage précis varie par ECU/constructeur et n'est
   pas implémenté) : recoupez-les avec une documentation fiable avant d'agir.

Ce logiciel est fourni sans garantie. Vous êtes seul responsable de son usage.

## Scanner réseau (onglet Internet)

Le scanner réseau (`netscan.py`, basé sur `nmap`) est un outil de test
d'intrusion classique — légitime pour un professionnel de la cybersécurité,
mais strictement encadré par la loi :

- **N'utilisez-le que sur des réseaux/hôtes que vous êtes explicitement
  autorisé à tester** : votre propre réseau, un engagement de pentest couvert
  par une autorisation écrite, un CTF...
- En France, scanner un système sans autorisation relève de l'article 323-1
  du code pénal (accès ou maintien frauduleux dans un système de traitement
  automatisé de données) — des dispositions équivalentes existent dans la
  plupart des juridictions.
- Un scan « complet » (tous les ports) ou répété peut être détecté et
  interprété comme une attaque par les outils de détection du réseau ciblé,
  même sur un réseau que vous administrez : prévenez les autres personnes
  concernées si le réseau est partagé.
- Les rapports de scan (`config/scans/`) peuvent contenir des informations
  sensibles sur des systèmes tiers : ce dossier est exclu du dépôt Git
  (`.gitignore`), ne le publiez pas.
