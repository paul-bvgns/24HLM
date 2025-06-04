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

        # États du système
        self.state = "loop"  # "loop", "fade_to_action", "action", "fade_to_learn", "learn"
        self.fade_progress = 0.0
        self.fade_speed = 0.08

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
        self.interaction_detected = False
        self.setup_gpio()

        # Vidéos
        self.loop_cap = None
        self.action_cap = None
        self.learn_cap = None
        self.current_frame_loop = None
        self.current_frame_action = None
        self.current_frame_learn = None

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

        # Calcul du slide offset seulement en mode action
        if self.state == "action":
            target = self.interaction_progress * self.max_slide_distance
            self.slide_offset_smooth = lerp(self.slide_offset_smooth, target, self.lerp_speed)
            self.current_slide_offset = int(self.slide_offset_smooth)

        return self.interaction_progress

    def update_state_machine(self):
        """Met à jour la machine d'état"""
        if self.state == "loop" and self.interaction_detected:
            # Démarrer le fade vers action
            print("[STATE] Loop → Fade vers Action")
            self.state = "fade_to_action"
            self.fade_progress = 0.0
            self.interaction_detected = False

        elif self.state == "fade_to_action":
            # Progression du fade
            self.fade_progress += self.fade_speed
            if self.fade_progress >= 1.0:
                self.fade_progress = 1.0
                print("[STATE] Fade terminé → Mode Action")
                self.state = "action"

        elif self.state == "action" and self.interaction_progress >= 1.0:
            # Seuil atteint, démarrer fade vers learn
            print("[STATE] Action → Fade vers Learn")
            self.state = "fade_to_learn"
            self.fade_progress = 0.0

        elif self.state == "fade_to_learn":
            # Progression du fade vers learn
            self.fade_progress += self.fade_speed
            if self.fade_progress >= 1.0:
                self.fade_progress = 1.0
                print("[STATE] Fade terminé → Mode Learn")
                self.state = "learn"

    def draw_progress_bar(self):
        """Affiche la barre de progression seulement en mode action"""
        if self.state != "action":
            return

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
        """Affiche le texte qui slide seulement en mode action"""
        if self.state == "action" and self.current_slide_offset > 0:
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
        if self.state in ["loop", "action"]:
            self.button_counter += 1
            self.last_button_time = time.time()
            print(f"[BUTTON] Clic détecté : {self.button_counter}/{BUTTON_PRESS_THRESHOLD}")

            # Marquer qu'une interaction a été détectée
            if self.state == "loop":
                self.interaction_detected = True

    def button_timeout_loop(self):
        while self.running:
            if (time.time() - self.last_button_time > BUTTON_RESET_TIMEOUT and
                    self.button_counter != 0 and self.state not in ["learn", "fade_to_learn"]):
                print("[BUTTON] Inactivité détectée. Reset.")
                self.reset_interaction()
            time.sleep(0.1)

    def on_encoder_rotate(self):
        if self.state in ["loop", "action"]:
            self.encoder_counter += 1
            self.last_rotation_time = time.time()
            print(f"[ENCODER] Rotation détectée : {self.encoder_counter}/{ENCODER_THRESHOLD}")

            # Marquer qu'une interaction a été détectée
            if self.state == "loop":
                self.interaction_detected = True

    def encoder_timeout_loop(self):
        while self.running:
            if (time.time() - self.last_rotation_time > ENCODER_RESET_TIMEOUT and
                    self.encoder_counter != 0 and self.state not in ["learn", "fade_to_learn"]):
                print("[ENCODER] Inactivité détectée. Reset.")
                self.reset_interaction()
            time.sleep(0.1)

    def reset_interaction(self):
        """Remet à zéro tout le système"""
        print("[RESET] Remise à zéro complète")
        self.button_counter = 0
        self.encoder_counter = 0
        self.interaction_progress = 0.0
        self.current_slide_offset = 0
        self.slide_offset_smooth = 0
        self.fade_progress = 0.0
        self.interaction_detected = False
        self.state = "loop"

    def get_video_frame(self, cap):
        """Récupère la prochaine frame d'une vidéo"""
        if cap and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                # Redémarrer la vidéo si elle est en boucle (pour loop et action)
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if not ret:
                    return None

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

        if self.state == "loop":
            # Mode loop normal
            surface_to_render = self.current_frame_loop

        elif self.state == "fade_to_action":
            # Fade de loop vers action
            if self.current_frame_loop and self.current_frame_action:
                surface_to_render = self.blend_surfaces(
                    self.current_frame_loop,
                    self.current_frame_action,
                    self.fade_progress
                )
            else:
                surface_to_render = self.current_frame_loop

        elif self.state == "action":
            # Mode action avec slide
            surface_to_render = self.current_frame_action

        elif self.state == "fade_to_learn":
            # Fade de action vers learn
            if self.current_frame_action and self.current_frame_learn:
                surface_to_render = self.blend_surfaces(
                    self.current_frame_action,
                    self.current_frame_learn,
                    self.fade_progress
                )
            else:
                surface_to_render = self.current_frame_action

        elif self.state == "learn":
            # Mode learn
            surface_to_render = self.current_frame_learn

        # Affichage avec ou sans slide
        if surface_to_render:
            if self.state == "action" and self.current_slide_offset > 0:
                # Appliquer le slide uniquement en mode action
                self.screen.fill((0, 0, 0))
                self.screen.blit(surface_to_render, (0, self.current_slide_offset))
                self.draw_sliding_text()
            else:
                # Affichage normal
                self.screen.blit(surface_to_render, (0, 0))

    def handle_learn_video_end(self):
        """Gère la fin de la vidéo learn"""
        if self.state == "learn" and self.learn_cap:
            ret, _ = self.learn_cap.read()
            if not ret:
                # Fin de la vidéo learn
                print("[LEARN] Vidéo terminée, retour au loop")
                self.learn_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset pour la prochaine fois
                self.reset_interaction()
                return True
        return False

    def run(self):
        try:
            while self.running:
                # Initialiser les vidéos
                self.loop_cap = cv2.VideoCapture(VIDEOS[self.current_language]["loop"])
                self.action_cap = cv2.VideoCapture(VIDEOS[self.current_language]["action"])
                self.learn_cap = cv2.VideoCapture(VIDEOS[self.current_language]["learn"])

                if not self.loop_cap.isOpened():
                    print(f"[ERREUR] Impossible d'ouvrir la vidéo loop")
                    break

                if not self.action_cap.isOpened():
                    print(f"[ERREUR] Impossible d'ouvrir la vidéo action")
                    break

                if not self.learn_cap.isOpened():
                    print(f"[ERREUR] Impossible d'ouvrir la vidéo learn")
                    break

                print(f"[VIDÉO] Démarrage en mode loop - Langue: {self.current_language}")

                while self.running:
                    # Récupérer les frames selon l'état
                    if self.state in ["loop", "fade_to_action"]:
                        self.current_frame_loop = self.get_video_frame(self.loop_cap)
                        if self.state == "fade_to_action":
                            self.current_frame_action = self.get_video_frame(self.action_cap)

                    elif self.state in ["action", "fade_to_learn"]:
                        self.current_frame_action = self.get_video_frame(self.action_cap)
                        if self.state == "fade_to_learn":
                            self.current_frame_learn = self.get_video_frame(self.learn_cap)

                    elif self.state == "learn":
                        self.current_frame_learn = self.get_video_frame(self.learn_cap)
                        # Vérifier si la vidéo learn est terminée
                        if self.handle_learn_video_end():
                            continue

                    # Calculer la progression de l'interaction
                    self.calculate_interaction_progress()

                    # Mettre à jour la machine d'état
                    self.update_state_machine()

                    # Rendu
                    self.render_frame()

                    # Afficher les éléments UI
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
                if self.learn_cap:
                    self.learn_cap.release()

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
                elif key == '0' and self.state == "loop":
                    print("[ACTION] Touche 0 → vidéo learn")
                    self.state = "learn"
                elif key in {'1', '2', '3', '4'} and self.state == "loop":
                    lang_map = {'1': 'fr', '2': 'it', '3': 'de', '4': 'en'}
                    new_lang = lang_map[key]
                    if new_lang != self.current_language:
                        print(f"[LANGUE] Passage de {self.current_language} à {new_lang}")
                        self.current_language = new_lang
                        raise StopIteration

if __name__ == "__main__":
    player = VideoPlayer()
    player.run()