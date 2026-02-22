import pygame
import pygame_gui
from pygame_gui.elements import UIWindow, UIButton, UIHorizontalSlider, UILabel, UIDropDownMenu
from utils.data_handler import DataManager
from utils.logger import Logger

logger = Logger()

# Résolutions disponibles (largeur x hauteur)
RESOLUTIONS = [
    "1280x720",
    "1366x768",
    "1600x900",
    "1920x1080",
    "2560x1440",
]


class SettingsPanel:
    """Panneau de paramètres du jeu"""

    def __init__(self, manager, window_size, config, game=None):
        """
        game : référence à l'instance Game (optionnel).
               Si fourni, le toggle plein écran s'applique immédiatement en jeu.
        """
        logger.info("Initializing SettingsPanel...")
        self.manager = manager
        self.window_width, self.window_height = window_size
        self.config = config
        self.game   = game          # None quand utilisé depuis le menu
        self.window = None
        self.is_visible = False
        self.elements = {}

    # ── Affichage ────────────────────────────────────────────────────────────

    def show(self):
        if self.window is not None:
            return

        self.is_visible = True

        panel_width  = 520
        panel_height = 560
        panel_x = (self.window_width  - panel_width)  // 2
        panel_y = (self.window_height - panel_height) // 2

        self.window = UIWindow(
            rect=pygame.Rect(panel_x, panel_y, panel_width, panel_height),
            manager=self.manager,
            window_display_title="Paramètres",
            object_id="#settings_window",
            resizable=False
        )

        margin       = 20
        y_pos        = margin
        label_width  = 200
        control_width= 240
        row_height   = 50

        # ── AFFICHAGE ──────────────────────────────────────────────────────
        self._section_label("AFFICHAGE", panel_width, margin, y_pos)
        y_pos += 40

        # Afficher FPS
        self._row_label("Afficher les FPS:", margin, y_pos, label_width)
        self.elements['fps_toggle'] = UIDropDownMenu(
            options_list=["Oui", "Non"],
            starting_option="Oui" if self.config.show_fps else "Non",
            relative_rect=pygame.Rect(margin + label_width, y_pos + 5, control_width, 35),
            manager=self.manager, container=self.window
        )
        y_pos += row_height

        # Limite FPS
        self._row_label("Limite FPS:", margin, y_pos, label_width)
        current_fps = str(self.config.fps) if self.config.fps > 0 else "Illimité"
        self.elements['fps_limit'] = UIDropDownMenu(
            options_list=["30", "60", "120", "144", "Illimité"],
            starting_option=current_fps,
            relative_rect=pygame.Rect(margin + label_width, y_pos + 5, control_width, 35),
            manager=self.manager, container=self.window
        )
        y_pos += row_height

        # Plein écran
        self._row_label("Plein écran:", margin, y_pos, label_width)
        self.elements['full_screen'] = UIDropDownMenu(
            options_list=["Oui", "Non"],
            starting_option="Oui" if self.config.full_screen else "Non",
            relative_rect=pygame.Rect(margin + label_width, y_pos + 5, control_width, 35),
            manager=self.manager, container=self.window
        )
        y_pos += row_height

        # Résolution
        self._row_label("Résolution:", margin, y_pos, label_width)
        current_res = f"{self.config.window_width}x{self.config.window_height}"
        if current_res not in RESOLUTIONS:
            current_res = RESOLUTIONS[0]
        self.elements['resolution'] = UIDropDownMenu(
            options_list=RESOLUTIONS,
            starting_option=current_res,
            relative_rect=pygame.Rect(margin + label_width, y_pos + 5, control_width, 35),
            manager=self.manager, container=self.window
        )
        y_pos += row_height + 10

        # ── INTERFACE ──────────────────────────────────────────────────────
        self._section_label("INTERFACE", panel_width, margin, y_pos)
        y_pos += 40

        # Largeur panneau
        self.elements['panel_width_label'] = UILabel(
            relative_rect=pygame.Rect(margin, y_pos, label_width, 30),
            text=f"Largeur panneau: {self.config.panel_width}px",
            manager=self.manager, container=self.window
        )
        self.elements['panel_width'] = UIHorizontalSlider(
            relative_rect=pygame.Rect(margin + label_width, y_pos + 5, control_width, 25),
            start_value=self.config.panel_width,
            value_range=(120, 400),
            manager=self.manager, container=self.window
        )
        y_pos += row_height + 20

        # ── BOUTONS ────────────────────────────────────────────────────────
        btn_w   = 130
        btn_h   = 40
        btn_gap = 12
        btns_y  = panel_height - btn_h - 60

        self.elements['apply_button'] = UIButton(
            relative_rect=pygame.Rect(margin, btns_y, btn_w, btn_h),
            text="Appliquer",
            manager=self.manager, container=self.window
        )
        self.elements['reset_button'] = UIButton(
            relative_rect=pygame.Rect(margin + btn_w + btn_gap, btns_y, btn_w, btn_h),
            text="Réinitialiser",
            manager=self.manager, container=self.window
        )
        self.elements['close_button'] = UIButton(
            relative_rect=pygame.Rect(panel_width - margin - btn_w - 15, btns_y, btn_w, btn_h),
            text="Fermer",
            manager=self.manager, container=self.window
        )

        self._apply_styles()

    def _section_label(self, text, panel_width, margin, y):
        UILabel(
            relative_rect=pygame.Rect(margin, y, panel_width - 2 * margin, 30),
            text=text,
            manager=self.manager, container=self.window,
            object_id="#section_title"
        )

    def _row_label(self, text, margin, y, width):
        UILabel(
            relative_rect=pygame.Rect(margin, y + 10, width, 30),
            text=text,
            manager=self.manager, container=self.window
        )

    def _apply_styles(self):
        self.elements['apply_button'].colours['normal_bg']  = pygame.Color(34, 139, 34)
        self.elements['apply_button'].colours['hovered_bg'] = pygame.Color(50, 200, 50)
        self.elements['apply_button'].rebuild()

        self.elements['reset_button'].colours['normal_bg']  = pygame.Color(200, 140, 50)
        self.elements['reset_button'].colours['hovered_bg'] = pygame.Color(230, 160, 70)
        self.elements['reset_button'].rebuild()

        self.elements['close_button'].colours['normal_bg']  = pygame.Color(180, 50, 50)
        self.elements['close_button'].colours['hovered_bg'] = pygame.Color(220, 70, 70)
        self.elements['close_button'].rebuild()

    def hide(self):
        if self.window:
            self.window.kill()
            self.window = None
            self.elements.clear()
            self.is_visible = False

    # ── Événements ───────────────────────────────────────────────────────────

    def process_event(self, event):
        if not self.is_visible:
            return None

        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_WINDOW_CLOSE:
                if event.ui_element == self.window:
                    self.hide()
                    return None

            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.elements.get('close_button'):
                    self.hide()
                    return None
                elif event.ui_element == self.elements.get('apply_button'):
                    return self._apply_settings()
                elif event.ui_element == self.elements.get('reset_button'):
                    return self._reset_settings()

            if event.user_type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                if event.ui_element == self.elements.get('panel_width'):
                    new_value = int(event.value)
                    self.elements['panel_width_label'].set_text(f"Largeur panneau: {new_value}px")

        return None

    def _apply_settings(self):
        logger.info("Applying settings...")
        changes = {}

        show_fps = self.elements['fps_toggle'].selected_option[0] == "Oui"
        if show_fps != self.config.show_fps:
            changes['show_fps'] = show_fps

        fps_text  = self.elements['fps_limit'].selected_option[0]
        fps_value = 0 if fps_text == "Illimité" else int(fps_text)
        if fps_value != self.config.fps:
            changes['fps'] = fps_value

        fullscreen = self.elements['full_screen'].selected_option[0] == "Oui"
        if fullscreen != self.config.full_screen:
            changes['full_screen'] = fullscreen

        # Résolution
        res_str = self.elements['resolution'].selected_option[0]
        res_w, res_h = map(int, res_str.split("x"))
        if res_w != self.config.window_width or res_h != self.config.window_height:
            changes['window_width']  = res_w
            changes['window_height'] = res_h

        panel_width = int(self.elements['panel_width'].get_current_value())
        if panel_width != self.config.panel_width:
            changes['panel_width'] = panel_width

        if changes:
            dm  = DataManager()
            cfg = dm.load_config()
            cfg.update(changes)
            dm.save_config(cfg)

            # Si on est en jeu et que seul le plein écran / FPS changent,
            # on peut les appliquer immédiatement sans restart
            if self.game is not None:
                self._apply_live(changes)
                # Pas de restart si aucun changement "lourd" (résolution, panel)
                heavy = {'window_width', 'window_height', 'panel_width'}
                if not heavy.intersection(changes.keys()):
                    self.hide()
                    return None  # pas de restart

            return ('apply', changes)

        return None

    def _apply_live(self, changes):
        """Applique immédiatement les changements légers pendant le jeu."""
        if 'show_fps' in changes:
            self.game.show_fps = changes['show_fps']
            self.game.config.show_fps = changes['show_fps']

        if 'fps' in changes:
            self.game.FPS = changes['fps']
            self.game.config.fps = changes['fps']

        if 'full_screen' in changes:
            # On délègue au game qui gère proprement la fenêtre
            if changes['full_screen'] != self.game.config.full_screen:
                self.game.toggle_fullscreen()

    def _reset_settings(self):
        logger.info("Reset settings")
        self.elements['fps_toggle'].selected_option  = ["Oui"]
        self.elements['fps_limit'].selected_option   = ["60"]
        self.elements['full_screen'].selected_option = ["Non"]
        self.elements['resolution'].selected_option  = ["1280x720"]
        self.elements['panel_width'].set_current_value(180)
        self.elements['panel_width_label'].set_text("Largeur panneau: 180px")

        return ('reset', {
            'show_fps': True, 'fps': 60,
            'full_screen': False, 'panel_width': 180,
            'window_width': 1280, 'window_height': 720
        })

    def toggle(self):
        if self.is_visible:
            self.hide()
        else:
            self.show()

    def resize(self, new_width, new_height):
        self.window_width  = new_width
        self.window_height = new_height
        if self.is_visible:
            self.hide()
            self.show()