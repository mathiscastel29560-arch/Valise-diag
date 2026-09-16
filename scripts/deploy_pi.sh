#!/usr/bin/env bash
# Déploiement de la valise diag sur le Raspberry Pi.
#
# À lancer SUR LE PI, depuis le dossier cloné :
#   bash scripts/deploy_pi.sh
#
# Ne supprime jamais rien : un éventuel ancien programme est déplacé (pas
# effacé), et ce script est prévu pour être relancé sans risque (idempotent)
# quand vous mettez à jour le code plus tard (git pull && bash scripts/deploy_pi.sh).
set -euo pipefail

DEST="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$HOME/ancien-programme-$(date +%Y%m%d-%H%M%S)"

echo "=== Valise diag — déploiement ==="
echo "Dossier du projet : $DEST"
echo

# 1. Sauvegarde de l'éventuel ancien programme (déplacé, jamais supprimé)
read -rp "Chemin de l'ancien programme à mettre de côté (Entrée pour ignorer) : " ancien
if [ -n "${ancien:-}" ]; then
    if [ -e "$ancien" ]; then
        mkdir -p "$BACKUP_DIR"
        mv "$ancien" "$BACKUP_DIR/"
        echo "-> Déplacé vers $BACKUP_DIR"
    else
        echo "-> '$ancien' introuvable, ignoré."
    fi
fi
echo

# 2. Paquets système
echo "=== Paquets système ==="
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip python3-dev build-essential \
    git nano w3m network-manager kbd

# 3. Environnement Python
echo "=== Environnement Python ==="
cd "$DEST"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
deactivate

# 4. Configuration (ne touche pas à un fichier déjà présent)
echo "=== Configuration ==="
[ -f config/vehicle_profile.yaml ] || cp config/vehicle_profile.example.yaml config/vehicle_profile.yaml
[ -f config/app.yaml ] || cp config/app.example.yaml config/app.yaml
echo "-> Pensez à éditer config/vehicle_profile.yaml et config/app.yaml (nano)."

# 5. Accès aux adaptateurs USB série (ELM327 / KKL)
sudo usermod -aG dialout "$USER"
echo "-> $USER ajouté au groupe dialout (effectif après reconnexion/reboot)."
echo

# 6. Signale un éventuel ancien autostart sans y toucher automatiquement
echo "=== Vérification de ~/.bashrc ==="
if grep -n "python3" "$HOME/.bashrc" 2>/dev/null | grep -v "valise-diag"; then
    echo "-> Les lignes ci-dessus semblent lancer un ancien programme au démarrage."
    echo "   Commentez-les à la main (nano ~/.bashrc) sinon les deux essaieront de démarrer."
else
    echo "-> Rien trouvé."
fi
echo

# 7. Autostart du nouveau menu sur tty1
MARK="# --- valise-diag autostart ---"
if ! grep -qF "$MARK" "$HOME/.bashrc" 2>/dev/null; then
    {
        echo ""
        echo "$MARK"
        sed "s#/home/pi/valise-diag#$DEST#g" "$DEST/systemd/autostart.bashrc.snippet"
    } >> "$HOME/.bashrc"
    echo "-> Bloc de démarrage automatique ajouté à la fin de ~/.bashrc."
else
    echo "-> Bloc de démarrage automatique déjà présent, inchangé."
fi

sudo mkdir -p /etc/systemd/system/getty@tty1.service.d
sed "s/--autologin pi/--autologin $USER/" "$DEST/systemd/getty-autologin-tty1.conf" \
    | sudo tee /etc/systemd/system/getty@tty1.service.d/override.conf > /dev/null
sudo systemctl daemon-reload
echo "-> Autologin sur tty1 configuré pour l'utilisateur $USER."

echo
echo "=== Terminé ==="
echo "Testez avant de redémarrer :"
echo "  cd $DEST && source .venv/bin/activate && python3 -m valise_diag --config config/app.yaml --simulate"
echo
echo "Une fois satisfait, redémarrez (sudo reboot) : le menu se lance tout seul sur l'écran du Pi."
