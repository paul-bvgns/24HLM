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

        self.max_slide_distance = self.size[1]
        self.current_slide_offset = 0

        self.progress_bar_width = 20
        self.progress_bar_height = self.size[1] - 40
        self.progress_bar_x = 20
        self.progress_bar_y = 20

        self.font_size = 100
        self.font = pygame.font.Font(None, self.font_size)
        self.text_content = "CONTINUE DE TOURNER !"
        self.text_color = (255, 255, 255)
        self.text_surface = self.font.render(self.text_content, True, self.text_color)
        self.text_rect = self.text_surface.get_rect()
        self.text_rect.centerx = self.size[0] // 2

        print("Touches : 1=FR, 2=IT, 3=DE, 4=EN, 0=vidéo temporaire, q=quitter")

        # Setup GPIO
        self.encoder_counter = 0
        self.button_counter = 0
        self.last_rotation_time = time.time()
        self.last_button_time = time.time()
        self.setup_gpio()

    def setup_gpio(self):
        if MODE == "button":
            self.button = Button(BUTTON_PIN)
            self.button.when_pressed = self.on_button_press

            # Lancement d'un thread pour reset du bouton après timeout
            thread = threading.Thread(target=self.button_timeout_loop)
            thread.daemon = True
            thread.start()

        elif MODE == "encoder":
            self.encoder = RotaryEncoder(CLK_PIN, DT_PIN)
            self.encoder.when_rotated = self.on_encoder_rotate

            # Lancement d'un thread pour reset après timeout
            thread = threading.Thread(target=self.encoder_timeout_loop)
            thread.daemon = True
            thread.start()

    def ease_out_quad(t):
        return 1 - (1 - t) ** 2

    def calculate_slide_offset(self):
        if MODE == "button":
            #progress = min(self.button_counter / BUTTON_PRESS_THRESHOLD, 1.0)
            raw_progress = min(self.button_counter / BUTTON_PRESS_THRESHOLD, 1.0)
            progress = self.ease_out_quad(raw_progress)
        elif MODE == "encoder":
            #progress = min(self.encoder_counter / ENCODER_THRESHOLD, 1.0)
            raw_progress = min(self.encoder_counter / ENCODER_THRESHOLD, 1.0)
            progress = self.ease_out_quad(raw_progress)
        else:
            progress = 0

        self.current_slide_offset = int(progress * self.max_slide_distance)

        return progress

    def draw_progress_bar(self):
        background_rect = pygame.Rect(
            self.progress_bar_x - 2,
            self.progress_bar_y - 2,
            self.progress_bar_width + 4,
            self.progress_bar_height + 4
        )
        pygame.draw.rect(self.screen, (40, 40, 40), background_rect)

        empty_rect = pygame.Rect(
            self.progress_bar_x,
            self.progress_bar_y,
            self.progress_bar_width,
            self.progress_bar_height
        )
        pygame.draw.rect(self.screen, (100, 100, 100), empty_rect)

        if MODE == "button":
            progress = min(self.button_counter / BUTTON_PRESS_THRESHOLD, 1.0)
        elif MODE == "encoder":
            progress = min(self.encoder_counter / ENCODER_THRESHOLD, 1.0)
        else:
            progress = 0

        if progress > 0:
            filled_height = int(self.progress_bar_height * progress)
            filled_rect = pygame.Rect(
                self.progress_bar_x,
                self.progress_bar_y + self.progress_bar_height - filled_height,
                self.progress_bar_width,
                filled_height
            )
            pygame.draw.rect(self.screen, (255, 0, 0), filled_rect)

    def draw_sliding_text(self):
        if self.current_slide_offset > 0:
            text_y = self.current_slide_offset - self.text_rect.height - 60  # 60

            text_position = (self.text_rect.centerx - self.text_rect.width // 2, text_y)

            if text_y + self.text_rect.height > 0:
                self.screen.blit(self.text_surface, text_position)

    def on_button_press(self):
        if not self.overlay_playing:
            self.button_counter += 1
            self.last_button_time = time.time()
            print(f"[BUTTON] Clic détecté : {self.button_counter}/{BUTTON_PRESS_THRESHOLD} - Glissement: {self.current_slide_offset}px")

            if self.button_counter >= BUTTON_PRESS_THRESHOLD:
                print("[BUTTON] clics atteints. Lancement vidéo temporaire.")
                self.overlay_requested = True
                self.button_counter = 0
                self.current_slide_offset = 0  # Reset du glissement

    def button_timeout_loop(self):
        while self.running:
            if (time.time() - self.last_button_time > BUTTON_RESET_TIMEOUT and
                    self.button_counter != 0):
                print("[BUTTON] Inactivité détectée. Reset des clics.")
                self.button_counter = 0
                self.current_slide_offset = 0  # Reset du glissement
            time.sleep(0.1)

    def on_encoder_rotate(self):
        if not self.overlay_playing:
            self.encoder_counter += 1
            self.last_rotation_time = time.time()
            print(f"[ENCODER] Rotation détectée : {self.encoder_counter}/{ENCODER_THRESHOLD} - Glissement: {self.current_slide_offset}px")
            if self.encoder_counter >= ENCODER_THRESHOLD:
                print("[ENCODER] Seuil atteint. Lancement vidéo temporaire.")
                self.overlay_requested = True
                self.encoder_counter = 0
                self.current_slide_offset = 0  # Reset du glissement

    def encoder_timeout_loop(self):
        while self.running:
            if (time.time() - self.last_rotation_time > ENCODER_RESET_TIMEOUT and
                    self.encoder_counter != 0):
                print("[ENCODER] Inactivité détectée. Reset.")
                self.encoder_counter = 0
                self.current_slide_offset = 0  # Reset du glissement
            time.sleep(0.1)

    def render_frame(self, surface):
        progress = self.calculate_slide_offset()

        if self.current_slide_offset > 0:
            self.screen.fill((0, 0, 0))

            # Afficher la vidéo décalée vers le bas
            self.screen.blit(surface, (0, self.current_slide_offset))

            # Afficher le texte qui descend avec la vidéo
            self.draw_sliding_text()

            #if progress > 0.5:
            #    fade_progress = (progress - 0.5) * 2
            #   fade_alpha = int(fade_progress * 255)
            #   fade_surface = pygame.Surface(self.size)
            #   fade_surface.set_alpha(fade_alpha)
            #  fade_surface.fill((0, 0, 0))
            #  self.screen.blit(fade_surface, (0, 0))
        else:
            self.screen.blit(surface, (0, 0))

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

            # Affichage avec effet de glissement basé sur le progrès
            self.render_frame(surface)

            # Affichage de la barre de progression
            self.draw_progress_bar()

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