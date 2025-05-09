#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestion du clavier pour changer la langue des vidéos à la volée (version pynput)
"""

import threading
import os
import signal
import time
import logging
from pynput import keyboard
from config import VIDEOS, DEFAULT_LANGUAGE


class KeyboardManager:
    def __init__(self):
        self.current_language = DEFAULT_LANGUAGE
        self.listener = None
        self.language_change_callback = None
        self.languages = {
            '1': 'fr',  # Français
            '2': 'it',  # Italien
            '3': 'de',  # Allemand
            '4': 'en'   # Anglais
        }

    def start(self, language_change_callback=None):
        """Démarre l'écoute du clavier en global (via pynput)"""
        if self.listener:
            return False

        self.language_change_callback = language_change_callback

        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.start()

        print("Gestion du clavier démarrée (pynput)")
        print("Appuyez sur :")
        print("- 1: Français")
        print("- 2: Italien")
        print("- 3: Allemand")
        print("- 4: Anglais")
        print("- q: Quitter")
        print("- 0: Lancer la vidéo temporaire")

        return True

    def stop(self):
        """Arrête l'écoute du clavier"""
        if self.listener:
            self.listener.stop()
            self.listener = None
        print("Gestion du clavier arrêtée")

    def _on_press(self, key):
        """Gestion des touches"""
        try:
            k = key.char
        except AttributeError:
            return  # Touche spéciale ignorée

        print(f"Touche détectée: {k}")

        if k in self.languages:
            new_language = self.languages[k]
            if new_language != self.current_language and new_language in VIDEOS:
                self.current_language = new_language
                print(f"Changement de langue: {self._get_language_name(new_language)}")
                if self.language_change_callback:
                    self.language_change_callback(new_language)

        elif k == 'q':
            print("Interruption demandée")
            os.kill(os.getpid(), signal.SIGINT)

        elif k == '0':
            print("Touche 0 détectée")
            try:
                from main import play_overlay
                play_overlay()
            except ImportError:
                print("Impossible d'importer play_overlay depuis main")

    def _get_language_name(self, code):
        names = {
            'fr': 'Français',
            'it': 'Italien',
            'de': 'Allemand',
            'en': 'Anglais'
        }
        return names.get(code, code)

    def get_current_language(self):
        """Retourne la langue actuellement sélectionnée"""
        return self.current_language


if __name__ == "__main__":
    def on_language_change(lang):
        print(f"Langue changée pour: {lang}")
        print(f"Vidéo en boucle: {VIDEOS[lang]['loop']}")
        print(f"Vidéo unique: {VIDEOS[lang]['once']}")

    keyboard_mgr = KeyboardManager()
    keyboard_mgr.start(on_language_change)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        keyboard_mgr.stop()
        print("Arrêt du programme")
