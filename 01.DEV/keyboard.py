#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestion du clavier pour changer la langue des vidéos à la volée
"""

import os
import signal
import tkinter as tk
from config import VIDEOS, DEFAULT_LANGUAGE


class KeyboardManager:
    def __init__(self):
        self.current_language = DEFAULT_LANGUAGE
        self.running = False
        self.language_change_callback = None
        self.tk_root = None

        self.languages = {
            '1': 'fr',  # Français
            '2': 'it',  # Italien
            '3': 'de',  # Allemand
            '4': 'en'   # Anglais
        }

    def start(self, language_change_callback=None):
        """Démarre l'écoute du clavier dans une fenêtre tkinter invisible"""
        if self.running:
            return False

        self.language_change_callback = language_change_callback
        self.running = True

        print("Gestion du clavier démarrée (fenêtre invisible)")
        print("Appuyez sur :")
        print("- 1: Français")
        print("- 2: Italien")
        print("- 3: Allemand")
        print("- 4: Anglais")
        print("- q: Quitter")
        print("- 0: Lancer la vidéo temporaire")

        self.tk_root = tk.Tk()
        self.tk_root.overrideredirect(True)        # Supprime bordures
        self.tk_root.attributes('-alpha', 0.0)     # Fenêtre invisible
        self.tk_root.geometry("1x1+0+0")           # Coin de l'écran
        self.tk_root.bind("<Key>", self._on_key)
        self.tk_root.focus_force()                 # Force le focus
        self.tk_root.mainloop()
        return True

    def stop(self):
        """Arrête proprement la fenêtre tkinter"""
        self.running = False
        if self.tk_root:
            self.tk_root.destroy()
            self.tk_root = None
        print("Gestion du clavier arrêtée")

    def _on_key(self, event):
        key = event.char
        print(f"Touche détectée: {repr(key)}")

        if key in self.languages:
            new_language = self.languages[key]
            if new_language != self.current_language and new_language in VIDEOS:
                self.current_language = new_language
                print(f"Changement de langue: {self._get_language_name(new_language)}")
                if self.language_change_callback:
                    self.language_change_callback(new_language)

        elif key == 'q':
            self.stop()
            os.kill(os.getpid(), signal.SIGINT)

        elif key == '0':
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

    keyboard = KeyboardManager()
    try:
        keyboard.start(on_language_change)
    except KeyboardInterrupt:
        keyboard.stop()
        print("Test terminé")
