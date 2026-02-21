"""
Module de gestion des événements du jeu
Gère les entrées clavier, souris, et fenêtre
"""
import pygame
import pygame_gui
from utils.logger import Logger
from .grid_manager import GridManager

logger = Logger()


class EventHandler:
    """Gère tous les événements du jeu"""
    
    def __init__(self, game):
        """
        Initialise le gestionnaire d'événements
        
        Args:
            game (Game): Référence à l'instance du jeu
        """
        self.game = game
        self.grid_manager: GridManager = self.game.grid_manager
        self.is_dragging = False
        self.last_mouse_pos = None
        self.last_cell = None
    
    def handle_events(self):
        """
        Traite tous les événements pygame
        
        Returns:
            bool: True pour continuer, False pour quitter
        """
        time_delta = self.game.clock.tick(self.game.FPS) / 1000.0
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_buttons = pygame.mouse.get_pressed()
        
        for event in pygame.event.get():
            # Événement de fermeture
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                logger.info("Quitting game...")
                return False
            
            # Redimensionnement de la fenêtre
            elif event.type == pygame.VIDEORESIZE:
                self._handle_resize(event)

            # Raccourci clavier pour la grille
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_g:
                self.game.grid_manager.toggle_visibility()
                self.game.ui.toggle_grid_button()  # Synchroniser l'état du bouton
                self.game.need_redraw = True
                logger.info(f"Grid visibility toggled: {self.game.grid_manager.visible}")

            # Molette de la souris (zoom)
            elif event.type == pygame.MOUSEWHEEL:
                self._handle_mousewheel(event, mouse_pos)
            
            # Clic de souris
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_mouse_down(mouse_pos)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                self._handle_mouse_down(mouse_pos, bu3=True)
            
            # Relâchement de la souris
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._handle_mouse_up()
            
            # Passer l'événement au gestionnaire UI
            self.game.manager.process_events(event)

            # Vérifier les boutons filtres ressources
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                result = self.game.ui.check_filter_event(event)
                if result is not None:
                    # result = None → filtre désactivé, str → ressource active
                    if self.game.ui.active_filter is None:
                        self.game.clear_resource_filter()
                    else:
                        self.game.apply_resource_filter(self.game.ui.active_filter)
        
        # Mettre à jour les boutons UI
        self._update_ui_buttons(mouse_pos, mouse_buttons[0])
        
        # Gérer le drag de la carte
        self._handle_drag(mouse_pos)
        
        # Mettre à jour le gestionnaire UI
        self.game.manager.update(time_delta)
        
        return True
    
    def _handle_resize(self, event):
        """Gère le redimensionnement de la fenêtre"""
        self.game.WINDOW_WIDTH, self.game.WINDOW_HEIGHT = event.w, event.h

        self.game.manager.set_window_resolution((event.w, event.h))
        
        # Mise à jour du viewport de la caméra
        map_viewport_width = self.game.WINDOW_WIDTH - self.game.PANEL_WIDTH
        map_viewport_height = self.game.WINDOW_HEIGHT
        self.game.camera.update_viewport_size(map_viewport_width, map_viewport_height)
        
        # Mise à jour UI
        self.game.ui.resize(self.game.WINDOW_WIDTH, self.game.WINDOW_HEIGHT)
        
        # Recréer la surface de la carte
        self.game.map_surface = pygame.Surface((map_viewport_width, map_viewport_height))
        
        # Invalidation du cache
        self.game.renderer.zoom_cache.clear()
        self.game.need_redraw = True

    def _handle_mousewheel(self, event, mouse_pos):
        """Gère le zoom avec la molette"""
        # Ajuster la position de la souris relative à la zone de la carte
        map_mouse_x = mouse_pos[0] - self.game.PANEL_WIDTH
        map_mouse_y = mouse_pos[1]
        
        # Seulement si la souris est sur la carte
        if map_mouse_x >= 0:
            zoom_factor = 1.2 if event.y > 0 else 0.8
            self.game.camera.apply_zoom(zoom_factor, (map_mouse_x, map_mouse_y))
            self.game.need_redraw = True
    
    def _handle_mouse_down(self, mouse_pos, bu3 : bool = False):
        """Gère le clic de souris"""
        # Gestion du clic sur la grille
        if self.game.grid_manager.visible and bu3:
            self._handle_grid_click(mouse_pos)
            return

        # Seulement si on clique sur la carte (pas sur le panel)
        if mouse_pos[0] >= self.game.PANEL_WIDTH:
            self.is_dragging = True
            self.last_mouse_pos = mouse_pos
            

    
    def _handle_mouse_up(self):
        """Gère le relâchement de la souris"""
        self.is_dragging = False
        self.last_mouse_pos = None

    def _handle_grid_click(self, mouse_pos):
        """Gère le clic sur une cellule de la grille"""
        # Convertir la position souris en position monde
        map_mouse_x = mouse_pos[0] - self.game.PANEL_WIDTH
        map_mouse_y = mouse_pos[1]

        if map_mouse_x < 0 or map_mouse_y < 0:
            return

        world_pos = self.game.camera.screen_to_world((map_mouse_x, map_mouse_y))
        cell = self.game.grid_manager.get_cell_at_world_position(world_pos[0], world_pos[1])

        if cell:
            logger.info(f"Clicked on grid cell: {cell}")

            # Effacer la dernière cellule surlignée
            if self.last_cell:
                self.grid_manager.reset_cell(self.last_cell[0], self.last_cell[1])

            # Surligner la nouvelle cellule
            self.game.grid_manager.set_cell_color(cell[0], cell[1], (225, 225, 80), 150)
            self.last_cell = (cell[0], cell[1])

            # ===== NOUVEAU : Récupérer et afficher les données du chunk =====
            chunk_data = self.game.data_handler.get_chunk_data(cell[0], cell[1])
            if chunk_data:
                logger.info(f"Chunk data: {chunk_data}")
                self.game.ui.update_chunk_info(chunk_data)
            else:
                logger.warning(f"No chunk data found for cell {cell}")
                self.game.ui.update_chunk_info(None)
            # =================================================================
    
    def _update_ui_buttons(self, mouse_pos, mouse_pressed):
        """Met à jour les boutons de l'interface"""
        overlay_changed, quit_clicked = self.game.ui.update(mouse_pos, mouse_pressed)
        
        if overlay_changed:
            # Basculer l'affichage de la grille
            self.game.grid_manager.toggle_visibility()
            self.game.need_redraw = True
        
        if quit_clicked:
            self.game.need_restart = True
            return False
        
        return True
    
    def _handle_drag(self, mouse_pos):
        """Gère le déplacement de la carte par drag"""
        if self.is_dragging and self.last_mouse_pos:
            current_pos = mouse_pos
            dx = (self.last_mouse_pos[0] - current_pos[0]) / self.game.camera.zoom
            dy = (self.last_mouse_pos[1] - current_pos[1]) / self.game.camera.zoom
            self.game.camera.move(dx, dy)
            self.last_mouse_pos = current_pos
            self.game.need_redraw = True
    
    def get_cell_at_mouse(self, mouse_pos):
        """
        Retourne la cellule de la grille sous la souris
        
        Args:
            mouse_pos (tuple): Position de la souris
        
        Returns:
            tuple: (x, y) de la cellule ou None
        """
        map_mouse_x = mouse_pos[0] - self.game.PANEL_WIDTH
        map_mouse_y = mouse_pos[1]
        
        if map_mouse_x < 0 or map_mouse_y < 0:
            return None
        
        world_pos = self.game.camera.screen_to_world((map_mouse_x, map_mouse_y))
        return self.game.grid_manager.get_cell_at_world_position(world_pos[0], world_pos[1])
