#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pygame
import cv2
import numpy as np
import RPi.GPIO as GPIO
import threading
import time
from config import *

class VideoPlayer:
    def __init__(self):
        pygame.init()
        self.screen_info = pygame.display.Info()
        self.size = (self.screen_info.current_w, self.screen_info.current_h)
        self.screen = pygame.display.set_mode(self.size, pygame.FULLSCREEN)
        pygame.display.set_caption("Lecteur vidéo")

        self.clock = pygame.time.Clock()
        self.current_language = DEFAULT_LANGUAGE
        self.running = True
        self.overlay_requested = False

        print("Touches : 1=FR, 2=IT, 3=DE, 4=EN, 0=vidéo temporaire, q=quitter")

        # Setup GPIO
        self.setup_gpio()
        self.start_gpio_thread()

    def setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        if MODE == "button":
            GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        elif MODE == "encoder":
            GPIO.setup(CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def start_gpio_thread(self):
        if MODE == "button":
            thread = threading.Thread(target=self.gpio_button_loop)
        elif MODE == "encoder":
            thread = threading.Thread(target=self.gpio_encoder_loop)
        thread.daemon = True
        thread.start()

    def gpio_button_loop(self):
        while self.running:
            if GPIO.input(BUTTON_PIN) == GPIO.HIGH:
                print("[GPIO] Bouton appuyé")
                self.overlay_requested = True
                time.sleep(0.5)
            time.sleep(0.01)

    def gpio_encoder_loop(self):
        last_clk = GPIO.input(CLK_PIN)
        count = 0
        last_time = time.time()

        while self.running:
            clk = GPIO.input(CLK_PIN)
            dt = GPIO.input(DT_PIN)

            if clk != last_clk:
                last_time = time.time()
                if dt != clk:
                    count += 1
                    print(f"[ENCODER] Rotation détectée : {count}")
                    if count >= ENCODER_THRESHOLD:
                        print("[ENCODER] Seuil atteint. Lancement vidéo temporaire.")
                        self.overlay_requested = True
                        count = 0
                last_clk = clk

            if time.time() - last_time > ENCODER_RESET_TIMEOUT and count != 0:
                print("[ENCODER] Inactivité détectée. Reset.")
                count = 0

            time.sleep(0.01)

    def play_video(self, path, loop=False, fade=True):
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            print(f"[ERREUR] Impossible d'ouvrir : {path}")
            return

        print(f"[VIDÉO] Lecture : {path}")
        fade_duration = 30  # frames pour fade in/out
        frame_count = 0
        fading_out = False

        while cap.isOpened() and self.running:
            ret, frame = cap.read()
            if not ret:
                if loop:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    frame_count = 0
                    continue
                else:
                    break

            frame = cv2.resize(frame, self.size)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            surface = pygame.surfarray.make_surface(np.flipud(np.rot90(frame)))
            surface = pygame.transform.scale(surface, self.size)

            if fade:
                # Appliquer fondu entrant (au début)
                if frame_count < fade_duration:
                    alpha = int(255 * (frame_count / fade_duration))
                    surface.set_alpha(alpha)
                # Appliquer fondu sortant (à la fin)
                elif not loop and cap.get(cv2.CAP_PROP_POS_FRAMES) >= cap.get(cv2.CAP_PROP_FRAME_COUNT) - fade_duration:
                    remaining = cap.get(cv2.CAP_PROP_FRAME_COUNT) - cap.get(cv2.CAP_PROP_POS_FRAMES)
                    alpha = int(255 * (remaining / fade_duration))
                    surface.set_alpha(alpha)
                else:
                    surface.set_alpha(255)

            self.screen.blit(surface, (0, 0))
            pygame.display.flip()
            frame_count += 1

            self.handle_events()

            # Si on demande une superposition, on quitte cette vidéo
            if self.overlay_requested:
                self.overlay_requested = False
                cap.release()
                self.play_video(VIDEOS[self.current_language]["once"], loop=False, fade=True)
                cap = cv2.VideoCapture(path)
                frame_count = 0

            self.clock.tick(30)

        cap.release()


    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                key = event.unicode
                if key == 'q':
                    print("[EXIT] Quitter")
                    self.running = False
                elif key == '0':
                    print("[ACTION] Touche 0 → vidéo temporaire")
                    self.overlay_requested = True
                elif key in {'1', '2', '3', '4'}:
                    lang_map = {'1': 'fr', '2': 'it', '3': 'de', '4': 'en'}
                    new_lang = lang_map[key]
                    if new_lang != self.current_language:
                        print(f"[LANGUE] Passage de {self.current_language} à {new_lang}")
                        self.current_language = new_lang
                        raise StopIteration  # Quitte la lecture en boucle pour recharger

    def run(self):
        loop_cap = cv2.VideoCapture(VIDEOS[self.current_language]["loop"])
        overlay_cap = None
        overlay_alpha = 0
        overlay_fade_frames = 30
        overlay_frame_count = 0
        showing_overlay = False

        while self.running:
            # --- Lecture de la vidéo de boucle ---
            ret, frame = loop_cap.read()
            if not ret:
                loop_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            frame = cv2.resize(frame, self.size)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            background = pygame.surfarray.make_surface(np.flipud(np.rot90(frame)))
            background = pygame.transform.scale(background, self.size)

            self.screen.blit(background, (0, 0))

            # --- Gérer superposition si demandée ---
            if self.overlay_requested and not showing_overlay:
                print("[OVERLAY] Lecture vidéo temporaire...")
                overlay_cap = cv2.VideoCapture(VIDEOS[self.current_language]["once"])
                overlay_frame_count = 0
                showing_overlay = True
                self.overlay_requested = False

            if showing_overlay and overlay_cap:
                ret_o, frame_o = overlay_cap.read()
                if not ret_o:
                    overlay_cap.release()
                    overlay_cap = None
                    showing_overlay = False
                    overlay_alpha = 0
                else:
                    frame_o = cv2.resize(frame_o, self.size)
                    frame_o = cv2.cvtColor(frame_o, cv2.COLOR_BGR2RGB)
                    overlay = pygame.surfarray.make_surface(np.flipud(np.rot90(frame_o)))
                    overlay = pygame.transform.scale(overlay, self.size)

                    # --- Fading ---
                    total_frames = overlay_cap.get(cv2.CAP_PROP_FRAME_COUNT)
                    if overlay_frame_count < overlay_fade_frames:
                        # Fade in
                        overlay_alpha = int(255 * (overlay_frame_count / overlay_fade_frames))
                    elif overlay_frame_count > total_frames - overlay_fade_frames:
                        # Fade out
                        overlay_alpha = int(255 * ((total_frames - overlay_frame_count) / overlay_fade_frames))
                    else:
                        overlay_alpha = 255

                    overlay.set_alpha(max(0, min(255, overlay_alpha)))
                    self.screen.blit(overlay, (0, 0))
                    overlay_frame_count += 1

            pygame.display.flip()
            self.handle_events()
            self.clock.tick(30)



if __name__ == "__main__":
    player = VideoPlayer()
    player.run()
