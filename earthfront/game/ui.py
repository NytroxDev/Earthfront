import pygame
import pygame_gui
from utils.logger import Logger
logger = Logger()

# Définition des ressources avec leur couleur et label
RESOURCES = [
    ("gold",   "Or",      (255, 215,   0)),
    ("iron",   "Fer",     (180, 180, 190)),
    ("copper", "Cuivre",  (200, 100,  40)),
    ("coal",   "Charbon", ( 60,  60,  70)),
    ("oil",    "Pétrole", (120,  80,  30)),
    ("wood",   "Bois",    ( 50, 160,  50)),
    ("water",  "Eau",     ( 30, 144, 255)),
]

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

        # ===== Zone d'affichage des infos chunk =====
        self.chunk_info_label = pygame_gui.elements.UITextBox(
            html_text="<b>Chunk Info</b><br>Cliquez sur une case",
            relative_rect=pygame.Rect(10, 10, panel_width - 20, 300),
            manager=manager,
            container=self.panel
        )

        # ===== Boutons filtres ressources =====
        self.active_filter = None
        self.filter_buttons = {}
        self._filter_just_clicked = None
        self._create_filter_buttons(panel_width, manager)
        # =======================================

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

    def _create_filter_buttons(self, panel_width, manager):
        """Crée les boutons filtres pour chaque ressource dans le panel"""
        margin = 10
        btn_h = 30
        start_y = 350  # sous le chunk_info_label
        label_y = start_y - 22

        # Titre section
        self.filter_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(margin, label_y, panel_width - 20, 20),
            text="— Filtres ressources —",
            manager=manager,
            container=self.panel
        )

        for i, (key, label, color) in enumerate(RESOURCES):
            y = start_y + i * (btn_h + 6)
            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(margin, y, panel_width - 20, btn_h),
                text=label,
                manager=manager,
                container=self.panel,
                object_id=f"#filter_{key}"
            )
            # Teinter légèrement le bouton avec la couleur de la ressource
            btn.colours["normal_bg"]   = pygame.Color(*color, 140)
            btn.colours["hovered_bg"]  = pygame.Color(min(color[0]+40,255), min(color[1]+40,255), min(color[2]+40,255))
            btn.colours["selected_bg"] = pygame.Color(255, 255, 255)   # blanc quand actif
            btn.colours["normal_text"]   = pygame.Color(0, 0, 0)       # texte noir
            btn.colours["hovered_text"]  = pygame.Color(0, 0, 0)
            btn.colours["selected_text"] = pygame.Color(*color)         # texte couleur ressource quand actif
            btn.rebuild()
            self.filter_buttons[key] = btn

    def _apply_btn_style(self, key, active):
        """Applique le style visuel d'un bouton filtre selon son état actif/inactif"""
        btn = self.filter_buttons[key]
        color = next(c for k, _, c in RESOURCES if k == key)
        if active:
            btn.colours["normal_bg"]     = pygame.Color(150, 150, 150)
            btn.colours["hovered_bg"]    = pygame.Color(200, 200, 200)
            btn.colours["selected_bg"]   = pygame.Color(150, 150, 150)
            btn.colours["normal_text"]   = pygame.Color(*color)
            btn.colours["hovered_text"]  = pygame.Color(*color)
            btn.colours["selected_text"] = pygame.Color(*color)
        else:
            btn.colours["normal_bg"]     = pygame.Color(*color, 140)
            btn.colours["hovered_bg"]    = pygame.Color(min(color[0]+40,255), min(color[1]+40,255), min(color[2]+40,255))
            btn.colours["selected_bg"]   = pygame.Color(*color, 140)
            btn.colours["normal_text"]   = pygame.Color(0, 0, 0)
            btn.colours["hovered_text"]  = pygame.Color(0, 0, 0)
            btn.colours["selected_text"] = pygame.Color(0, 0, 0)
        btn.rebuild()

    def check_filter_event(self, event):
        """
        Vérifie si un event correspond à un clic sur un bouton filtre.
        Retourne la clé de la ressource active, ou None si désactivé.
        """
        if event.type != pygame_gui.UI_BUTTON_PRESSED:
            return None
        for key, btn in self.filter_buttons.items():
            if event.ui_element == btn:
                if self.active_filter == key:
                    # Désactiver
                    self.active_filter = None
                    self._apply_btn_style(key, active=False)
                else:
                    # Désactiver l'ancien
                    if self.active_filter:
                        self._apply_btn_style(self.active_filter, active=False)
                    # Activer le nouveau
                    self.active_filter = key
                    self._apply_btn_style(key, active=True)
                return self.active_filter
        return None

    def update_chunk_info(self, chunk_data):
        """Met à jour l'affichage des infos du chunk"""
        if chunk_data is None:
            html = "<b>Chunk Info</b><br>Cliquez sur une case"
        else:
            html = f"""
            <b>Chunk ({chunk_data.position[0]}, {chunk_data.position[1]})</b><br>
            <font color='#FFD700'>Or: {chunk_data.gold}</font>
            <font color='#C0C0C0'>Fer: {chunk_data.iron}</font>
            <font color='#FF8C00'>Cuivre: {chunk_data.copper}</font>
            <font color='#000000'>Charbon: {chunk_data.coal}</font>
            <font color='#8B4513'>Pétrole: {chunk_data.oil}</font>
            <font color='#228B22'>Bois: {chunk_data.wood}</font>
            <font color='#1E90FF'>Eau: {chunk_data.water}</font>
            """

        self.chunk_info_label.html_text = html
        self.chunk_info_label.rebuild()

    def toggle_grid_button(self):
        """Basculer l'état actif du bouton grille"""
        self.button_overlay.active = not self.button_overlay.active
        self.show_overlay = self.button_overlay.active

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

        # Reconstruire les boutons filtres (ils sont dans le panel)
        for btn in self.filter_buttons.values():
            btn.rebuild()

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