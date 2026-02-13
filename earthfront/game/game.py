import pygame
import pygame_gui
from utils.path_manager import Images, check_path
from .camera import Camera
from .ui import GameUI
from .menu import MainMenu
from utils.data_handler import DataManager
from utils.logger import Logger

logger = Logger()


# noinspection PyBroadException
class Game:
    def __init__(self):
        logger.info("Initializing class Game...")

        logger.info("Checking paths...")
        check_path()

        logger.info("Initializing pygame...")
        pygame.init()

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

        logger.info("Initializing screen...")

        self.screen = pygame.display.set_mode(
            (self.WINDOW_WIDTH, self.WINDOW_HEIGHT),
            pygame.RESIZABLE if not self.config.full_screen else pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
        )
        pygame.display.set_caption("Earthfront - v1.0")

        logger.info("Initializing pygame_gui...")
        # Manager GUI
        self.manager = pygame_gui.UIManager((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))

        logger.info("Initializing MainMenu...")
        # Afficher le menu d'abord
        menu = MainMenu(self.screen, self.manager, self.config)
        should_start, need_restart = menu.run()

        logger.info("MainMenu result: should_start = {}, need_restart = {}".format(should_start, need_restart))

        self.need_restart = need_restart

        if need_restart:
            logger.info("Restarting game...")
            return

        if not should_start:
            logger.info("Game not started, exiting...")
            pygame.quit()
            return

        # Recréer le manager pour le jeu
        self.manager = pygame_gui.UIManager((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))

        logger.info("Initializing GameUI...")

        # UI - Essayer avec icône, sinon fallback sur texte
        try:
            self.ui = GameUI(
                self.PANEL_WIDTH,
                (self.WINDOW_WIDTH, self.WINDOW_HEIGHT),
                self.manager,
                icon_path=Images.ICON_RESOURCES,
                quit_icon_path=Images.ICON_QUIT  # Nouveau
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

        # Images – convert pour performances
        logger.info("Loading images...")
        self.map_image = pygame.image.load(Images.CARTES).convert()
        self.map_width = self.map_image.get_width()
        self.map_height = self.map_image.get_height()

        # Caméra (zone de la carte uniquement, pas le panel)
        logger.info("Initializing camera...")
        map_viewport_width = self.WINDOW_WIDTH - self.PANEL_WIDTH
        map_viewport_height = self.WINDOW_HEIGHT
        self.camera = Camera(
            self.map_width,
            self.map_height,
            map_viewport_width,
            map_viewport_height
        )

        # Variables
        logger.info("Initializing variables...")
        self.is_dragging = False
        self.last_mouse_pos = None
        self.clock = pygame.time.Clock()
        self.running = True

        # Cache optimisé - cache multi-niveaux
        logger.info("Initializing cache...")
        self.zoom_cache = {}
        self.current_cache_zoom = None
        self.map_surface = None
        self.need_redraw = True

        # FPS
        self.font = pygame.font.Font(None, 36)
        self.show_fps = self.config.show_fps
        self.fps_update_counter = 0
        self.fps_text_surface = None
        self.last_fps = 0

        # Dernière position de la caméra
        self.last_camera_pos = None

        # Grille de ressources
        self.show_resource_grid = False
        self.grid_surface = None

    def handle_events(self):
        time_delta = self.clock.tick(self.FPS) / 1000.0

        mouse_pos = pygame.mouse.get_pos()
        mouse_buttons = pygame.mouse.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                logger.info("Quitting game...")
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.WINDOW_WIDTH, self.WINDOW_HEIGHT = event.w, event.h
                self.screen = pygame.display.set_mode(
                    (event.w, event.h),
                    pygame.RESIZABLE | pygame.HWSURFACE | pygame.DOUBLEBUF
                )
                self.manager.set_window_resolution((event.w, event.h))

                # Mise à jour du viewport de la caméra
                map_viewport_width = self.WINDOW_WIDTH - self.PANEL_WIDTH
                map_viewport_height = self.WINDOW_HEIGHT
                self.camera.update_viewport_size(map_viewport_width, map_viewport_height)

                # Mise à jour UI
                self.ui.resize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

                # Recréer la surface de la carte
                self.map_surface = pygame.Surface((map_viewport_width, map_viewport_height))

                # Invalidation du cache
                self.zoom_cache.clear()
                self.need_redraw = True

            elif event.type == pygame.MOUSEWHEEL:
                # Ajuster la position de la souris relative à la zone de la carte
                map_mouse_x = mouse_pos[0] - self.PANEL_WIDTH
                map_mouse_y = mouse_pos[1]
                # Seulement si la souris est sur la carte
                if map_mouse_x >= 0:
                    zoom_factor = 1.2 if event.y > 0 else 0.8
                    self.camera.apply_zoom(zoom_factor, (map_mouse_x, map_mouse_y))
                    self.need_redraw = True

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Seulement si on clique sur la carte (pas sur le panel).
                if mouse_pos[0] >= self.PANEL_WIDTH:
                    self.is_dragging = True
                    self.last_mouse_pos = mouse_pos

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.is_dragging = False
                self.last_mouse_pos = None

            self.manager.process_events(event)

        # Mettre à jour le bouton personnalisé
        overlay_changed, quit_clicked = self.ui.update(mouse_pos, mouse_buttons[0])

        if overlay_changed:
            # Basculer l'affichage de la grille
            self.show_resource_grid = not self.show_resource_grid
            self.need_redraw = True

        if quit_clicked:
            self.running = False
            self.need_restart = True

        # Drag carte
        if self.is_dragging and self.last_mouse_pos:
            current_pos = pygame.mouse.get_pos()
            dx = (self.last_mouse_pos[0] - current_pos[0]) / self.camera.zoom
            dy = (self.last_mouse_pos[1] - current_pos[1]) / self.camera.zoom
            self.camera.move(dx, dy)
            self.last_mouse_pos = current_pos
            self.need_redraw = True

        self.manager.update(time_delta)

    def draw_grid(self, surface):
        """Dessine une grille de carrés 10x10px sur toute la carte avec des bordures de 2px"""
        if not self.show_resource_grid:
            return

        # Taille fixe de chaque cellule en pixels monde
        cell_size = 10  # 10x10 pixels

        # Calculer le nombre de lignes et colonnes
        num_cols = self.map_width // cell_size  # 1500 / 10 = 150 colonnes
        num_rows = self.map_height // cell_size  # 900 / 10 = 90 lignes

        # Couleur de la grille
        grid_color = (121, 122, 125, 1)

        # Calculer la région visible pour optimiser le rendu
        top_left = self.camera.screen_to_world((0, 0))
        bottom_right = self.camera.screen_to_world((self.camera.viewport_width, self.camera.viewport_height))

        # Déterminer les indices de début et fin pour les lignes visibles
        start_col = max(0, int(top_left[0] // cell_size) - 1)
        end_col = min(num_cols + 1, int(bottom_right[0] // cell_size) + 2)
        start_row = max(0, int(top_left[1] // cell_size) - 1)
        end_row = min(num_rows + 1, int(bottom_right[1] // cell_size) + 2)

        # Dessiner les lignes verticales
        for i in range(start_col, end_col):
            x = i * cell_size
            world_start = (x, max(0, start_row * cell_size))
            world_end = (x, min(self.map_height, end_row * cell_size))

            screen_start = self.camera.world_to_screen(world_start)
            screen_end = self.camera.world_to_screen(world_end)

            pygame.draw.line(surface, grid_color, screen_start, screen_end, 1)

        # Dessiner les lignes horizontales
        for i in range(start_row, end_row):
            y = i * cell_size
            world_start = (max(0, start_col * cell_size), y)
            world_end = (min(self.map_width, end_col * cell_size), y)

            screen_start = self.camera.world_to_screen(world_start)
            screen_end = self.camera.world_to_screen(world_end)

            pygame.draw.line(surface, grid_color, screen_start, screen_end, 1)

    def get_visible_region(self):
        """Calcule la région visible de la carte en coordonnés mondes"""
        top_left = self.camera.screen_to_world((0, 0))
        bottom_right = self.camera.screen_to_world((self.camera.viewport_width, self.camera.viewport_height))

        margin = 100 / self.camera.zoom

        x1 = max(0, top_left[0] - margin)
        y1 = max(0, top_left[1] - margin)
        x2 = min(self.map_width, bottom_right[0] + margin)
        y2 = min(self.map_height, bottom_right[1] + margin)

        return int(x1), int(y1), int(x2 - x1), int(y2 - y1)

    def draw_ui_overlay(self):
        """Dessine tous les éléments UI par-dessus la carte"""
        # FPS (décalé pour ne pas toucher le bouton quit)
        if self.show_fps and self.fps_text_surface:
            # Décaler à gauche pour éviter le bouton (64px + 20px margin + 10px espace)
            fps_x = self.WINDOW_WIDTH - 120 - 84
            self.screen.blit(self.fps_text_surface, (fps_x, 20))

        # UI Manager
        self.manager.draw_ui(self.screen)

        # Boutons personnalisés avec coins arrondis
        self.ui.draw_button(self.screen)

    def render(self):
        # Mettre à jour le FPS toutes les 15 frames
        self.fps_update_counter += 1
        if self.fps_update_counter >= 15:
            self.fps_update_counter = 0
            fps = int(self.clock.get_fps())
            if fps != self.last_fps:
                self.last_fps = fps
                self.fps_text_surface = self.font.render(f"FPS: {fps}", True, (255, 255, 0))

        camera_pos = (self.camera.x, self.camera.y)

        # Vérifier si on peut skip le rendu de la carte
        # Note: on ne peut pas skip si show_resource_grid a changé ou si la grille est affichée,
        # car la grille dépend de la position de la caméra
        if (not self.need_redraw and
                self.last_camera_pos == camera_pos and
                self.current_cache_zoom == self.camera.zoom and
                self.map_surface is not None and
                not self.show_resource_grid):
            self.screen.fill(self.COLOR_BG)
            self.screen.blit(self.map_surface, (self.PANEL_WIDTH, 0))
            self.draw_ui_overlay()
            pygame.display.flip()
            return

        # Rendu complet nécessaire
        self.screen.fill(self.COLOR_BG)

        # Zone disponible pour la carte
        map_width = self.WINDOW_WIDTH - self.PANEL_WIDTH
        map_height = self.WINDOW_HEIGHT

        # Créer la surface si nécessaire
        if self.map_surface is None or self.map_surface.get_size() != (map_width, map_height):
            self.map_surface = pygame.Surface((map_width, map_height))

        self.map_surface.fill(self.COLOR_BG)

        # Stratégie de rendu selon le zoom
        if self.camera.zoom > 1.5:
            # Gros zoom : extraire et redimensionner seulement la région visible
            visible_region = self.get_visible_region()
            x, y, w, h = visible_region

            if w > 0 and h > 0:
                try:
                    cropped_map = self.map_image.subsurface(pygame.Rect(x, y, w, h))

                    scaled_w = int(w * self.camera.zoom)
                    scaled_h = int(h * self.camera.zoom)

                    scaled_map = pygame.transform.scale(cropped_map, (scaled_w, scaled_h))

                    world_pos = (x, y)
                    screen_pos = self.camera.world_to_screen(world_pos)

                    self.map_surface.blit(scaled_map, screen_pos)

                except ValueError:
                    # Fallback
                    scaled_width = int(self.map_width * self.camera.zoom)
                    scaled_height = int(self.map_height * self.camera.zoom)

                    scaled_map = pygame.transform.scale(self.map_image, (scaled_width, scaled_height))
                    top_left_world = (0, 0)
                    top_left_screen = self.camera.world_to_screen(top_left_world)
                    self.map_surface.blit(scaled_map, top_left_screen)

        else:
            # Petit zoom : utiliser le cache
            zoom_key = round(self.camera.zoom, 2)

            if zoom_key not in self.zoom_cache:
                scaled_width = int(self.map_width * self.camera.zoom)
                scaled_height = int(self.map_height * self.camera.zoom)

                scaled_map = pygame.transform.scale(self.map_image, (scaled_width, scaled_height))

                self.zoom_cache[zoom_key] = scaled_map

                # Limiter la taille du cache
                if len(self.zoom_cache) > 10:
                    oldest = list(self.zoom_cache.keys())[0]
                    del self.zoom_cache[oldest]

            scaled_map = self.zoom_cache[zoom_key]

            top_left_world = (0, 0)
            top_left_screen = self.camera.world_to_screen(top_left_world)

            self.map_surface.blit(scaled_map, top_left_screen)

        # Dessiner la grille de ressources si activée
        if self.show_resource_grid:
            self.draw_grid(self.map_surface)

        # Blitter la surface de la carte sur l'écran
        self.screen.blit(self.map_surface, (self.PANEL_WIDTH, 0))

        # Dessiner tous les éléments UI
        self.draw_ui_overlay()

        pygame.display.flip()

        # Sauvegarder l'état
        self.last_camera_pos = camera_pos
        self.current_cache_zoom = self.camera.zoom
        self.need_redraw = False

    def run(self):
        logger.info("Running game...")
        if self.need_restart:
            logger.info("Restarting game...")
            return "RESTART"

        if not hasattr(self, "running"):
            logger.info("Game not running, exiting...")
            pygame.quit()
            return "EXIT"

        while self.running:
            self.handle_events()
            self.render()
            if self.need_restart:
                logger.info("Restarting game...")
                return "RESTART"

        logger.info("Quitting game...")
        pygame.quit()
        return None