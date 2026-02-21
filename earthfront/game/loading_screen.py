import pygame

# ─────────────────────────────────────────────
#  CONFIGURATION — modifie ces valeurs librement
# ─────────────────────────────────────────────
CONFIG = {
    "title":           "EARTHFRONT",
    "subtitle":        "Chargement de la partie...",
    "bg_color":        (12, 12, 14),        # couleur de fond
    "bar_color":       (60, 180, 100),      # couleur de la barre de progression
    "bar_bg_color":    (30, 30, 34),        # couleur de fond de la barre
    "text_color":      (220, 220, 220),     # couleur du texte principal
    "sub_color":       (100, 100, 110),     # couleur du sous-texte
    "accent_color":    (60, 180, 100),      # couleur de l'accent (ligne déco)
    "bar_width":       500,                 # largeur de la barre
    "bar_height":      4,                   # hauteur de la barre (fin = épuré)
    "font_title_size": 52,
    "font_sub_size":   16,
    "font_tip_size":   14,
    "tips": [                               # astuces affichées aléatoirement
        "Contrôlez les territoires pour gagner des ressources.",
        "Collaborez avec vos alliés pour étendre votre influence.",
        "Chaque territoire a ses propres caractéristiques.",
        "Surveillez les frontières adverses.",
    ]
}
# ─────────────────────────────────────────────


class LoadingScreen:
    """
    Écran de chargement pour Earthfront.

    Utilisation :
        loader = LoadingScreen(screen)
        loader.start()

        # Dans ta boucle de chargement :
        loader.update(progress=0.5, status="Génération de la carte...")
        loader.draw()

        loader.finish()  # anime la fin proprement
    """

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.W, self.H = screen.get_size()
        self.cfg = CONFIG

        self._progress = 0.0          # 0.0 → 1.0
        self._display_progress = 0.0  # progression lissée (animation)
        self._status = self.cfg["subtitle"]
        self._tip = self.cfg["tips"][0]
        self._alpha = 0               # fade-in global
        self._done = False

        self._load_fonts()
        self._pick_tip()

    # ── Setup ──────────────────────────────────────────────────────────────

    def _load_fonts(self):
        pygame.font.init()
        # Utilise la police système disponible ; tu peux remplacer par un .ttf
        self.font_title = pygame.font.SysFont("Segoe UI", self.cfg["font_title_size"], bold=True)
        self.font_sub   = pygame.font.SysFont("Segoe UI", self.cfg["font_sub_size"])
        self.font_tip   = pygame.font.SysFont("Segoe UI", self.cfg["font_tip_size"], italic=True)

    def _pick_tip(self):
        import random
        self._tip = random.choice(self.cfg["tips"])

    # ── Public API ─────────────────────────────────────────────────────────

    def start(self):
        """Appelle ça juste avant ta boucle de chargement."""
        self._alpha = 0
        self._display_progress = 0.0
        self._progress = 0.0
        self._pick_tip()

    def update(self, progress: float, status: str = ""):
        """
        progress : float entre 0.0 et 1.0
        status   : texte à afficher sous la barre
        """
        self._progress = max(0.0, min(1.0, progress))
        if status:
            self._status = status

    def draw(self, dt: float = 0.016):
        """
        À appeler dans ta boucle principale après update().
        dt : delta time en secondes (pour les animations).
        """
        # Fade-in
        if self._alpha < 255:
            self._alpha = min(255, self._alpha + int(255 * dt * 3))

        # Progression lissée
        speed = 2.5
        if self._display_progress < self._progress:
            self._display_progress = min(
                self._progress,
                self._display_progress + (self._progress - self._display_progress) * dt * speed
            )

        # ── Fond ──
        self.screen.fill(self.cfg["bg_color"])

        # ── Ligne déco en haut ──
        accent_rect = pygame.Rect(0, 0, self.W, 2)
        pygame.draw.rect(self.screen, self.cfg["accent_color"], accent_rect)

        # ── Titre ──
        title_surf = self.font_title.render(self.cfg["title"], True, self.cfg["text_color"])
        title_rect = title_surf.get_rect(center=(self.W // 2, self.H // 2 - 80))
        self.screen.blit(title_surf, title_rect)

        # ── Barre de progression ──
        bar_x = (self.W - self.cfg["bar_width"]) // 2
        bar_y = self.H // 2 + 10

        # fond de la barre
        pygame.draw.rect(
            self.screen, self.cfg["bar_bg_color"],
            (bar_x, bar_y, self.cfg["bar_width"], self.cfg["bar_height"]),
            border_radius=4
        )
        # progression
        filled = int(self.cfg["bar_width"] * self._display_progress)
        if filled > 0:
            pygame.draw.rect(
                self.screen, self.cfg["bar_color"],
                (bar_x, bar_y, filled, self.cfg["bar_height"]),
                border_radius=4
            )

        # ── Pourcentage ──
        pct_text = f"{int(self._display_progress * 100)}%"
        pct_surf = self.font_sub.render(pct_text, True, self.cfg["sub_color"])
        pct_rect = pct_surf.get_rect(midright=(bar_x + self.cfg["bar_width"], bar_y - 10))
        self.screen.blit(pct_surf, pct_rect)

        # ── Status ──
        status_surf = self.font_sub.render(self._status, True, self.cfg["sub_color"])
        status_rect = status_surf.get_rect(midleft=(bar_x, bar_y + self.cfg["bar_height"] + 12))
        self.screen.blit(status_surf, status_rect)

        # ── Astuce en bas ──
        tip_label = self.font_tip.render("Astuce : " + self._tip, True, self.cfg["sub_color"])
        tip_rect  = tip_label.get_rect(center=(self.W // 2, self.H - 50))
        self.screen.blit(tip_label, tip_rect)

        # ── Fade-in overlay ──
        if self._alpha < 255:
            fade = pygame.Surface((self.W, self.H))
            fade.fill((0, 0, 0))
            fade.set_alpha(255 - self._alpha)
            self.screen.blit(fade, (0, 0))

        pygame.display.flip()

    def finish(self, fade_duration: float = 0.6):
        """Anime la fin (fade-out) puis retourne."""
        clock = pygame.time.Clock()
        alpha = 0
        while alpha < 255:
            dt = clock.tick(60) / 1000
            alpha = min(255, alpha + int(255 * dt / fade_duration))
            self.draw(dt)
            fade = pygame.Surface((self.W, self.H))
            fade.fill((0, 0, 0))
            fade.set_alpha(alpha)
            self.screen.blit(fade, (0, 0))
            pygame.display.flip()


# ─────────────────────────────────────────────
#  EXEMPLE D'UTILISATION COMPLET
#  (retire ce bloc quand tu intègres dans ton jeu)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((900, 600))
    pygame.display.set_caption("Earthfront — Loading")

    loader = LoadingScreen(screen)
    loader.start()

    # Simule des étapes de chargement
    steps = [
        (0.15, "Initialisation du moteur..."),
        (0.35, "Génération de la carte..."),
        (0.55, "Chargement des territoires..."),
        (0.75, "Placement des ressources..."),
        (0.95, "Finalisation..."),
        (1.00, "Prêt !"),
    ]

    clock = pygame.time.Clock()
    step_index = 0
    step_timer = 0.0
    step_delay = 0.8  # secondes entre chaque étape simulée

    running = True
    while running:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if step_index < len(steps):
            step_timer += dt
            if step_timer >= step_delay:
                step_timer = 0
                progress, status = steps[step_index]
                loader.update(progress, status)
                step_index += 1
        else:
            loader.finish()
            running = False

        loader.draw(dt)

    pygame.quit()