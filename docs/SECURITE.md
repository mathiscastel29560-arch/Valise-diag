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

Ce logiciel est fourni sans garantie. Vous êtes seul responsable de son usage.
