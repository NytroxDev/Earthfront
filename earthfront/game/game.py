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
from utils.database_handler import DatabaseHandler
from utils.data_handler import DataManager
from utils.logger import Logger
from .loading_screen import LoadingScreen
import threading

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
                icon_path=Images.ICON_VIEW_GRID,
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

        # Database handler
        self.data_handler = DatabaseHandler(self)

        # Générer le monde si la BDD est vide
        info = self.data_handler.get_world_info()
        if info['chunk_count'] != 2050:
            logger.info("Monde non généré — lancement de la génération avec écran de chargement")
            self._run_world_generation()
        else:
            logger.info(f"Monde déjà généré ({info['chunk_count']} chunks), skip")


    def _run_world_generation(self):
        """Lance la génération du monde dans un thread et affiche le loading screen."""
        width_chunks  = self.map_width  // 10
        height_chunks = self.map_height // 10
        total         = width_chunks * height_chunks

        logger.info(f"Taille de la carte : {width_chunks}x{height_chunks} chunks ({total} total)")

        # État partagé entre les threads (protégé par un verrou)
        state = {"progress": 0.0, "status": "Initialisation...", "done": False, "error": None}
        lock  = threading.Lock()

        # Callback appelé par generate_world() à chaque chunk inséré
        def on_chunk_generated(count):
            with lock:
                state["progress"] = count / total
                state["status"]   = f"Génération des chunks... ({count}/{total})"

        def generate():
            logger.info("Thread de génération démarré")
            try:
                self.data_handler.generate_world(
                    seed=55,
                    width=width_chunks,
                    height=height_chunks,
                    on_progress=on_chunk_generated,   # ← callback
                )
                logger.info("Thread de génération terminé avec succès")
                with lock:
                    state["progress"] = 1.0
                    state["status"]   = "Terminé !"
                    state["done"]     = True
            except Exception as e:
                logger.error(f"Erreur dans le thread de génération : {e}")
                with lock:
                    state["error"] = str(e)
                    state["done"]  = True

        threading.Thread(target=generate, daemon=True).start()
        logger.info("Thread de génération lancé, démarrage du loading screen")

        loader = LoadingScreen(self.screen)
        loader.start()
        clock  = pygame.time.Clock()

        while True:
            dt = clock.tick(60) / 1000.0

            with lock:
                loader.update(state["progress"], state["status"])
                done  = state["done"]
                error = state["error"]

            loader.draw(dt)

            # Pomper les events pour éviter que la fenêtre freeze
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    logger.info("Fermeture demandée pendant le chargement")
                    pygame.quit()
                    import sys; sys.exit()

            if done:
                break

        loader.finish()

        if error:
            logger.error(f"La génération a échoué : {error}")
        else:
            logger.info("Loading screen terminé, lancement du jeu")

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

    # ===== FILTRES RESSOURCES =====

    def apply_resource_filter(self, resource_key):
        """
        Colorie tous les chunks selon la densité de la ressource donnée.
        resource_key: 'gold', 'iron', 'copper', 'coal', 'oil', 'wood', 'water'
        """
        from game.ui import RESOURCES

        # Couleur associée à la ressource
        color = next((c for k, _, c in RESOURCES if k == resource_key), (255, 255, 255))

        # Récupérer tous les chunks de la BDD
        conn = self.data_handler.conn
        cur = conn.cursor()
        cur.execute(f"SELECT position, {resource_key} FROM chunk")
        rows = cur.fetchall()

        if not rows:
            return

        # Valeur max pour normaliser l'opacité
        max_val = max((row[1] for row in rows), default=1) or 1

        self.grid_manager.clear_all_cells()

        for position_str, value in rows:
            if value <= 0:
                continue
            try:
                x, y = map(int, position_str.split(";"))
            except ValueError:
                continue
            # Opacité proportionnelle à la quantité (30 → 220)
            alpha = int(30 + (value / max_val) * 190)
            self.grid_manager.set_cell_color(x, y, color, alpha)

        self.need_redraw = True
        logger.info(f"Filter applied: {resource_key} ({len(rows)} chunks)")

    def clear_resource_filter(self):
        """Efface le filtre ressource actif"""
        self.grid_manager.clear_all_cells()
        self.need_redraw = True
        logger.info("Resource filter cleared")

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
