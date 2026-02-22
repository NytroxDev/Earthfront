"""
Module de gestion des événements du jeu
"""
import pygame
import pygame_gui
from utils.logger import Logger
from .grid_manager import GridManager

logger = Logger()


class EventHandler:
    """Gère tous les événements du jeu"""

    def __init__(self, game):
        self.game = game
        self.grid_manager: GridManager = self.game.grid_manager_game
        self.is_dragging = False
        self.last_mouse_pos = None
        self.last_cell = None
        self.last_cell_color = None

    def handle_events(self):
        """
        Traite tous les événements pygame.
        Retourne False pour retourner au menu (pas pour quitter pygame).
        """
        time_delta = self.game.clock.tick(self.game.FPS) / 1000.0

        mouse_pos     = pygame.mouse.get_pos()
        mouse_buttons = pygame.mouse.get_pressed()

        for event in pygame.event.get():

            # ── Fermeture / retour au menu ───────────────────────────────
            if event.type == pygame.QUIT:
                logger.info("Fenêtre fermée → retour au menu")
                return False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                logger.info("ESC → retour au menu")
                return False

            # ── Raccourcis clavier ────────────────────────────────────────
            elif event.type == pygame.KEYDOWN:

                # G : toggle grille
                if event.key == pygame.K_g:
                    self.game.grid_manager_game.toggle_visibility()
                    self.game.ui.toggle_grid_button()
                    self.game.need_redraw = True
                    logger.info(f"Grid toggled: {self.game.grid_manager_game.visible}")

                # F11 : toggle plein écran en jeu
                elif event.key == pygame.K_F11:
                    self.game.toggle_fullscreen()

            # ── Redimensionnement ─────────────────────────────────────────
            elif event.type == pygame.VIDEORESIZE:
                self._handle_resize(event)

            # ── Molette (zoom) ────────────────────────────────────────────
            elif event.type == pygame.MOUSEWHEEL:
                self._handle_mousewheel(event, mouse_pos)

            # ── Clics souris ──────────────────────────────────────────────
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_mouse_down(mouse_pos)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                self._handle_mouse_down(mouse_pos, bu3=True)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._handle_mouse_up()

            # ── UI Manager ────────────────────────────────────────────────
            self.game.manager.process_events(event)

            # ── Boutons filtres ressources ────────────────────────────────
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                result = self.game.ui.check_filter_event(event)
                if result is not None:
                    if self.game.ui.active_filter is None:
                        self.game.clear_resource_filter()
                    else:
                        self.game.apply_resource_filter(self.game.ui.active_filter)

        # ── Boutons UI custom (grille, quit) ──────────────────────────────
        self._update_ui_buttons(mouse_pos, mouse_buttons[0])

        # ── Drag carte ────────────────────────────────────────────────────
        self._handle_drag(mouse_pos)

        self.game.manager.update(time_delta)
        return True

    # ── Handlers privés ───────────────────────────────────────────────────

    def _handle_resize(self, event):
        self.game.WINDOW_WIDTH, self.game.WINDOW_HEIGHT = event.w, event.h
        self.game.manager.set_window_resolution((event.w, event.h))

        map_viewport_width  = self.game.WINDOW_WIDTH  - self.game.PANEL_WIDTH
        map_viewport_height = self.game.WINDOW_HEIGHT
        self.game.camera.update_viewport_size(map_viewport_width, map_viewport_height)

        self.game.ui.resize(self.game.WINDOW_WIDTH, self.game.WINDOW_HEIGHT)
        self.game.map_surface = pygame.Surface((map_viewport_width, map_viewport_height))
        self.game.renderer.zoom_cache.clear()
        self.game.need_redraw = True

    def _handle_mousewheel(self, event, mouse_pos):
        map_mouse_x = mouse_pos[0] - self.game.PANEL_WIDTH
        map_mouse_y = mouse_pos[1]
        if map_mouse_x >= 0:
            zoom_factor = 1.2 if event.y > 0 else 0.8
            self.game.camera.apply_zoom(zoom_factor, (map_mouse_x, map_mouse_y))
            self.game.need_redraw = True

    def _handle_mouse_down(self, mouse_pos, bu3: bool = False):
        if self.grid_manager.visible and bu3:
            self._handle_grid_click(mouse_pos)
            return

        if mouse_pos[0] >= self.game.PANEL_WIDTH:
            self.is_dragging    = True
            self.last_mouse_pos = mouse_pos

    def _handle_mouse_up(self):
        self.is_dragging    = False
        self.last_mouse_pos = None

    def _handle_grid_click(self, mouse_pos):
        map_mouse_x = mouse_pos[0] - self.game.PANEL_WIDTH
        map_mouse_y = mouse_pos[1]

        if map_mouse_x < 0 or map_mouse_y < 0:
            return

        world_pos = self.game.camera.screen_to_world((map_mouse_x, map_mouse_y))
        cell      = self.grid_manager.get_cell_at_world_position(world_pos[0], world_pos[1])

        if cell:
            logger.info(f"Clicked on grid cell: {cell}")

            if self.last_cell:
                if self.last_cell_color != (None, None):
                    self.grid_manager.set_cell_color(
                        self.last_cell[0], self.last_cell[1],
                        self.last_cell_color[0], self.last_cell_color[1]
                    )
                    self.last_cell_color = None
                else:
                    self.grid_manager.reset_cell(self.last_cell[0], self.last_cell[1])

            self.last_cell_color = self.grid_manager.get_cell_color(cell[0], cell[1])
            self.grid_manager.set_cell_color(cell[0], cell[1], (225, 225, 80), 150)
            self.last_cell = (cell[0], cell[1])

            chunk_data = self.game.data_handler.get_chunk_data(cell[0], cell[1])
            if chunk_data:
                self.game.ui.update_chunk_info(chunk_data)
            else:
                self.game.ui.update_chunk_info(None)

    def _update_ui_buttons(self, mouse_pos, mouse_pressed):
        overlay_changed, quit_clicked = self.game.ui.update(mouse_pos, mouse_pressed)

        if overlay_changed:
            self.grid_manager.toggle_visibility()
            self.game.need_redraw = True

        if quit_clicked:
            # Bouton "quitter" en jeu → retour au menu
            self.game.running = False

        return True

    def _handle_drag(self, mouse_pos):
        if self.is_dragging and self.last_mouse_pos:
            dx = (self.last_mouse_pos[0] - mouse_pos[0]) / self.game.camera.zoom
            dy = (self.last_mouse_pos[1] - mouse_pos[1]) / self.game.camera.zoom
            self.game.camera.move(dx, dy)
            self.last_mouse_pos = mouse_pos
            self.game.need_redraw = True

    def get_cell_at_mouse(self, mouse_pos):
        map_mouse_x = mouse_pos[0] - self.game.PANEL_WIDTH
        map_mouse_y = mouse_pos[1]

        if map_mouse_x < 0 or map_mouse_y < 0:
            return None

        world_pos = self.game.camera.screen_to_world((map_mouse_x, map_mouse_y))
        return self.grid_manager.get_cell_at_world_position(world_pos[0], world_pos[1])