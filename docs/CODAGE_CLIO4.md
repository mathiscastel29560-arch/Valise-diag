# Codage confort — Renault Clio 4 (X98) 1.5 dCi 90 (2012)

Ce document recense ce qui a été trouvé publiquement sur le codage confort
(UCH) pour une Clio 4 phase 1, et surtout **ce qui manque encore** avant de
pouvoir l'intégrer sans risque dans `config/vehicle_profile.yaml`.

## Pourquoi rien n'est encore câblé dans la valise

Aucun DID/bit trouvé ci-dessous n'a été confirmé sur un Clio 4 **phase 1
diesel de 2012-2015**. Toutes les confirmations concrètes trouvées viennent
de modèles 2016+ (phase 2, ou phase 1 tardif avec une version logicielle UCH
différente — "SW14", "SW15_2"...). Un post d'un même fil mentionne un Clio de
2015 en version logicielle antérieure ("SW8.5") où l'auteur a été
explicitement déconseillé de toucher aux réglages phares : le nom exact du
paramètre et sa position dans l'UCH changent avec la version logicielle, pas
seulement avec le modèle. Mettre une valeur "probable" dans le profil serait
exactement le genre de donnée inventée que ce projet refuse de fabriquer
(voir `config/vehicle_profile.example.yaml`).

## Ce qui a été trouvé (pistes à vérifier vous-même via ddt4all)

| Fonction | ECU (selon les sources) | Paramètre (nom rapporté) | Année du véhicule source | Risque réglementaire |
|---|---|---|---|---|
| Horloge/température permanente à l'écran | non précisé | non précisé | Clio 4 2016 | Aucun |
| Vitesse km/h → mph | non précisé | non précisé | Clio 4 2016 | Aucun |
| Désactivation de l'assistance au démarrage en côte (HSA) | ABS/ESC | non précisé | Clio 4 2016 | Aucun (confort/assistance, pas homologation) |
| Phares via télécommande / clé | UPC-EMM | non précisé | Clio 4 2016 | Aucun |
| Follow-me-home (phares temporisés à l'extinction) | UPC-EMM | non précisé | Clio 4 2016 | Aucun |
| Fermeture automatique des vitres en roulant | non précisé | non précisé | Clio 4 2016 (rapporté "ne fonctionne pas") | Aucun |
| Feux de jour toujours allumés + Welcome/Goodbye lights | EMM EDISON DDT2000 SW15_2 | `NSX Singlebulb DRL TAIL CF` (0-3, 3=actif) | Clio 4 2016 (halogène + DRL calandre) | **Oui — cf. ci-dessous** |

**Sources** :
- [DDT4ALL Modifications — ClioSport.net](https://cliosport.net/threads/ddt4all-modifications.826511/)
- [Welcome/Goodbye lights — issue #250, cedricp/ddt4all](https://github.com/cedricp/ddt4all/issues/250)
- [Codage confort demandé pour un Clio IV 2012 1.5 dCi — issue #761, cedricp/ddt4all](https://github.com/cedricp/ddt4all/issues/761) (question restée sans réponse technique)
- [Feux de jour/croisement Clio IV — forum Planète Renault](https://www.planeterenault.com/forum/clio-iv-feux-de-jour-et-feux-et-feux-de-croisement-regle-t40546.html) (contient un témoignage d'un Clio IV Dynamique 90 dCi de 2013 — proche de votre véhicule, mais sans valeur de codage)

## Point réglementaire — feux de jour (DRL)

Un intervenant du forum Planète Renault (fil ci-dessus) signale que modifier
le comportement des feux de jour peut rendre le véhicule **non conforme au
règlement ECE** pour la circulation sur route ouverte — contrairement aux
fonctions de confort pur (verrouillage, unités d'affichage, HSA), qui n'ont
pas cette implication. À éviter tant que ce point n'est pas éclairci pour
votre marché/homologation.

## Marche à suivre

1. Installer ddt4all sur un PC (https://github.com/cedricp/ddt4all/releases),
   brancher l'adaptateur OBD2 (une fois le souci de connexion réglé) et se
   connecter à l'UCH (`26` dans la table d'adressage du projet `X98 - Renault
   Clio IV`).
2. Noter la version logicielle détectée et la liste réelle des paramètres que
   ddt4all propose pour cet UCH précis.
3. Comparer avec le tableau ci-dessus : si un paramètre de nom similaire
   apparaît, tester le changement **dans ddt4all d'abord** (facilement
   réversible) avant d'envisager de le reporter dans la valise.
4. Une fois une valeur confirmée sur votre véhicule, elle peut être ajoutée
   comme `ActuatorDef`/`ParameterDef` dans `config/vehicle_profile.yaml` (voir
   `config/vehicle_profile.clio4.example.yaml` pour un squelette prêt à
   compléter) — c'est à ce moment-là une documentation que vous détenez
   légitimement, plus une donnée supposée.
