#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
import os
import signal
from config import VIDEOS, DEFAULT_LANGUAGE

class LanguageManager:
    def __init__(self):
        self.current_language = DEFAULT_LANGUAGE
        self.languages = {
            '1': 'fr',
            '2': 'it',
            '3': 'de',
            '4': 'en'
        }

    def handle_key(self, key_char):
        if key_char in self.languages:
            lang = self.languages[key_char]
            if lang != self.current_language and lang in VIDEOS:
                self.current_language = lang
                print(f"Langue changée : {self._get_language_name(lang)}")
                print(f"Vidéo en boucle : {VIDEOS[lang]['loop']}")
                print(f"Vidéo unique : {VIDEOS[lang]['once']}")
                # Ici tu peux appeler un callback ou fonction de changement
        elif key_char == '0':
            print("Lecture de la vidéo temporaire")
            try:
                from main import play_overlay
                play_overlay()
            except ImportError:
                print("Impossible d’importer play_overlay depuis main")
        elif key_char == 'q':
            print("Sortie demandée")
            os.kill(os.getpid(), signal.SIGINT)

    def _get_language_name(self, code):
        return {
            'fr': 'Français',
            'it': 'Italien',
            'de': 'Allemand',
            'en': 'Anglais'
        }.get(code, code)

# Création de la fenêtre invisible
def launch_keyboard_window():
    manager = LanguageManager()

    root = tk.Tk()
    root.overrideredirect(True)       # Pas de barre de titre
    root.attributes('-alpha', 0.0)    # Entièrement invisible
    root.geometry("1x1+0+0")          # Coin de l'écran
    root.bind("<Key>", lambda e: manager.handle_key(e.char))
    root.focus_force()                # Force le focus pour capter les touches

    print("Appuyez sur 1/2/3/4 pour changer de langue, 0 pour vidéo temporaire, q pour quitter.")
    root.mainloop()

if __name__ == "__main__":
    try:
        launch_keyboard_window()
    except KeyboardInterrupt:
        print("Interrompu proprement.")
