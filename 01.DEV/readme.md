# 🎛️ Configuration Raspberry Pi pour 24HLM

Ce guide vous accompagne pas à pas dans la configuration d'un Raspberry Pi optimisé pour exécuter le projet **24HLM**, en désactivant les services inutiles, en activant le SSH et en configurant un script de démarrage automatique.

---

## 📺 Installation de MPV (Lecteur multimédia)

Installez **MPV**

```bash
sudo apt install mpv
```

---

## 📡 Désactiver le Bluetooth

Éditez le fichier de configuration :

```bash
sudo nano /boot/firmware/config.txt
```

Ajoutez la ligne suivante à la fin du fichier :

```bash
dtoverlay=disable-bt
```

Puis désactivez le service :

```bash
sudo systemctl disable hciuart
```

---

## 🔐 Activer et configurer SSH

Activez le SSH avec l'outil de configuration :

```bash
sudo raspi-config
```

> Naviguez vers `Interfaces -> SSH` et activez-le.

Modifiez ensuite la configuration SSH :

```bash
sudo nano /etc/ssh/sshd_config
```

Ajoutez ou modifiez les lignes suivantes :

```bash
PermitEmptyPasswords yes
PasswordAuthentication yes
PermitRootLogin yes
```

Supprimez le mot de passe utilisateur `pha5e` :

```bash
sudo passwd -d pha5e
```

Redémarrez le service SSH :

```bash
sudo systemctl restart ssh
```

---

## 🚀 Démarrage automatique du script 24HLM

Créez le dossier `autostart` s’il n’existe pas :

```bash
mkdir -p ~/.config/autostart
```

Créez un fichier de démarrage :

```bash
nano ~/.config/autostart/24HLM.desktop
```

Ajoutez le contenu suivant :

```ini
[Desktop Entry]
Type=Application
Name=24HLM Script
Exec=python3 /home/pha5e/Desktop/24HLM/01.DEV/main.py
X-GNOME-Autostart-enabled=true
```

---

## 🔕 Mode NoDisturb (anti-notification & anti-veilles)

Créez le script `nodisturb.sh` :

```bash
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
```

Créez ensuite un service `systemd` :

```bash
sudo nano /etc/systemd/system/nodisturb.service
```

Ajoutez-y :

```ini
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
```

Activez et démarrez le service :

```bash
sudo systemctl enable nodisturb.service
sudo systemctl start nodisturb.service
sudo systemctl status nodisturb.service
```

---
## ⌨️ Raccourcis Clavier

Pendant l'exécution de l'application vidéo, certaines touches du clavier permettent d'interagir avec le système :

- `q` : Quitter immédiatement le processus.
- `1` : Lancer le flux **français**.
- `2` : Lancer le flux **anglais**.
- `3` : Lancer le flux **italien**.
- `4` : Lancer le flux **allemand**.
- `0` : Lancer la **vidéo éphémère**.


