#!/bin/bash

# Script d'installation automatique pour le projet 24HLM sur Raspberry Pi
# Ce script exécute toutes les étapes nécessaires après l'installation de Raspberry Pi OS

# Affichage d'un message de bienvenue
echo "====================================================="
echo "    Configuration automatique Raspberry Pi 24HLM"
echo "====================================================="
echo ""
echo "Ce script va configurer votre Raspberry Pi pour le projet 24HLM:"
echo "- Installation des dépendances Python"
echo "- Clone du dépôt GitHub"
echo "- Configuration du SSH"
echo "- Configuration du démarrage automatique"
echo "- Configuration du mode NoDisturb"
echo "- Personnalisation du bureau"
echo ""
echo "Le processus démarrera dans 5 secondes..."
echo ""
echo ""
sleep 5

# Mise à jour des paquets
#echo "====================================================="
#echo "Mise à jour des paquets système..."
#echo "====================================================="
#sudo apt update && sudo apt upgrade -y

# Installation des dépendances Python
echo ""
echo ""
echo "====================================================="
echo "Installation des dépendances Python..."
echo "====================================================="
sudo apt install -y python3-pip python3-dev python3-opencv python3-pygame python3-numpy python3-gpiozero


echo ""
echo ""
echo "====================================================="
echo "Clonage du dépôt GitHub..."
echo "====================================================="
git clone https://github.com/paul-bvgns/24HLM.git 24HLM
echo "Dépôt cloné dans le répertoire 24HLM."

# Configuration SSH
echo ""
echo ""
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

# Supprimer le mot de passe utilisateur
sudo passwd -d pha5e

# Redémarrer le service SSH
sudo systemctl restart ssh

# Création du dossier autostart
echo ""
echo ""
echo "====================================================="
echo "Configuration du démarrage automatique du script 24HLM..."
echo "====================================================="
mkdir -p ~/.config/autostart

# Création du fichier de démarrage automatique
cat << EOF > ~/.config/autostart/24HLM.desktop
[Desktop Entry]
Type=Application
Name=24HLM Script
Exec=lxterminal -e "sudo /home/pha5e/run_24hlm.sh"
X-GNOME-Autostart-enabled=true
EOF

# Création du script run_24hlm.sh
cat << EOF > /home/pha5e/run_24hlm.sh
#!/bin/bash

sudo python3 /home/pha5e/24HLM/01.DEV/main.py



# Configuration du mode NoDisturb
echo ""
echo ""
echo "====================================================="
echo "Configuration du mode NoDisturb..."
echo "====================================================="

# Création du script no_disturb.sh
cat > /home/pha5e/no_disturb.sh << 'EOF'
#!/bin/bash

# Script mode "Ne pas déranger" pour Raspberry Pi
# Ce script désactive temporairement plusieurs services pour éviter les interruptions

# Vérifier si l'utilisateur est root
if [ "$(id -u)" -ne 0 ]; then
    echo "Ce script doit être exécuté en tant que root (utilisez sudo)."
    exit 1
fi

echo "Activation du mode 'Ne pas déranger'..."

# Désactiver le Bluetooth
echo "Désactivation du Bluetooth..."
rfkill block bluetooth
systemctl stop bluetooth.service
systemctl disable bluetooth.service
echo "Bluetooth désactivé."

# Désactiver le Wi-Fi
#echo "Désactivation du Wi-Fi..."
#rfkill block wifi
#systemctl stop wpa_supplicant.service
#systemctl disable wpa_supplicant.service
#echo "Wi-Fi désactivé."


# Désactiver les mises à jour automatiques
echo "Désactivation des mises à jour automatiques..."
systemctl stop apt-daily.service
systemctl stop apt-daily.timer
systemctl stop apt-daily-upgrade.timer
systemctl stop apt-daily-upgrade.service
systemctl disable apt-daily.service
systemctl disable apt-daily.timer
systemctl disable apt-daily-upgrade.timer
systemctl disable apt-daily-upgrade.service
echo "Mises à jour automatiques désactivées."

# Désactiver les notifications système (si utilisation d'un environnement graphique)
if [ -n "$DISPLAY" ]; then
    echo "Désactivation des notifications..."
    if command -v notify-send &> /dev/null; then
        # Utilisation d'un fichier pour stocker l'état précédent
        mkdir -p ~/.config/no-disturb
        gsettings get org.freedesktop.Notifications.settings enable > ~/.config/no-disturb/notifications-state
        gsettings set org.freedesktop.Notifications.settings enable false
    fi
    echo "Notifications désactivées."
fi

# Désactiver les journaux non essentiels
echo "Réduction du niveau de journalisation..."
systemctl stop rsyslog.service
systemctl disable rsyslog.service
echo "Journalisation réduite."

# Réduire les services en arrière-plan
echo "Désactivation des services non essentiels..."
systemctl stop avahi-daemon.service
systemctl disable avahi-daemon.service
systemctl stop triggerhappy.service
systemctl disable triggerhappy.service
echo "Services non essentiels désactivés."

# Créer un script de restauration
cat > /home/pha5e/disable_no_disturb.sh << 'INNEREOF'
#!/bin/bash

# Script de restauration - désactive le mode "Ne pas déranger"
if [ "$(id -u)" -ne 0 ]; then
    echo "Ce script doit être exécuté en tant que root (utilisez sudo)."
    exit 1
fi

echo "Désactivation du mode 'Ne pas déranger'..."

# Réactiver le Bluetooth
echo "Réactivation du Bluetooth..."
rfkill unblock bluetooth
systemctl start bluetooth.service
systemctl enable bluetooth.service
echo "Bluetooth réactivé."

# Réactiver les mises à jour automatiques
echo "Réactivation des mises à jour automatiques..."
systemctl start apt-daily.service
systemctl start apt-daily.timer
systemctl start apt-daily-upgrade.timer
systemctl start apt-daily-upgrade.service
systemctl enable apt-daily.service
systemctl enable apt-daily.timer
systemctl enable apt-daily-upgrade.timer
systemctl enable apt-daily-upgrade.service
echo "Mises à jour automatiques réactivées."

# Réactiver les notifications système
if [ -n "$DISPLAY" ]; then
    echo "Réactivation des notifications..."
    if command -v notify-send &> /dev/null && [ -f ~/.config/no-disturb/notifications-state ]; then
        previous_state=$(cat ~/.config/no-disturb/notifications-state)
        gsettings set org.freedesktop.Notifications.settings enable "$previous_state"
    fi
    echo "Notifications réactivées."
fi

# Réactiver les journaux
echo "Restauration de la journalisation..."
systemctl start rsyslog.service
systemctl enable rsyslog.service
echo "Journalisation restaurée."

# Réactiver les services en arrière-plan
echo "Réactivation des services..."
systemctl start avahi-daemon.service
systemctl enable avahi-daemon.service
systemctl start triggerhappy.service
systemctl enable triggerhappy.service
echo "Services réactivés."

echo "Mode 'Ne pas déranger' désactivé. Tous les services sont restaurés."
INNEREOF

# Rendre le script de restauration exécutable
chmod +x /home/pha5e/disable_no_disturb.sh

echo "Mode 'Ne pas déranger' activé."
echo "Pour restaurer les paramètres normaux, exécutez: sudo /home/pha5e/disable_no_disturb.sh"
EOF

# Rendre le script no_disturb exécutable
chmod +x /home/pha5e/no_disturb.sh

# Créer un service systemd pour exécuter no_disturb au démarrage
cat > /etc/systemd/system/no-disturb.service << EOF
[Unit]
Description=Mode Ne pas déranger
After=network.target

[Service]
Type=oneshot
ExecStart=/home/pha5e/no_disturb.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Activer le service no-disturb
systemctl enable no-disturb.service

echo "Script NoDisturb installé et configuré pour s'exécuter au démarrage."


# Création d'un raccourci sur le bureau pour lancer le projet
echo ""
echo ""
echo "====================================================="
echo "Création d'un raccourci sur le bureau..."
echo "====================================================="

# Créer un fichier .desktop sur le bureau
cat << EOF > /home/pha5e/Desktop/24HLM.desktop
[Desktop Entry]
Name=24HLM Project
Comment=Lancer le projet 24HLM (Python)
Exec=lxterminal -e "sudo python3 /home/pha5e/24HLM/01.DEV/main.py"
Icon=application-x-executable
Terminal=true
Type=Application
Categories=Utility;
X-GNOME-Autostart-enabled=true
EOF

# Donner les permissions d'exécution au fichier .desktop
chmod +x /home/pha5e/Desktop/24HLM.desktop

# Message de confirmation
echo "Le raccourci pour lancer 24HLM a été créé sur le bureau."


echo ""
echo ""
echo "====================================================="
echo "Personnalisation du bureau..."
echo "====================================================="

# wallpaper
pcmanfm --set-wallpaper /home/pha5e/24HLM/00.RESSOURCES/wallpaper.png --wallpaper-mode=fit

# Message de fin
echo ""
echo ""
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
