#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pygame
import cv2
import numpy as np
import time
import threading
from gpiozero import Button, RotaryEncoder
from config import *

class VideoPlayer:
    def __init__(self):
        pygame.init()
        self.screen_info = pygame.display.Info()
        self.size = (self.screen_info.current_w, self.screen_info.current_h)
        self.screen = pygame.display.set_mode(self.size, pygame.FULLSCREEN)
        pygame.display.set_caption("Lecteur vidéo")
        pygame.mouse.set_visible(False)

        self.clock = pygame.time.Clock()
        self.current_language = DEFAULT_LANGUAGE
        self.running = True
        self.overlay_requested = False
        self.overlay_playing = False

        print("Touches : 1=FR, 2=IT, 3=DE, 4=EN, 0=vidéo temporaire, q=quitter")

        # Setup GPIO
        self.encoder_counter = 0
        self.last_rotation_time = time.time()
        self.setup_gpio()

    def setup_gpio(self):
        if MODE == "button":
            self.button = Button(BUTTON_PIN)
            self.button.when_pressed = self.on_button_press
        elif MODE == "encoder":
            self.encoder = RotaryEncoder(CLK_PIN, DT_PIN)
            self.encoder.when_rotated = self.on_encoder_rotate

            # Lancement d’un thread pour reset après timeout
            thread = threading.Thread(target=self.encoder_timeout_loop)
            thread.daemon = True
            thread.start()

    def on_button_press(self):
        if not self.overlay_playing:
            print("[GPIOZERO] Bouton appuyé")
            self.overlay_requested = True

    def on_encoder_rotate(self):
        if not self.overlay_playing:
            self.encoder_counter += 1
            self.last_rotation_time = time.time()
            print(f"[ENCODER] Rotation détectée : {self.encoder_counter}")
            if self.encoder_counter >= ENCODER_THRESHOLD:
                print("[ENCODER] Seuil atteint. Lancement vidéo temporaire.")
                self.overlay_requested = True
                self.encoder_counter = 0

    def encoder_timeout_loop(self):
        while self.running:
            if (time.time() - self.last_rotation_time > ENCODER_RESET_TIMEOUT and
                    self.encoder_counter != 0):
                print("[ENCODER] Inactivité détectée. Reset.")
                self.encoder_counter = 0
            time.sleep(0.1)

    def play_video(self, path, loop=False):
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            print(f"[ERREUR] Impossible d'ouvrir : {path}")
            return

        print(f"[VIDÉO] Lecture : {path}")

        while cap.isOpened() and self.running:
            ret, frame = cap.read()
            if not ret:
                if loop:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break

            frame = cv2.resize(frame, self.size)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            surface = pygame.surfarray.make_surface(np.flipud(np.rot90(frame)))
            self.screen.blit(surface, (0, 0))
            pygame.display.flip()

            self.handle_events()
            if self.overlay_requested:
                self.overlay_requested = False
                self.overlay_playing = True
                cap.release()
                self.play_video(VIDEOS[self.current_language]["once"], loop=False)
                cap = cv2.VideoCapture(path)

            self.clock.tick(30)

        cap.release()
        self.overlay_playing = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                key = event.unicode
                if key == '-':
                    print("[EXIT] Quitter")
                    self.running = False
                elif key == '0' and not self.overlay_playing:
                    print("[ACTION] Touche 0 → vidéo temporaire")
                    self.overlay_requested = True
                elif key in {'1', '2', '3', '4'} and not self.overlay_playing:
                    lang_map = {'1': 'fr', '2': 'it', '3': 'de', '4': 'en'}
                    new_lang = lang_map[key]
                    if new_lang != self.current_language:
                        print(f"[LANGUE] Passage de {self.current_language} à {new_lang}")
                        self.current_language = new_lang
                        raise StopIteration

    def run(self):
        try:
            while self.running:
                self.play_video(VIDEOS[self.current_language]["loop"], loop=True)
        except StopIteration:
            self.run()
        finally:
            pygame.quit()
            print("[EXIT] Nettoyage terminé.")

if __name__ == "__main__":
    player = VideoPlayer()
    player.run()
