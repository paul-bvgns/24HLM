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
        self.video_playing = False  # Ajout d'une variable pour vérifier si une vidéo est en cours

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
            if GPIO.input(BUTTON_PIN) == GPIO.HIGH and not self.video_playing:
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
                    if count >= ENCODER_THRESHOLD and not self.video_playing:
                        print("[ENCODER] Seuil atteint. Lancement vidéo temporaire.")
                        self.overlay_requested = True
                        count = 0
                last_clk = clk

            if time.time() - last_time > ENCODER_RESET_TIMEOUT and count != 0:
                print("[ENCODER] Inactivité détectée. Reset.")
                count = 0

            time.sleep(0.01)

    def play_video(self, path, loop=False):
        self.video_playing = True  # On commence à lire la vidéo

        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            print(f"[ERREUR] Impossible d'ouvrir : {path}")
            self.video_playing = False  # On réinitialise dès qu'on sort de la lecture
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
                cap.release()
                self.play_video(VIDEOS[self.current_language]["once"], loop=False)
                cap = cv2.VideoCapture(path)  # Redémarre la boucle

            self.clock.tick(30)

        cap.release()
        self.video_playing = False  # La vidéo est terminée, réinitialisation du verrou

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                key = event.unicode
                if key == 'q':
                    print("[EXIT] Quitter")
                    self.running = False
                elif key == '0' and not self.video_playing:
                    print("[ACTION] Touche 0 → vidéo temporaire")
                    self.overlay_requested = True
                elif key in {'1', '2', '3', '4'} and not self.video_playing:
                    lang_map = {'1': 'fr', '2': 'it', '3': 'de', '4': 'en'}
                    new_lang = lang_map[key]
                    if new_lang != self.current_language:
                        print(f"[LANGUE] Passage de {self.current_language} à {new_lang}")
                        self.current_language = new_lang
                        raise StopIteration  # Quitte la lecture en boucle pour recharger

    def run(self):
        try:
            while self.running:
                self.play_video(VIDEOS[self.current_language]["loop"], loop=True)
        except StopIteration:
            self.run()
        finally:
            GPIO.cleanup()
            pygame.quit()
            print("[EXIT] Nettoyage terminé.")
