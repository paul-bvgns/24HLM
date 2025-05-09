#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pygame
import cv2
import numpy as np
from config import VIDEOS, DEFAULT_LANGUAGE


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

        print("Touches : 1=FR, 2=IT, 3=DE, 4=EN, 0=vidéo temporaire, q=quitter")

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
                    print("[ACTION] Lecture vidéo temporaire")
                    self.play_video(VIDEOS[self.current_language]["once"], loop=False)
                elif key in {'1', '2', '3', '4'}:
                    lang_map = {'1': 'fr', '2': 'it', '3': 'de', '4': 'en'}
                    new_lang = lang_map[key]
                    if new_lang != self.current_language:
                        print(f"[LANGUE] Passage de {self.current_language} à {new_lang}")
                        self.current_language = new_lang
                        self.play_video(VIDEOS[self.current_language]["loop"], loop=True)

    def run(self):
        self.play_video(VIDEOS[self.current_language]["loop"], loop=True)
        pygame.quit()


if __name__ == "__main__":
    player = VideoPlayer()
    player.run()
