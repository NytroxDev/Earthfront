import pygame
import pygame_gui
from earthfront.game.settings import SettingsPanel


class MainMenu:
    """Menu d'accueil du jeu"""

    def __init__(self, screen, manager, config):

        self.config = config

        self.restart = False

        self.screen = screen
        self.manager = manager
        self.running = True
        self.start_game = False

        # Dimensions
        self.width = screen.get_width()
        self.height = screen.get_height()

        # Couleurs
        self.bg_color = (20, 20, 30)
        self.title_color = (255, 215, 0)

        # Fonts
        self.title_font = pygame.font.Font(None, 100)
        self.subtitle_font = pygame.font.Font(None, 40)

        # Panneau de paramètres
        self.settings_panel = SettingsPanel(self.manager, (self.width, self.height), self.config)

        # Créer les éléments UI
        self.create_ui()

    def create_ui(self):
        """Créer les éléments du menu"""
        button_width = 300
        button_height = 60
        button_spacing = 20
        center_x = self.width // 2 - button_width // 2
        start_y = self.height // 2 - 50

        # Bouton Jouer
        self.play_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (center_x, start_y),
                (button_width, button_height)
            ),
            text="JOUER",
            manager=self.manager
        )

        # Bouton Options
        self.options_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (center_x, start_y + button_height + button_spacing),
                (button_width, button_height)
            ),
            text="OPTIONS",
            manager=self.manager
        )

        # Bouton Quitter
        self.quit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (center_x, start_y + (button_height + button_spacing) * 2),
                (button_width, button_height)
            ),
            text="QUITTER",
            manager=self.manager
        )

        # Style des boutons
        self._style_buttons()

    def _style_buttons(self):
        """Appliquer un style personnalisé aux boutons"""
        # Bouton Jouer - Vert
        self.play_button.colours['normal_bg'] = pygame.Color(34, 139, 34)
        self.play_button.colours['hovered_bg'] = pygame.Color(50, 200, 50)
        self.play_button.colours['selected_bg'] = pygame.Color(34, 139, 34)

        # Bouton Options - Bleu
        self.options_button.colours['normal_bg'] = pygame.Color(50, 100, 180)
        self.options_button.colours['hovered_bg'] = pygame.Color(70, 120, 220)
        self.options_button.colours['selected_bg'] = pygame.Color(50, 100, 180)

        # Bouton Quitter - Rouge
        self.quit_button.colours['normal_bg'] = pygame.Color(180, 50, 50)
        self.quit_button.colours['hovered_bg'] = pygame.Color(220, 70, 70)
        self.quit_button.colours['selected_bg'] = pygame.Color(180, 50, 50)

        self.play_button.rebuild()
        self.options_button.rebuild()
        self.quit_button.rebuild()

    def handle_events(self, clock):
        """Gérer les événements du menu"""
        time_delta = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Si le panneau de paramètres est ouvert, le fermer
                    if self.settings_panel.is_visible:
                        self.settings_panel.hide()
                    else:
                        self.running = False
                elif event.key == pygame.K_RETURN:
                    self.start_game = True
                    self.running = False

            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.w, event.h
                self.manager.set_window_resolution((event.w, event.h))
                self.settings_panel.resize(event.w, event.h)
                self._recreate_ui()

            elif event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.play_button:
                        self.start_game = True
                        self.running = False
                    elif event.ui_element == self.options_button:
                        self.settings_panel.toggle()
                    elif event.ui_element == self.quit_button:
                        self.running = False

            # Traiter les événements du panneau de paramètres
            result = self.settings_panel.process_event(event)
            if result:
                action, changes = result
                if action == 'apply':
                    print(f"Paramètres appliqués: {changes}")
                    self.restart = True
                    self.running = False
                elif action == 'reset':
                    print(f"Paramètres réinitialisés: {changes}")

            self.manager.process_events(event)

        self.manager.update(time_delta)

    def _recreate_ui(self):
        """Recréer l'UI après un resize"""
        self.play_button.kill()
        self.options_button.kill()
        self.quit_button.kill()
        self.create_ui()

    def render(self):
        """Afficher le menu"""
        # Background avec dégradé
        self.screen.fill(self.bg_color)

        # Effet de dégradé subtil
        for i in range(self.height // 2):
            alpha = int(30 * (1 - i / (self.height // 2)))
            color = (self.bg_color[0] + alpha, self.bg_color[1] + alpha, self.bg_color[2] + alpha)
            pygame.draw.line(self.screen, color, (0, i), (self.width, i))

        # Titre
        title_text = self.title_font.render("Earthfront", True, self.title_color)
        title_rect = title_text.get_rect(center=(self.width // 2, self.height // 4 - 20))

        # Ombre du titre
        shadow_text = self.title_font.render("Earthfront", True, (0, 0, 0))
        shadow_rect = shadow_text.get_rect(center=(self.width // 2 + 4, self.height // 4 - 16))
        self.screen.blit(shadow_text, shadow_rect)
        self.screen.blit(title_text, title_rect)

        # Sous-titre avec plus d'espace
        subtitle_text = self.subtitle_font.render("------------", True, (200, 200, 200))
        subtitle_rect = subtitle_text.get_rect(center=(self.width // 2, self.height // 4 + 60))
        self.screen.blit(subtitle_text, subtitle_rect)

        # Version
        version_font = pygame.font.Font(None, 24)
        version_text = version_font.render("v1.0", True, (100, 100, 100))
        self.screen.blit(version_text, (self.width - 60, self.height - 30))

        # UI Manager
        self.manager.draw_ui(self.screen)
        pygame.display.flip()

    def run(self):
        """Boucle principale du menu"""
        clock = pygame.time.Clock()

        while self.running:
            self.handle_events(clock)
            self.render()

        # Nettoyer les éléments UI du menu
        self.play_button.kill()
        self.options_button.kill()
        self.quit_button.kill()
        self.settings_panel.hide()

        return self.start_game, self.restart
