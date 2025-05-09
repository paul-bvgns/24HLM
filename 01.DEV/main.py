#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import subprocess
import time
import signal
import os
import sys
from config import *
from keyboard import KeyboardManager

# Variables globales
current_loop_proc = None
current_language = DEFAULT_LANGUAGE
keyboard = KeyboardManager()

def setup_gpio():
    """Configure les broches GPIO en fonction du mode sélectionné"""
    GPIO.setmode(GPIO.BCM)
    if MODE == "button":
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        print(f"[INIT] Mode de déclenchement : {MODE} (Pin {BUTTON_PIN})")
    elif MODE == "encoder":
        GPIO.setup(CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        print(f"[INIT] Mode de déclenchement : {MODE} (Pins CLK={CLK_PIN}, DT={DT_PIN})")
    else:
        raise ValueError(f"Mode inconnu: {MODE}")

def start_loop():
    """Lance la vidéo en boucle"""
    global current_loop_proc, current_language
    
    # Arrêter la vidéo en boucle précédente si elle existe
    if current_loop_proc:
        try:
            current_loop_proc.terminate()
            time.sleep(0.5)  # Attendre que le processus se termine
        except:
            pass
    
    loop_video = VIDEOS[current_language]["loop"]
    print(f"[LOOP] Lancement de la vidéo de boucle ({current_language}).")
    
    # Arguments pour mpv en mode boucle
    args = [
        "mpv", loop_video,
        "--fs",
        "--loop=inf",
        "--mute",
        "--no-terminal",
        "--no-border",
        "--geometry=0:0",
        "--ontop=no",
        "--force-window=yes",
        "--wid=0",
        "--alpha=yes",
        "--loop-file=inf",
        "--keep-open=always",
        "--hr-seek=no",
        "--vf=format=rgba",
        "--no-keepaspect",
        "--deinterlace=no"
        "--input-default-bindings=no" 
        "--no-input-terminal"

    ]
    
    current_loop_proc = subprocess.Popen(args)
    return current_loop_proc

def play_overlay():
    """Joue la vidéo de superposition"""
    global current_language
    
    once_video = VIDEOS[current_language]["once"]
    print(f"[OVERLAY] Déclenchement de la vidéo temporaire ({current_language})...")
    
    # Arguments pour mpv en mode superposition
    args = [
        "mpv", once_video,
        "--fs",
        "--mute",
        "--no-terminal",
        "--ontop",
        "--no-border",
        "--geometry=0:0",
        "--alpha=yes",
        "--vf=format=rgba,fade=t=in:st=0:d=1,fade=t=out:st=5:d=1"
        "--input-default-bindings=no"
        "--no-input-terminal"
    ]
    
    subprocess.run(args)
    print("[OVERLAY] Vidéo temporaire terminée.")

def button_mode_loop():
    """Boucle principale pour le mode bouton"""
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.HIGH:
            print("[BUTTON] Bouton appuyé.")
            play_overlay()
            time.sleep(0.5)
        time.sleep(0.001)

def encoder_mode_loop():
    """Boucle principale pour le mode encodeur rotatif"""
    encoder_count = 0
    last_clk = GPIO.input(CLK_PIN)
    last_rotation_time = time.time()
    
    while True:
        clk_state = GPIO.input(CLK_PIN)
        dt_state = GPIO.input(DT_PIN)
        
        if clk_state != last_clk:
            last_rotation_time = time.time()
            if dt_state != clk_state:
                encoder_count += 1
            # else:
            #     encoder_count -= 1
            
            print(f"[ENCODER] Compteur : {encoder_count}")
            
            if encoder_count >= ENCODER_THRESHOLD:
                print("[ENCODER] Seuil atteint !")
                play_overlay()
                encoder_count = 0
                last_rotation_time = time.time()
            
            last_clk = clk_state
        
        # Réinitialisation après inactivité
        if time.time() - last_rotation_time > ENCODER_RESET_TIMEOUT and encoder_count != 0:
            print("[ENCODER] Inactivité détectée. Réinitialisation du compteur.")
            encoder_count = 0
        
        time.sleep(0.001)

def handle_language_change(new_language):
    """Gère le changement de langue"""
    global current_language
    
    print(f"[LANGUAGE] Changement vers {new_language}")
    current_language = new_language
    
    # Redémarrer la vidéo en boucle avec la nouvelle langue
    start_loop()

def signal_handler(sig, frame):
    """Gère l'arrêt propre du programme"""
    print("[EXIT] Signal d'arrêt reçu. Nettoyage...")
    keyboard.stop()

    if current_loop_proc:
        try:
            current_loop_proc.terminate()
            time.sleep(0.5)  # Attendre que le processus se termine
        except:
            pass
    
    GPIO.cleanup()
    print("[EXIT] Nettoyage terminé.")
    sys.exit(0)

def main():
    """Fonction principale"""
    global current_loop_proc
    
    try:
        # Gestion des signaux d'arrêt
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Configuration GPIO
        setup_gpio()
        
        # Démarrage du gestionnaire de clavier
        keyboard.start(handle_language_change)
        
        # Lancement de la vidéo en boucle
        print("[INIT] Lancement de la vidéo de boucle...")
        current_loop_proc = start_loop()
        
        # Boucle principale selon le mode
        if MODE == "button":
            button_mode_loop()
        elif MODE == "encoder":
            encoder_mode_loop()
            
    except KeyboardInterrupt:
        print("[EXIT] Interruption clavier détectée. Arrêt du script...")
    finally:
        # Nettoyage
        keyboard.stop()
        if current_loop_proc:
            current_loop_proc.terminate()
        GPIO.cleanup()
        print("[EXIT] Nettoyage terminé.")

if __name__ == "__main__":
    main()