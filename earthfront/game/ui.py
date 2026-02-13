import pygame
import pygame_gui
from earthfront.utils.logger import Logger
logger = Logger()

class RoundedButton:
    """Bouton personnalisé avec coins arrondis"""

    def __init__(self, pos, size, icon_path=None, corner_radius=12):
        self.rect = pygame.Rect(pos[0], pos[1], size, size)
        self.size = size
        self.corner_radius = corner_radius
        self.is_hovered = False
        self.is_pressed = False
        self.active = False

        # Couleurs par défaut (peuvent être modifiées)
        self.color_normal = (70, 70, 90)
        self.color_hover = (90, 90, 110)
        self.color_active = (34, 139, 34)
        self.color_active_hover = (50, 200, 50)

        # Charger l'icône
        self.icon = None
        if icon_path:
            try:
                original_icon = pygame.image.load(icon_path).convert_alpha()
                padding = 12
                icon_size = size - (padding * 2)
                self.icon = pygame.transform.smoothscale(original_icon, (icon_size, icon_size))
            except Exception as e:
                logger.info(f"Erreur chargement icône: {e}")

    def update(self, mouse_pos, mouse_pressed):
        """Mettre à jour l'état du bouton"""
        self.is_hovered = self.rect.collidepoint(mouse_pos)

        if self.is_hovered and mouse_pressed:
            self.is_pressed = True
        elif self.is_pressed and not mouse_pressed:
            self.is_pressed = False
            if self.is_hovered:
                self.active = not self.active
                return True  # Bouton cliqué

        return False

    def draw(self, screen):
        """Dessiner le bouton avec coins arrondis"""
        # Couleurs selon l'état
        if self.active:
            color = self.color_active_hover if self.is_hovered else self.color_active
        else:
            color = self.color_hover if self.is_hovered else self.color_normal

        # Dessiner le rectangle avec coins arrondis (sans bordure)
        pygame.draw.rect(screen, color, self.rect, border_radius=self.corner_radius)

        # Dessiner l'icône au centre
        if self.icon:
            icon_alpha = 255 if self.active else 180
            icon_copy = self.icon.copy()
            icon_copy.set_alpha(icon_alpha)
            icon_rect = icon_copy.get_rect(center=self.rect.center)
            screen.blit(icon_copy, icon_rect)

    def set_position(self, x, y):
        """Changer la position du bouton"""
        self.rect.x = x
        self.rect.y = y


class GameUI:
    """Gestion du panel et des boutons overlay"""

    def __init__(self, panel_width, window_size, manager, icon_path=None, quit_icon_path=None):
        logger.info("Initializing GameUI...")
        self.panel_width = panel_width
        self.window_width, self.window_height = window_size
        self.manager = manager

        # Panel à gauche avec style
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((0, 0), (panel_width, self.window_height)),
            starting_height=1,
            manager=manager,
            margins={'left': 0, 'right': 0, 'top': 0, 'bottom': 0}
        )

        # Bouton ressources en bas à droite
        button_size = 64
        margin = 20
        button_x = self.window_width - button_size - margin
        button_y = self.window_height - button_size - margin

        self.button_overlay = RoundedButton(
            pos=(button_x, button_y),
            size=button_size,
            icon_path=icon_path,
            corner_radius=16
        )

        # Bouton quitter en haut à droite
        quit_button_x = self.window_width - button_size - margin
        quit_button_y = margin

        self.button_quit = RoundedButton(
            pos=(quit_button_x, quit_button_y),
            size=button_size,
            icon_path=quit_icon_path,
            corner_radius=16
        )
        # Le bouton quit est toujours rouge
        self.button_quit.color_normal = (180, 50, 50)
        self.button_quit.color_hover = (220, 70, 70)

        # États des overlays
        self.show_overlay = False
        self.quit_requested = False

    def update(self, mouse_pos, mouse_pressed):
        """Mettre à jour le bouton personnalisé"""
        overlay_changed = False
        quit_clicked = False

        # Mettre à jour le bouton ressources
        if self.button_overlay.update(mouse_pos, mouse_pressed):
            self.show_overlay = self.button_overlay.active
            overlay_changed = True

        # Mettre à jour le bouton quit
        if self.button_quit.update(mouse_pos, mouse_pressed):
            quit_clicked = True

        return overlay_changed, quit_clicked

    def draw_button(self, screen):
        """Dessiner les boutons personnalisés"""
        self.button_overlay.draw(screen)
        self.button_quit.draw(screen)

    def resize(self, new_width, new_height):
        """Mettre à jour le panel et les boutons flottants lors du resize"""
        self.window_width = new_width
        self.window_height = new_height

        # Redimensionner le panel
        self.panel.set_dimensions((self.panel_width, new_height))
        self.panel.rebuild()

        # Repositionner les boutons
        button_size = 64
        margin = 20

        # Bouton ressources (bas droite)
        button_x = new_width - button_size - margin
        button_y = new_height - button_size - margin
        self.button_overlay.set_position(button_x, button_y)

        # Bouton quit (haut droite)
        quit_button_x = new_width - button_size - margin
        quit_button_y = margin
        self.button_quit.set_position(quit_button_x, quit_button_y)