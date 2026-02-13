import pygame
import pygame_gui
from pygame_gui.elements import UIWindow, UIButton, UIHorizontalSlider, UILabel, UIDropDownMenu
from utils.data_handler import DataManager
from utils.logger import Logger
logger = Logger()

class SettingsPanel:
    """Panneau de paramètres du jeu"""

    def __init__(self, manager, window_size, config):
        logger.info("Initializing SettingsPanel...")
        self.manager = manager
        self.window_width, self.window_height = window_size
        self.config = config
        self.window = None
        self.is_visible = False

        # Éléments UI
        self.elements = {}

    def show(self):
        """Afficher le panneau de paramètres"""
        if self.window is not None:
            return

        self.is_visible = True

        # Dimensions du panneau
        panel_width = 500
        panel_height = 450
        panel_x = (self.window_width - panel_width) // 2
        panel_y = (self.window_height - panel_height) // 2

        # Créer la fenêtre principale
        self.window = UIWindow(
            rect=pygame.Rect(panel_x, panel_y, panel_width, panel_height),
            manager=self.manager,
            window_display_title="Paramètres",
            object_id="#settings_window",
            resizable=False
        )

        # Conteneur interne pour les éléments
        margin = 20
        y_pos = margin
        label_width = 200
        control_width = 220
        row_height = 50

        # === AFFICHAGE ===
        # Titre section
        UILabel(
            relative_rect=pygame.Rect(margin, y_pos, panel_width - 2 * margin, 30),
            text="AFFICHAGE",
            manager=self.manager,
            container=self.window,
            object_id="#section_title"
        )
        y_pos += 40

        # FPS - Label
        UILabel(
            relative_rect=pygame.Rect(margin, y_pos + 10, label_width, 30),
            text="Afficher les FPS:",
            manager=self.manager,
            container=self.window
        )

        # FPS - Options
        fps_options = ["Oui", "Non"]
        self.elements['fps_toggle'] = UIDropDownMenu(
            options_list=fps_options,
            starting_option="Oui" if self.config.show_fps else "Non",
            relative_rect=pygame.Rect(margin + label_width, y_pos + 5, control_width, 35),
            manager=self.manager,
            container=self.window
        )
        y_pos += row_height

        # Limite FPS - Label
        UILabel(
            relative_rect=pygame.Rect(margin, y_pos + 10, label_width, 30),
            text="Limite FPS:",
            manager=self.manager,
            container=self.window
        )

        # Limite FPS - Dropdown
        fps_options = ["30", "60", "120", "144", "Illimité"]
        current_fps = str(self.config.fps) if self.config.fps > 0 else "Illimité"
        self.elements['fps_limit'] = UIDropDownMenu(
            options_list=fps_options,
            starting_option=current_fps,
            relative_rect=pygame.Rect(margin + label_width, y_pos + 5, control_width, 35),
            manager=self.manager,
            container=self.window
        )
        y_pos += row_height

        # Mode plein écran - Label
        UILabel(
            relative_rect=pygame.Rect(margin, y_pos + 10, label_width, 30),
            text="Plein écran:",
            manager=self.manager,
            container=self.window
        )

        # Mode plein écran - Options
        fullscreen_options = ["Oui", "Non"]
        self.elements['full_screen'] = UIDropDownMenu(
            options_list=fullscreen_options,
            starting_option="Oui" if self.config.full_screen else "Non",
            relative_rect=pygame.Rect(margin + label_width, y_pos + 5, control_width, 35),
            manager=self.manager,
            container=self.window
        )
        y_pos += row_height + 10

        # === INTERFACE ===
        # Titre section
        UILabel(
            relative_rect=pygame.Rect(margin, y_pos, panel_width - 2 * margin, 30),
            text="INTERFACE",
            manager=self.manager,
            container=self.window,
            object_id="#section_title"
        )
        y_pos += 40

        # Largeur du panneau - Label
        UILabel(
            relative_rect=pygame.Rect(margin, y_pos, label_width, 30),
            text=f"Largeur panneau: {self.config.panel_width}px",
            manager=self.manager,
            container=self.window,
            object_id="#panel_width_label"
        )
        self.elements['panel_width_label'] = UILabel(
            relative_rect=pygame.Rect(margin, y_pos, label_width, 30),
            text=f"Largeur panneau: {self.config.panel_width}px",
            manager=self.manager,
            container=self.window,
            object_id="#panel_width_label"
        )

        # Largeur du panneau - Slider
        self.elements['panel_width'] = UIHorizontalSlider(
            relative_rect=pygame.Rect(margin + label_width, y_pos + 5, control_width, 25),
            start_value=self.config.panel_width,
            value_range=(120, 400),
            manager=self.manager,
            container=self.window
        )
        y_pos += row_height + 20

        # === BOUTONS ===
        button_width = 120
        button_height = 40
        button_spacing = 15
        buttons_y = panel_height - button_height - 60

        # Bouton Appliquer
        self.elements['apply_button'] = UIButton(
            relative_rect=pygame.Rect(
                margin,
                buttons_y,
                button_width,
                button_height
            ),
            text="Appliquer",
            manager=self.manager,
            container=self.window
        )

        # Bouton Réinitialiser
        self.elements['reset_button'] = UIButton(
            relative_rect=pygame.Rect(
                margin + button_width + button_spacing,
                buttons_y,
                button_width,
                button_height
            ),
            text="Réinitialiser",
            manager=self.manager,
            container=self.window
        )

        # Bouton Fermer
        self.elements['close_button'] = UIButton(
            relative_rect=pygame.Rect(
                panel_width - margin - button_width - 15,
                buttons_y,
                button_width,
                button_height
            ),
            text="Fermer",
            manager=self.manager,
            container=self.window
        )

        # Appliquer les styles
        self._apply_styles()

    def _apply_styles(self):
        """Appliquer les styles personnalisés aux boutons"""
        # Bouton Appliquer - Vert
        self.elements['apply_button'].colours['normal_bg'] = pygame.Color(34, 139, 34)
        self.elements['apply_button'].colours['hovered_bg'] = pygame.Color(50, 200, 50)
        self.elements['apply_button'].rebuild()

        # Bouton Réinitialiser - Orange
        self.elements['reset_button'].colours['normal_bg'] = pygame.Color(200, 140, 50)
        self.elements['reset_button'].colours['hovered_bg'] = pygame.Color(230, 160, 70)
        self.elements['reset_button'].rebuild()

        # Bouton Fermer - Rouge
        self.elements['close_button'].colours['normal_bg'] = pygame.Color(180, 50, 50)
        self.elements['close_button'].colours['hovered_bg'] = pygame.Color(220, 70, 70)
        self.elements['close_button'].rebuild()

    def hide(self):
        """Masquer le panneau de paramètres"""
        if self.window:
            self.window.kill()
            self.window = None
            self.elements.clear()
            self.is_visible = False

    def process_event(self, event):
        """Traiter les événements du panneau"""
        if not self.is_visible:
            return None

        if event.type == pygame.USEREVENT:
            # Fermeture de la fenêtre
            if event.user_type == pygame_gui.UI_WINDOW_CLOSE:
                if event.ui_element == self.window:
                    self.hide()
                    return None

            # Boutons
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.elements.get('close_button'):
                    self.hide()
                    return None

                elif event.ui_element == self.elements.get('apply_button'):
                    return self._apply_settings()

                elif event.ui_element == self.elements.get('reset_button'):
                    return self._reset_settings()

            # Slider du panneau
            if event.user_type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                if event.ui_element == self.elements.get('panel_width'):
                    new_value = int(event.value)
                    self.elements['panel_width_label'].set_text(f"Largeur panneau: {new_value}px")

        return None

    def _apply_settings(self):
        logger.info("Applying settings...")
        """Appliquer les nouveaux paramètres"""
        changes = {}

        # FPS Display
        show_fps = self.elements['fps_toggle'].selected_option[0] == "Oui"
        if show_fps != self.config.show_fps:
            changes['show_fps'] = show_fps

        # FPS Limit
        fps_text = self.elements['fps_limit'].selected_option[0]
        fps_value = 0 if fps_text == "Illimité" else int(fps_text)
        if fps_value != self.config.fps:
            changes['fps'] = fps_value

        # Fullscreen
        fullscreen = self.elements['full_screen'].selected_option[0] == "Oui"
        if fullscreen != self.config.full_screen:
            changes['full_screen'] = fullscreen

        # Panel Width
        panel_width = int(self.elements['panel_width'].get_current_value())
        if panel_width != self.config.panel_width:
            changes['panel_width'] = panel_width

        if changes:

            manager = DataManager()
            config = manager.load_config()
            config.update(changes)
            manager.save_config(config)

            return 'apply', changes

        return None

    def _reset_settings(self):
        logger.info("Reset settings")
        """Réinitialiser aux valeurs par défaut"""
        # Réinitialiser les contrôles
        self.elements['fps_toggle'].selected_option = ["Oui"]
        self.elements['fps_limit'].selected_option = ["60"]
        self.elements['full_screen'].selected_option = ["Non"]
        self.elements['panel_width'].set_current_value(180)
        self.elements['panel_width_label'].set_text("Largeur panneau: 180px")

        return ('reset', {
            'show_fps': True,
            'fps': 60,
            'full_screen': False,
            'panel_width': 180
        })

    def toggle(self):
        """Basculer la visibilité du panneau"""
        if self.is_visible:
            self.hide()
        else:
            self.show()

    def resize(self, new_width, new_height):
        """Gérer le redimensionnement de la fenêtre"""
        self.window_width = new_width
        self.window_height = new_height

        # Si le panneau est visible, le recréer au centre
        if self.is_visible:
            self.hide()
            self.show()