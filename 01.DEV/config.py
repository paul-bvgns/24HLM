#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration pour le système de déclenchement vidéo
"""

MODE = "encoder"

ENCODER_THRESHOLD = 70

ENCODER_RESET_TIMEOUT = 5

BUTTON_PRESS_THRESHOLD = 5

BUTTON_RESET_TIMEOUT = 5

BUTTON_PIN = 17
CLK_PIN = 21
DT_PIN = 20

# Optimisations vidéo
VIDEO_BUFFER_SIZE = 1  # Buffer minimal
TARGET_FPS = 30
ENABLE_VSYNC = True

VIDEOS = {
    "fr": {
        "loop": "/home/pha5e/24HLM/01.DEV/videos/fr/loop.mp4",
        "action": "/home/pha5e/24HLM/01.DEV/videos/fr/action.mp4",
        "learn": "/home/pha5e/24HLM/01.DEV/videos/fr/learn.mp4",
        "image": "/home/pha5e/24HLM/01.DEV/videos/fr/image.png",
    },
    "es": {
        "loop": "/home/pha5e/24HLM/01.DEV/videos/es/loop-video.mp4",
        "once": "/home/pha5e/24HLM/01.DEV/videos/es/video-test.mp4"
    },
    "en": {
        "loop": "/home/pha5e/24HLM/01.DEV/videos/en/loop-video.mp4",
        "once": "/home/pha5e/24HLM/01.DEV/videos/en/video-test.mp4"
    }
}


DEFAULT_LANGUAGE = "fr"

VIDEO_LOOP = VIDEOS[DEFAULT_LANGUAGE]["loop"]
VIDEO_ONCE = VIDEOS[DEFAULT_LANGUAGE]["learn"]
