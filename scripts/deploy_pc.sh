#!/usr/bin/env bash
# Installation de la valise diag sur un PC Linux classique (Fedora/dnf) —
# pour brancher l'adaptateur OBD directement sur l'ordinateur, sans passer
# par le Raspberry Pi. Pas de mode kiosque ici (pas d'autologin/autostart
# sur une console tty1, ça n'a pas de sens sur un PC de bureau) : on
# installe juste l'appli, vous la lancez vous-même depuis un terminal.
#
# À lancer depuis le dossier cloné :
#   bash scripts/deploy_pc.sh
#
# Ne supprime jamais rien, et peut être relancé sans risque (idempotent)
# pour mettre à jour les dépendances après un git pull.
set -euo pipefail

DEST="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== Valise diag — installation PC (Fedora) ==="
echo "Dossier du projet : $DEST"
echo

# 1. Paquets système
echo "=== Paquets système (dnf) ==="
sudo dnf install -y python3 python3-pip python3-virtualenv python3-devel \
    gcc git nano nmap

# 2. Environnement Python
echo "=== Environnement Python ==="
cd "$DEST"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
deactivate

# 3. Configuration (ne touche pas à un fichier déjà présent)
echo "=== Configuration ==="
[ -f config/vehicle_profile.yaml ] || cp config/vehicle_profile.example.yaml config/vehicle_profile.yaml
[ -f config/app.yaml ] || cp config/app.example.yaml config/app.yaml
echo "-> Pensez à éditer config/vehicle_profile.yaml et config/app.yaml (nano) —"
echo "   notamment le port série (voir dmesg après avoir branché l'adaptateur)."

# 4. Accès aux adaptateurs USB série (ELM327 / KKL)
sudo usermod -aG dialout "$USER"
echo "-> $USER ajouté au groupe dialout (effectif après déconnexion/reconnexion de session)."
echo

echo "=== Vérification finale ==="
source "$DEST/.venv/bin/activate"
if ! python3 -c "import valise_diag" 2>/dev/null; then
    echo "ERREUR : l'installation Python a échoué, le programme ne peut pas démarrer." >&2
    exit 1
fi
deactivate
echo "-> Le programme s'importe correctement."

echo
echo "=== Terminé ==="
echo "Déconnectez-vous/reconnectez-vous (ou redémarrez) pour que l'appartenance"
echo "au groupe dialout prenne effet, puis lancez :"
echo "  cd $DEST && source .venv/bin/activate && python3 -m valise_diag --config config/app.yaml"
echo
echo "Sans adaptateur branché, testez d'abord avec --simulate :"
echo "  python3 -m valise_diag --config config/app.yaml --simulate"
