"""Doc rapide : vocabulaire courant du codage/programmation ECU (onglet Programmation)."""

DOC_CODAGE = """
VOCABULAIRE DE CODAGE / PROGRAMMATION ECU
==========================================

DID (Data Identifier)
  Identifiant (2 octets en UDS) d'une donnée lisible/écrivable dans l'ECU
  (ex : un paramètre, une variante logicielle, un numéro de pièce).

Identifiant local (Local Identifier)
  Équivalent du DID en KWP2000 (1 octet), utilisé sur les liaisons K-line.

Codage long / codage court
  Terme historique VAG : suite d'octets stockée dans l'ECU qui active ou
  désactive des options (ex : présence d'un capteur, type de boîte de
  vitesses). Le "codage court" (quelques bits) a été remplacé par le
  "codage long" (plusieurs octets) sur les ECU plus récents.

Canal d'adaptation (Adaptation)
  Réglage fin d'une valeur numérique stockée dans l'ECU (ex : position de
  butée d'un papillon, compteur d'usure d'embrayage). Différent du codage :
  c'est une valeur réglable, pas une option on/off.

Code atelier (Workshop Code)
  Numéro d'identification de l'atelier, enregistré dans l'historique de
  l'ECU à chaque intervention (traçabilité, pas un mot de passe).

SecurityAccess (Seed/Key)
  Mécanisme de déverrouillage en deux temps : l'ECU envoie une valeur
  aléatoire ("seed"), l'outil renvoie une "clé" calculée à partir de cette
  valeur pour prouver qu'il est autorisé à écrire. L'algorithme de calcul
  est propriétaire : ce logiciel ne l'implémente pas — vous devez fournir
  votre propre fonction si vous en disposez légitimement pour votre véhicule.

Routine (RoutineControl / StartRoutineByLocalIdentifier)
  Procédure exécutée par l'ECU sur demande (ex : recalibrage d'un capteur,
  test d'un composant), démarrée/arrêtée/consultée via un identifiant de
  routine.

Bloc KW1281 (Block)
  Sur les ECU VAG pré-CAN (câble KKL), les échanges se font par blocs
  numérotés (longueur, compteur, titre, données) plutôt que par DID. Le
  "titre" du bloc joue le même rôle qu'un DID mais sa valeur dépend de
  l'ECU et de l'année du véhicule.

Reprogrammation / Flashing
  Remplacement complet du logiciel de l'ECU. Non géré par cet outil : très
  risqué sans le matériel et les fichiers homologués par le constructeur,
  une coupure de courant pendant un flash peut rendre l'ECU inutilisable.

Checksum
  Octet(s) de contrôle ajoutés à une trame pour détecter une erreur de
  transmission. Une trame reçue avec un mauvais checksum est normalement
  rejetée par l'ECU (voir kwp2000.py pour le calcul utilisé sur K-line).
"""


def afficher_doc_codage() -> None:
    print(DOC_CODAGE)
