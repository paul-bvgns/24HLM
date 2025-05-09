#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestion du clavier pour changer la langue des vidéos à la volée
"""

import threading
import sys
import time
import os
import select
import termios
import tty
import logging
import signal
from config import VIDEOS, DEFAULT_LANGUAGE


class KeyboardManager:
    def __init__(self):
        self.current_language = DEFAULT_LANGUAGE
        self.running = False
        self.keyboard_thread = None
        self.language_change_callback = None
        self.languages = {
            '1': 'fr',  # Français
            '2': 'it',  # Italien 
            '3': 'de',  # Allemand
            '4': 'en'   # Anglais
        }

    def start(self, language_change_callback=None):
        """Démarre l'écoute du clavier dans un thread séparé"""
        if self.running:
            return False

        self.language_change_callback = language_change_callback
        self.running = True
        self.keyboard_thread = threading.Thread(target=self._keyboard_loop)
        self.keyboard_thread.daemon = True
        self.keyboard_thread.start()

        
        print("Gestion du clavier démarrée")
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
        self.running = False
        if self.keyboard_thread:
            self.keyboard_thread.join(timeout=1.0)
        print("Gestion du clavier arrêtée")

    def _keyboard_loop(self):
        """Boucle principale pour l'écoute du clavier avec timeout"""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            tty.setraw(fd)
            while self.running:
                r, _, _ = select.select([sys.stdin], [], [], 0.1)
                if r:
                    key = sys.stdin.read(1)
                    print(f"Touche détectée: {key}")
                    if key in self.languages:
                        new_language = self.languages[key]
                        if new_language != self.current_language and new_language in VIDEOS:
                            self.current_language = new_language
                            print(f"Changement de langue: {self._get_language_name(new_language)}")
                            if self.language_change_callback:
                                self.language_change_callback(new_language)
                    elif key == 'q':
                        os.kill(os.getpid(), signal.SIGINT)
                    elif key == '0':
                        print("Touche 0 détectée")
                        try:
                            from main import play_overlay
                            play_overlay()
                        except ImportError:
                            print("Impossible d'importer play_overlay depuis main")
                time.sleep(0.01)

        except Exception as e:
            print(f"Erreur: {e}")
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

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


    keyboard = KeyboardManager()
    keyboard.start(on_language_change)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        keyboard.stop()
        print("Test terminé")