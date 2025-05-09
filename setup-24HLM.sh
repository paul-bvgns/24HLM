#!/bin/bash

# Script d'installation automatique pour le projet 24HLM sur Raspberry Pi
# Ce script exécute toutes les étapes nécessaires après l'installation de Raspberry Pi OS

# Affichage d'un message de bienvenue
echo "====================================================="
echo "    Configuration automatique Raspberry Pi 24HLM"
echo "====================================================="
echo ""
echo "Ce script va configurer votre Raspberry Pi pour le projet 24HLM:"
echo "- Installation de MPV"
echo "- Désactivation du Bluetooth"
echo "- Configuration du SSH"
echo "- Configuration du démarrage automatique"
echo "- Configuration du mode NoDisturb"
echo ""
echo "Le processus démarrera dans 5 secondes..."
sleep 5

# Mise à jour des paquets
echo "====================================================="
echo "Mise à jour des paquets système..."
echo "====================================================="
sudo apt update && sudo apt upgrade -y

# Installation de MPV
echo "====================================================="
echo "Installation de MPV..."
echo "====================================================="
sudo apt install -y mpv

# Désactivation du Bluetooth
echo "====================================================="
echo "Désactivation du Bluetooth..."
echo "====================================================="
echo "dtoverlay=disable-bt" | sudo tee -a /boot/firmware/config.txt
sudo systemctl disable hciuart

# Configuration SSH
echo "====================================================="
echo "Configuration du SSH..."
echo "====================================================="
# Activer SSH
sudo systemctl enable ssh
sudo systemctl start ssh

# Modifier la configuration SSH
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
cat << EOF | sudo tee -a /etc/ssh/sshd_config
PermitEmptyPasswords yes
PasswordAuthentication yes
PermitRootLogin yes
EOF

# Supprimer le mot de passe utilisateur (remplacer 'pha5e' par le nom d'utilisateur si différent)
sudo passwd -d pha5e

# Redémarrer le service SSH
sudo systemctl restart ssh

# Création du dossier autostart
echo "====================================================="
echo "Configuration du démarrage automatique du script 24HLM..."
echo "====================================================="
mkdir -p ~/.config/autostart

# Création du fichier de démarrage automatique
cat << EOF > ~/.config/autostart/24HLM.desktop
[Desktop Entry]
Type=Application
Name=24HLM Script
Exec=python3 /home/pha5e/Desktop/24HLM/01.DEV/main.py
X-GNOME-Autostart-enabled=true
EOF

# Création du mode NoDisturb
echo "====================================================="
echo "Configuration du mode NoDisturb..."
echo "====================================================="

# Création du script nodisturb.sh
cat << EOF > ~/Desktop/24HLM/nodisturb.sh
#!/bin/bash

# Désactiver les notifications
sudo systemctl stop notification-daemon
sudo systemctl disable notification-daemon

# Désactiver la mise en veille et l'écran de veille
xset s off
xset -dpms

# Désactiver les mises à jour automatiques
sudo sed -i 's/APT::Periodic::Update-Package-Lists "1"/APT::Periodic::Update-Package-Lists "0"/' /etc/apt/apt.conf.d/20auto-upgrades
sudo sed -i 's/APT::Periodic::Unattended-Upgrade "1"/APT::Periodic::Unattended-Upgrade "0"/' /etc/apt/apt.conf.d/20auto-upgrades

# Supprimer les messages système
echo "*.*   -/dev/null" | sudo tee -a /etc/rsyslog.d/99-disable.conf
EOF

# Rendre le script exécutable
chmod +x ~/Desktop/24HLM/nodisturb.sh

# Création du service systemd pour NoDisturb
cat << EOF | sudo tee /etc/systemd/system/nodisturb.service
[Unit]
Description=NoDisturb
After=graphical.target

[Service]
Type=oneshot
ExecStart=/home/pha5e/Desktop/24HLM/nodisturb.sh
RemainAfterExit=true
User=pha5e

[Install]
WantedBy=multi-user.target
EOF

# Activation et démarrage du service
sudo systemctl enable nodisturb.service
sudo systemctl start nodisturb.service

# Clonage du dépôt GitHub
echo "====================================================="
echo "Clone du dépôt GitHub 24HLM..."
echo "====================================================="
git clone https://github.com/paul-bvgns/24HLM.git 24HLM


# Message de fin
echo "====================================================="
echo "Configuration terminée avec succès!"
echo "====================================================="
echo ""
echo "Un redémarrage est recommandé pour appliquer tous les changements."
echo "Voulez-vous redémarrer maintenant? (o/n)"
read response

if [[ "$response" =~ ^([oO][uU][iI]|[oO])$ ]]; then
    echo "Redémarrage du système dans 5 secondes..."
    sleep 5
    sudo reboot
else
    echo "N'oubliez pas de redémarrer manuellement plus tard."
fi