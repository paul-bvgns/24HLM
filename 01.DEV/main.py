#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pygame
import cv2
import numpy as np
import time
import threading
from gpiozero import Button, RotaryEncoder
from config import *

def lerp(a, b, t):
    return a + (b - a) * t

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

        # États de vidéo
        self.video_state = "loop"  # "loop", "action", "learn"
        self.fade_progress = 0.0
        self.is_fading = False

        # Variables pour l'interaction
        self.interaction_progress = 0.0
        self.max_slide_distance = self.size[1]
        self.current_slide_offset = 0
        self.slide_offset_smooth = 0
        self.lerp_speed = 0.1

        # Interface utilisateur
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

        # GPIO
        self.encoder_counter = 0
        self.button_counter = 0
        self.last_rotation_time = time.time()
        self.last_button_time = time.time()
        self.setup_gpio()

        # Vidéos
        self.loop_cap = None
        self.action_cap = None
        self.current_frame_loop = None
        self.current_frame_action = None

    def setup_gpio(self):
        if MODE == "button":
            self.button = Button(BUTTON_PIN)
            self.button.when_pressed = self.on_button_press
            thread = threading.Thread(target=self.button_timeout_loop)
            thread.daemon = True
            thread.start()
        elif MODE == "encoder":
            self.encoder = RotaryEncoder(CLK_PIN, DT_PIN)
            self.encoder.when_rotated = self.on_encoder_rotate
            thread = threading.Thread(target=self.encoder_timeout_loop)
            thread.daemon = True
            thread.start()

    def calculate_interaction_progress(self):
        if MODE == "button":
            self.interaction_progress = min(self.button_counter / BUTTON_PRESS_THRESHOLD, 1.0)
        elif MODE == "encoder":
            self.interaction_progress = min(self.encoder_counter / ENCODER_THRESHOLD, 1.0)
        else:
            self.interaction_progress = 0

        # Calcul du slide offset
        target = self.interaction_progress * self.max_slide_distance
        self.slide_offset_smooth = lerp(self.slide_offset_smooth, target, self.lerp_speed)
        self.current_slide_offset = int(self.slide_offset_smooth)

        return self.interaction_progress

    def start_fade_to_action(self):
        """Démarre le fade de la vidéo loop vers la vidéo action"""
        if self.video_state == "loop" and not self.is_fading:
            print("[FADE] Début du fade vers vidéo action")
            self.is_fading = True
            self.fade_progress = 0.0
            self.video_state = "action"

    def update_fade(self):
        """Met à jour le fade entre les vidéos"""
        if self.is_fading:
            self.fade_progress += 0.05  # Vitesse du fade
            if self.fade_progress >= 1.0:
                self.fade_progress = 1.0
                self.is_fading = False
                print("[FADE] Fade terminé")

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

        if self.interaction_progress > 0:
            filled_height = int(self.progress_bar_height * self.interaction_progress)
            filled_rect = pygame.Rect(
                self.progress_bar_x,
                self.progress_bar_y + self.progress_bar_height - filled_height,
                self.progress_bar_width,
                filled_height
            )
            pygame.draw.rect(self.screen, (255, 0, 0), filled_rect)

    def draw_sliding_text(self):
        if self.current_slide_offset > 0:
            text_y = self.current_slide_offset - self.text_rect.height - 60
            center_y = self.size[1] // 2 - self.text_rect.height // 2
            text_y = min(text_y, center_y)

            text_position = (
                self.text_rect.centerx - self.text_rect.width // 2,
                text_y
            )

            if text_y + self.text_rect.height > 0:
                self.screen.blit(self.text_surface, text_position)

    def on_button_press(self):
        if self.video_state == "loop":
            self.button_counter += 1
            self.last_button_time = time.time()
            print(f"[BUTTON] Clic détecté : {self.button_counter}/{BUTTON_PRESS_THRESHOLD}")

            # Démarrer le fade dès la première interaction
            if self.button_counter == 1:
                self.start_fade_to_action()

            if self.button_counter >= BUTTON_PRESS_THRESHOLD:
                print("[BUTTON] Seuil atteint. Lancement vidéo learn.")
                self.video_state = "learn"
                self.reset_interaction()

    def button_timeout_loop(self):
        while self.running:
            if (time.time() - self.last_button_time > BUTTON_RESET_TIMEOUT and
                    self.button_counter != 0 and self.video_state != "learn"):
                print("[BUTTON] Inactivité détectée. Reset des clics.")
                self.reset_interaction()
            time.sleep(0.1)

    def on_encoder_rotate(self):
        if self.video_state == "loop":
            self.encoder_counter += 1
            self.last_rotation_time = time.time()
            print(f"[ENCODER] Rotation détectée : {self.encoder_counter}/{ENCODER_THRESHOLD}")

            # Démarrer le fade dès la première interaction
            if self.encoder_counter == 1:
                self.start_fade_to_action()

            if self.encoder_counter >= ENCODER_THRESHOLD:
                print("[ENCODER] Seuil atteint. Lancement vidéo learn.")
                self.video_state = "learn"
                self.reset_interaction()

    def encoder_timeout_loop(self):
        while self.running:
            if (time.time() - self.last_rotation_time > ENCODER_RESET_TIMEOUT and
                    self.encoder_counter != 0 and self.video_state != "learn"):
                print("[ENCODER] Inactivité détectée. Reset.")
                self.reset_interaction()
            time.sleep(0.1)

    def reset_interaction(self):
        """Remet à zéro les compteurs d'interaction"""
        self.button_counter = 0
        self.encoder_counter = 0
        self.interaction_progress = 0.0
        self.current_slide_offset = 0
        self.slide_offset_smooth = 0
        self.fade_progress = 0.0
        self.is_fading = False

    def get_video_frame(self, cap):
        """Récupère la prochaine frame d'une vidéo"""
        if cap and cap.isOpened():
            ret, frame = cap.read()
            if ret:
                frame = cv2.resize(frame, self.size)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return pygame.surfarray.make_surface(np.flipud(np.rot90(frame)))
            else:
                # Redémarrer la vidéo si elle est en boucle
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if ret:
                    frame = cv2.resize(frame, self.size)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    return pygame.surfarray.make_surface(np.flipud(np.rot90(frame)))
        return None

    def blend_surfaces(self, surface1, surface2, alpha):
        """Mélange deux surfaces avec un facteur alpha"""
        if surface1 is None:
            return surface2
        if surface2 is None:
            return surface1

        # Créer une surface temporaire pour le blend
        blended = surface1.copy()
        surface2_copy = surface2.copy()
        surface2_copy.set_alpha(int(255 * alpha))
        blended.blit(surface2_copy, (0, 0))
        return blended

    def render_frame(self):
        """Rendu principal avec gestion des états"""
        surface_to_render = None

        if self.video_state == "loop":
            # Mode loop normal
            surface_to_render = self.current_frame_loop

        elif self.video_state == "action":
            # Mode action avec fade et slide
            if self.is_fading and self.current_frame_loop and self.current_frame_action:
                # Blend entre loop et action
                surface_to_render = self.blend_surfaces(
                    self.current_frame_loop,
                    self.current_frame_action,
                    self.fade_progress
                )
            else:
                surface_to_render = self.current_frame_action

            # Appliquer le slide
            if surface_to_render and self.current_slide_offset > 0:
                self.screen.fill((0, 0, 0))
                self.screen.blit(surface_to_render, (0, self.current_slide_offset))
                self.draw_sliding_text()
            elif surface_to_render:
                self.screen.blit(surface_to_render, (0, 0))

        elif self.video_state == "learn":
            # Mode learn - vidéo simple
            surface_to_render = self.current_frame_loop  # Utilise la même variable pour simplifier
            if surface_to_render:
                self.screen.blit(surface_to_render, (0, 0))

        # Affichage par défaut si pas de surface
        if surface_to_render and self.video_state not in ["action"]:
            self.screen.blit(surface_to_render, (0, 0))

    def play_video_learn(self, path):
        """Joue la vidéo learn une seule fois"""
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            print(f"[ERREUR] Impossible d'ouvrir : {path}")
            return

        print(f"[VIDÉO LEARN] Lecture : {path}")

        while cap.isOpened() and self.running and self.video_state == "learn":
            ret, frame = cap.read()
            if not ret:
                # Fin de la vidéo learn, retour au loop
                print("[VIDÉO LEARN] Terminée, retour au loop")
                break

            frame = cv2.resize(frame, self.size)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            surface = pygame.surfarray.make_surface(np.flipud(np.rot90(frame)))

            self.screen.blit(surface, (0, 0))
            pygame.display.flip()

            self.handle_events()
            self.clock.tick(30)

        cap.release()
        # Retour au mode loop
        self.video_state = "loop"
        self.reset_interaction()

    def run(self):
        try:
            while self.running:
                # Initialiser les vidéos
                self.loop_cap = cv2.VideoCapture(VIDEOS[self.current_language]["loop"])
                self.action_cap = cv2.VideoCapture(VIDEOS[self.current_language]["action"])

                if not self.loop_cap.isOpened():
                    print(f"[ERREUR] Impossible d'ouvrir la vidéo loop")
                    break

                if not self.action_cap.isOpened():
                    print(f"[ERREUR] Impossible d'ouvrir la vidéo action")
                    break

                print(f"[VIDÉO] Démarrage en mode loop - Langue: {self.current_language}")

                while self.running:
                    # Récupérer les frames
                    if self.video_state in ["loop", "action"]:
                        self.current_frame_loop = self.get_video_frame(self.loop_cap)
                        if self.video_state == "action":
                            self.current_frame_action = self.get_video_frame(self.action_cap)

                    # Calculer la progression de l'interaction
                    self.calculate_interaction_progress()

                    # Mettre à jour le fade
                    self.update_fade()

                    # Si on passe en mode learn
                    if self.video_state == "learn":
                        self.loop_cap.release()
                        self.action_cap.release()
                        self.play_video_learn(VIDEOS[self.current_language]["learn"])
                        # Après learn, redémarrer les vidéos loop/action
                        break

                    # Rendu
                    self.render_frame()

                    # Afficher la barre de progression
                    if self.video_state == "action":
                        self.draw_progress_bar()

                    pygame.display.flip()

                    # Gérer les événements
                    self.handle_events()
                    self.clock.tick(30)

                # Nettoyer les vidéos
                if self.loop_cap:
                    self.loop_cap.release()
                if self.action_cap:
                    self.action_cap.release()

        except StopIteration:
            self.run()
        finally:
            pygame.quit()
            print("[EXIT] Nettoyage terminé.")

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                key = event.unicode
                if key == '-':
                    print("[EXIT] Quitter")
                    self.running = False
                elif key == '0' and self.video_state == "loop":
                    print("[ACTION] Touche 0 → vidéo learn")
                    self.video_state = "learn"
                elif key in {'1', '2', '3', '4'} and self.video_state == "loop":
                    lang_map = {'1': 'fr', '2': 'it', '3': 'de', '4': 'en'}
                    new_lang = lang_map[key]
                    if new_lang != self.current_language:
                        print(f"[LANGUE] Passage de {self.current_language} à {new_lang}")
                        self.current_language = new_lang
                        raise StopIteration

if __name__ == "__main__":
    player = VideoPlayer()
    player.run()