#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration pour le système de déclenchement vidéo
"""

# Mode de déclenchement: "button" ou "encoder"
MODE = "button"

# Seuil pour l'encodeur rotatif
ENCODER_THRESHOLD = 90

# Configuration des broches GPIO
BUTTON_PIN = 17
CLK_PIN = 21
DT_PIN = 20

# Chemins des fichiers vidéo par langue
VIDEOS = {
    "fr": {  # Français
        "loop": "/home/pha5e/24HLM/01.DEV/videos/fr/loop-video.mp4",
        "once": "/home/pha5e/24HLM/01.DEV/videos/fr/video-test.mp4"
    },
    "it": {  # Italien
        "loop": "/home/pha5e/24HLM/01.DEV/videos/it/loop-video.mp4",
        "once": "/home/pha5e/24HLM/01.DEV/videos/it/video-test.mp4"
    },
    "de": {  # Allemand
        "loop": "/home/pha5e/24HLM/01.DEV/videos/de/loop-video.mp4",
        "once": "/home/pha5e/24HLM/01.DEV/videos/de/video-test.mp4"
    },
    "en": {  # Anglais
        "loop": "/home/pha5e/24HLM/01.DEV/videos/en/loop-video.mp4",
        "once": "/home/pha5e/24HLM/01.DEV/videos/en/video-test.mp4"
    }
}


# Langue par défaut
DEFAULT_LANGUAGE = "fr"

# Pour la rétrocompatibilité
VIDEO_LOOP = VIDEOS[DEFAULT_LANGUAGE]["loop"]
VIDEO_ONCE = VIDEOS[DEFAULT_LANGUAGE]["once"]

# Paramètres pour la réinitialisation de l'encodeur
ENCODER_RESET_TIMEOUT = 3  # secondes
