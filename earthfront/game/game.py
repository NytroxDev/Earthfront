"""
Classe principale du jeu - Version modulaire
"""
import pygame
import pygame_gui
from utils.path_manager import Images, check_path
from .camera import Camera
from .ui import GameUI
from .menu import MainMenu
from .grid_manager import GridManager
from .event_handler import EventHandler
from .renderer import Renderer
from .database_handler import DatabaseHandler
from utils.data_handler import DataManager
from utils.logger import Logger

logger = Logger()


# noinspection PyBroadException
class Game:
    """Classe principale du jeu - coordonne tous les modules"""

    def __init__(self):
        logger.info("Initializing class Game...")

        # Initialisation de base
        self._init_paths()
        self._init_pygame()
        self._init_config()
        self._init_screen()

        # Afficher le menu
        if not self._show_menu():
            return

        # Initialiser les composants du jeu
        self._init_ui()
        self._init_map()
        self._init_camera()
        self._init_modules()
        self._init_variables()

        logger.info("Game initialized successfully")

    # ===== INITIALISATION =====

    def _init_paths(self):
        """Vérifie les chemins des ressources"""
        logger.info("Checking paths...")
        check_path()

    def _init_pygame(self):
        """Initialise pygame"""
        logger.info("Initializing pygame...")
        pygame.init()

    def _init_config(self):
        """Charge la configuration"""
        logger.info("Initializing DataManager...")
        self.data_manager = DataManager()

        logger.info("Loading config...")
        self.config = self.data_manager.load_config()

        if self.config is None:
            logger.error("Config not found!")
            pygame.quit()
            import sys
            sys.exit()

        self.WINDOW_WIDTH = self.config.window_width
        self.WINDOW_HEIGHT = self.config.window_height
        self.PANEL_WIDTH = self.config.panel_width
        self.FPS = self.config.fps
        self.COLOR_BG = (20, 20, 30)
        self.show_fps = self.config.show_fps

    def _init_screen(self):
        """Initialise l'écran"""
        logger.info("Initializing screen...")
        flags = pygame.RESIZABLE if not self.config.full_screen else pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT), flags)
        pygame.display.set_caption("Earthfront - v1.0")

    def _show_menu(self):
        """Affiche le menu principal"""
        logger.info("Initializing pygame_gui...")
        self.manager = pygame_gui.UIManager((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))

        logger.info("Initializing MainMenu...")
        menu = MainMenu(self.screen, self.manager, self.config)
        should_start, need_restart = menu.run()

        logger.info(f"MainMenu result: should_start={should_start}, need_restart={need_restart}")

        self.need_restart = need_restart

        if need_restart:
            logger.info("Restarting game...")
            return False

        if not should_start:
            logger.info("Game not started, exiting...")
            pygame.quit()
            return False

        # Recréer le manager pour le jeu
        self.manager = pygame_gui.UIManager((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        return True

    def _init_ui(self):
        """Initialise l'interface utilisateur"""
        logger.info("Initializing GameUI...")
        try:
            self.ui = GameUI(
                self.PANEL_WIDTH,
                (self.WINDOW_WIDTH, self.WINDOW_HEIGHT),
                self.manager,
                icon_path=Images.ICON_RESOURCES,
                quit_icon_path=Images.ICON_QUIT
            )
        except:
            logger.warning("Icon not found, using text button")
            self.ui = GameUI(
                self.PANEL_WIDTH,
                (self.WINDOW_WIDTH, self.WINDOW_HEIGHT),
                self.manager,
                icon_path=None,
                quit_icon_path=None
            )

    def _init_map(self):
        """Charge la carte"""
        logger.info("Loading images...")
        self.map_image = pygame.image.load(Images.CARTES).convert()
        self.map_width = self.map_image.get_width()
        self.map_height = self.map_image.get_height()

    def _init_camera(self):
        """Initialise la caméra"""
        logger.info("Initializing camera...")
        map_viewport_width = self.WINDOW_WIDTH - self.PANEL_WIDTH
        map_viewport_height = self.WINDOW_HEIGHT
        self.camera = Camera(
            self.map_width,
            self.map_height,
            map_viewport_width,
            map_viewport_height
        )

    def _init_modules(self):
        """Initialise les modules (grille, events, rendu)"""
        logger.info("Initializing modules...")

        # Gestionnaire de grille
        self.grid_manager: GridManager = GridManager(self.map_width, self.map_height, cell_size=10)

        # Gestionnaire d'événements
        self.event_handler = EventHandler(self)

        # Moteur de rendu
        self.renderer = Renderer(self)

        self.data_handler = DatabaseHandler(self)

    def _init_variables(self):
        """Initialise les variables du jeu"""
        logger.info("Initializing variables...")
        self.clock = pygame.time.Clock()
        self.running = True
        self.map_surface = None
        self.need_redraw = True

    # ===== FONCTIONS PUBLIQUES POUR LA GRILLE =====

    def set_cell_color(self, x, y, color, alpha=180):
        """
        Colorie une cellule de la grille

        Args:
            x (int): Colonne (0-149)
            y (int): Ligne (0-89)
            color (tuple): Couleur RGB (r, g, b)
            alpha (int): Transparence 0-255
        """
        if self.grid_manager.set_cell_color(x, y, color, alpha):
            self.need_redraw = True

    def set_cell_image(self, x, y, image_surface, alpha=255):
        """
        Place une image sur une cellule

        Args:
            x (int): Colonne (0-149)
            y (int): Ligne (0-89)
            image_surface (pygame.Surface): Image à placer
            alpha (int): Transparence 0-255
        """
        if self.grid_manager.set_cell_image(x, y, image_surface, alpha):
            self.need_redraw = True

    def reset_cell(self, x, y):
        """
        Remet une cellule à son état par défaut

        Args:
            x (int): Colonne (0-149)
            y (int): Ligne (0-89)
        """
        self.grid_manager.reset_cell(x, y)
        self.need_redraw = True

    def clear_all_cells(self):
        """Efface toutes les cellules colorées/avec images"""
        self.grid_manager.clear_all_cells()
        self.need_redraw = True

    def get_cell_at_mouse(self, mouse_pos=None):
        """
        Retourne la cellule sous la souris

        Args:
            mouse_pos (tuple): Position de la souris (optionnel, utilise la position actuelle si None)

        Returns:
            tuple: (x, y) de la cellule ou None
        """
        if mouse_pos is None:
            mouse_pos = pygame.mouse.get_pos()
        return self.event_handler.get_cell_at_mouse(mouse_pos)

    def show_grid(self):
        """Affiche la grille"""
        self.grid_manager.show()
        self.need_redraw = True

    def hide_grid(self):
        """Cache la grille"""
        self.grid_manager.hide()
        self.need_redraw = True

    def toggle_grid(self):
        """Bascule l'affichage de la grille"""
        self.grid_manager.toggle_visibility()
        self.need_redraw = True

    def get_grid_stats(self):
        """Retourne les statistiques de la grille"""
        return self.grid_manager.get_stats()

    # ===== BOUCLE PRINCIPALE =====

    def run(self):
        """Boucle principale du jeu"""
        logger.info("Running game...")

        if self.need_restart:
            logger.info("Restarting game...")
            return "RESTART"

        if not hasattr(self, "running"):
            logger.info("Game not running, exiting...")
            pygame.quit()
            return "EXIT"

        while self.running:
            # Gérer les événements
            if not self.event_handler.handle_events():
                self.running = False

            # Vérifier si on doit redémarrer
            if self.need_restart:
                logger.info("Restarting game...")
                return "RESTART"

            # Rendu
            self.renderer.render()

        logger.info("Quitting game...")
        pygame.quit()
        return None
