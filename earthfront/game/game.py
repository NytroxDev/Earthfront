"""
Classe principale du jeu - Version modulaire
"""
import pygame
import pygame_gui
from utils.path_manager import Images, check_path
from .camera import Camera
from .ui import GameUI
from .menu import MainMenu
from game.ui import RESOURCES
from .grid_manager import GridManager
from .event_handler import EventHandler
from .renderer import Renderer
from utils.database_handler import DatabaseHandler
from utils.data_handler import DataManager, Config
from utils.logger import Logger
from .loading_screen import LoadingScreen
import threading

logger = Logger()


class Game:
    """Classe principale du jeu - coordonne tous les modules"""

    def __init__(self, screen: pygame.Surface, config: Config):
        logger.info("Initializing class Game...")

        self.screen = screen
        self.config = config
        self.need_restart = False
        self._should_exit = False  # True = quitter le jeu complètement

        self._init_paths()
        self._apply_config()

        # Afficher le menu principal
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
        logger.info("Checking paths...")
        check_path()

    def _apply_config(self):
        self.WINDOW_WIDTH  = self.screen.get_width()
        self.WINDOW_HEIGHT = self.screen.get_height()
        self.PANEL_WIDTH   = self.config.panel_width
        self.FPS           = self.config.fps
        self.COLOR_BG      = (20, 20, 30)
        self.show_fps      = self.config.show_fps

    def _show_menu(self):
        """Affiche le menu principal — un seul UIManager créé ici."""
        logger.info("Initializing UIManager for menu...")
        w, h = self.screen.get_size()
        self.manager = pygame_gui.UIManager((w, h))

        logger.info("Initializing MainMenu...")
        menu = MainMenu(self.screen, self.manager, self.config)
        should_start, need_restart = menu.run()

        logger.info(f"MainMenu: should_start={should_start}, need_restart={need_restart}")

        if need_restart:
            # Settings modifiés → on signale un restart à main.py
            self.need_restart = True
            return False

        if not should_start:
            # Bouton Quitter dans le menu → sortie complète
            logger.info("Quitter demandé depuis le menu.")
            self._should_exit = True
            return False

        # Vider l'UI du menu et réutiliser le même manager pour le jeu
        self.manager.clear_and_reset()
        return True

    def _init_ui(self):
        logger.info("Initializing GameUI...")
        try:
            self.ui = GameUI(
                self.PANEL_WIDTH,
                (self.WINDOW_WIDTH, self.WINDOW_HEIGHT),
                self.manager,
                icon_path=Images.ICON_VIEW_GRID,
                quit_icon_path=Images.ICON_QUIT
            )
        except Exception:
            logger.warning("Icon not found, using text button")
            self.ui = GameUI(
                self.PANEL_WIDTH,
                (self.WINDOW_WIDTH, self.WINDOW_HEIGHT),
                self.manager,
                icon_path=None,
                quit_icon_path=None
            )

    def _init_map(self):
        logger.info("Loading images...")
        self.map_image  = pygame.image.load(Images.CARTES).convert()
        self.map_width  = self.map_image.get_width()
        self.map_height = self.map_image.get_height()

    def _init_camera(self):
        logger.info("Initializing camera...")
        map_viewport_width  = self.WINDOW_WIDTH - self.PANEL_WIDTH
        map_viewport_height = self.WINDOW_HEIGHT
        self.camera = Camera(
            self.map_width, self.map_height,
            map_viewport_width, map_viewport_height
        )

    def _init_modules(self):
        logger.info("Initializing modules...")
        self.grid_manager_game = GridManager(self.map_width, self.map_height, cell_size=10)
        self.event_handler     = EventHandler(self)
        self.renderer          = Renderer(self)
        self.data_handler      = DatabaseHandler(self)

        info = self.data_handler.get_world_info()
        if info['chunk_count'] != 2050:
            logger.info("Monde non généré — lancement de la génération")
            self._run_world_generation()
        else:
            logger.info(f"Monde déjà généré ({info['chunk_count']} chunks), skip")

    def _run_world_generation(self):
        width_chunks  = self.map_width  // 10
        height_chunks = self.map_height // 10
        total         = width_chunks * height_chunks

        state = {"progress": 0.0, "status": "Initialisation...", "done": False, "error": None}
        lock  = threading.Lock()

        def on_chunk_generated(count):
            with lock:
                state["progress"] = count / total
                state["status"]   = f"Génération des chunks... ({count}/{total})"

        def generate():
            try:
                self.data_handler.generate_world(
                    seed=55, width=width_chunks, height=height_chunks,
                    on_progress=on_chunk_generated,
                )
                with lock:
                    state["progress"] = 1.0
                    state["status"]   = "Terminé !"
                    state["done"]     = True
            except Exception as e:
                logger.error(f"Erreur génération : {e}")
                with lock:
                    state["error"] = str(e)
                    state["done"]  = True

        threading.Thread(target=generate, daemon=True).start()

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

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    import sys
                    pygame.quit()
                    sys.exit()

            if done:
                break

        loader.finish()
        if error:
            logger.error(f"La génération a échoué : {error}")

    def _init_variables(self):
        logger.info("Initializing variables...")
        self.clock       = pygame.time.Clock()
        self.running     = True
        self.map_surface = None
        self.need_redraw = True

    # ===== PLEIN ÉCRAN EN JEU =====

    def toggle_fullscreen(self):
        """Bascule le plein écran sans recréer de fenêtre pygame."""
        self.config.full_screen = not self.config.full_screen

        if self.config.full_screen:
            flags = pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
            self.screen = pygame.display.set_mode(
                (self.config.window_width, self.config.window_height), flags
            )
        else:
            self.screen = pygame.display.set_mode(
                (self.config.window_width, self.config.window_height), pygame.RESIZABLE
            )

        w, h = self.screen.get_size()
        self.WINDOW_WIDTH  = w
        self.WINDOW_HEIGHT = h
        self.manager.set_window_resolution((w, h))
        self.camera.update_viewport_size(w - self.PANEL_WIDTH, h)
        self.ui.resize(w, h)
        self.map_surface = None
        self.renderer.zoom_cache.clear()
        self.need_redraw = True

        # Sauvegarder dans la config
        dm = DataManager()
        cfg = dm.load_config()
        cfg.full_screen = self.config.full_screen
        dm.save_config(cfg)

        logger.info(f"Fullscreen toggled: {self.config.full_screen}")

    # ===== FONCTIONS PUBLIQUES POUR LA GRILLE =====

    def set_cell_color(self, x, y, color, alpha=180):
        if self.grid_manager_game.set_cell_color(x, y, color, alpha):
            self.need_redraw = True

    def set_cell_image(self, x, y, image_surface, alpha=255):
        if self.grid_manager_game.set_cell_image(x, y, image_surface, alpha):
            self.need_redraw = True

    def reset_cell(self, x, y):
        self.grid_manager_game.reset_cell(x, y)
        self.need_redraw = True

    def clear_all_cells(self):
        self.grid_manager_game.clear_all_cells()
        self.need_redraw = True

    def get_cell_at_mouse(self, mouse_pos=None):
        if mouse_pos is None:
            mouse_pos = pygame.mouse.get_pos()
        return self.event_handler.get_cell_at_mouse(mouse_pos)

    def show_grid(self):
        self.grid_manager_game.show()
        self.need_redraw = True

    def hide_grid(self):
        self.grid_manager_game.hide()
        self.need_redraw = True

    def toggle_grid(self):
        self.grid_manager_game.toggle_visibility()
        self.need_redraw = True

    def get_grid_stats(self):
        return self.grid_manager_game.get_stats()

    # ===== FILTRES RESSOURCES =====

    def apply_resource_filter(self, resource_key):
        color = next((c for k, _, c in RESOURCES if k == resource_key), (255, 255, 255))

        # WHERE > 0 directement en SQL, évite de rapatrier les zéros
        cur = self.data_handler.conn.cursor()
        cur.execute(f"SELECT position, {resource_key} FROM chunk WHERE {resource_key} > 0")
        rows = cur.fetchall()

        if not rows:
            return

        max_val = max(v for _, v in rows) or 1

        # Batch write direct dans grid_cells — évite N set_cell_color
        # et donc N "_overlay_dirty = True" inutiles
        gm = self.grid_manager_game
        gm.grid_cells.clear()

        r, g, b = color
        for position_str, value in rows:
            try:
                x, y = map(int, position_str.split(";"))
            except ValueError:
                continue
            if not (0 <= x < gm.num_cols and 0 <= y < gm.num_rows):
                continue
            alpha = int(30 + (value / max_val) * 190)
            gm.grid_cells[(x, y)] = {'color': (r, g, b), 'alpha': alpha}

        gm._overlay_dirty = True  # un seul dirty à la fin
        self.need_redraw = True
        logger.info(f"Filter applied: {resource_key} ({len(rows)} chunks)")

    def clear_resource_filter(self):
        self.grid_manager_game.clear_all_cells()
        self.need_redraw = True
        logger.info("Resource filter cleared")

    # ===== BOUCLE PRINCIPALE =====

    def run(self):
        """Boucle principale du jeu."""
        logger.info("Running game...")

        # Settings appliqués depuis le menu → restart
        if self.need_restart:
            return "RESTART"

        # Quitter demandé depuis le menu
        if self._should_exit:
            return "EXIT"

        # Le menu n'a pas initialisé le jeu (cas inattendu)
        if not hasattr(self, "running"):
            return "EXIT"

        while self.running:
            if not self.event_handler.handle_events():
                # ESC ou croix en jeu → retour au menu (pas de pygame.quit() !)
                self.running = False
                return None  # main.py reboucle → retour au menu

            if self.need_restart:
                return "RESTART"

            self.renderer.render()

        # Ne JAMAIS appeler pygame.quit() ici — c'est main.py qui gère ça
        return None