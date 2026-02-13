"""
Module de gestion du rendu
Gère l'affichage de la carte, de la grille, et de l'interface
"""
import pygame
from utils.logger import Logger

logger = Logger()


class Renderer:
    """Gère tout le rendu du jeu"""
    
    def __init__(self, game):
        """
        Initialise le moteur de rendu
        
        Args:
            game (Game): Référence à l'instance du jeu
        """
        self.game = game
        
        # Cache pour le rendu
        self.zoom_cache = {}
        self.current_cache_zoom = None
        self.last_camera_pos = None
        
        # FPS
        self.fps_update_counter = 0
        self.fps_text_surface = None
        self.last_fps = 0
        self.font = pygame.font.Font(None, 36)
    
    def render(self):
        """Effectue le rendu complet de la scène"""
        # Mettre à jour le FPS toutes les 15 frames
        self._update_fps_display()
        
        camera_pos = (self.game.camera.x, self.game.camera.y)
        
        # Vérifier si on peut skip le rendu de la carte
        if self._can_skip_render(camera_pos):
            self._quick_render()
            return
        
        # Rendu complet nécessaire
        self._full_render()
        
        # Sauvegarder l'état
        self.last_camera_pos = camera_pos
        self.current_cache_zoom = self.game.camera.zoom
        self.game.need_redraw = False
    
    def _can_skip_render(self, camera_pos):
        """Détermine si on peut sauter le rendu complet"""
        return (not self.game.need_redraw and
                self.last_camera_pos == camera_pos and
                self.current_cache_zoom == self.game.camera.zoom and
                self.game.map_surface is not None and
                not self.game.grid_manager.visible)
    
    def _quick_render(self):
        """Rendu rapide sans recalculer la carte"""
        self.game.screen.fill(self.game.COLOR_BG)
        self.game.screen.blit(self.game.map_surface, (self.game.PANEL_WIDTH, 0))
        self._draw_ui_overlay()
        pygame.display.flip()
    
    def _full_render(self):
        """Rendu complet de la scène"""
        self.game.screen.fill(self.game.COLOR_BG)
        
        # Zone disponible pour la carte
        map_width = self.game.WINDOW_WIDTH - self.game.PANEL_WIDTH
        map_height = self.game.WINDOW_HEIGHT
        
        # Créer la surface si nécessaire
        if self.game.map_surface is None or self.game.map_surface.get_size() != (map_width, map_height):
            self.game.map_surface = pygame.Surface((map_width, map_height))
        
        self.game.map_surface.fill(self.game.COLOR_BG)
        
        # Dessiner la carte selon le zoom
        if self.game.camera.zoom > 1.5:
            self._render_high_zoom()
        else:
            self._render_low_zoom()
        
        # Dessiner la grille de ressources si activée
        if self.game.grid_manager.visible:
            self.game.grid_manager.draw(self.game.map_surface, self.game.camera)
        
        # Blitter la surface de la carte sur l'écran
        self.game.screen.blit(self.game.map_surface, (self.game.PANEL_WIDTH, 0))
        
        # Dessiner tous les éléments UI
        self._draw_ui_overlay()
        
        pygame.display.flip()
    
    def _render_high_zoom(self):
        """Rendu optimisé pour gros zoom (> 1.5)"""
        visible_region = self._get_visible_region()
        x, y, w, h = visible_region
        
        if w > 0 and h > 0:
            try:
                cropped_map = self.game.map_image.subsurface(pygame.Rect(x, y, w, h))
                
                scaled_w = int(w * self.game.camera.zoom)
                scaled_h = int(h * self.game.camera.zoom)
                
                scaled_map = pygame.transform.scale(cropped_map, (scaled_w, scaled_h))
                
                world_pos = (x, y)
                screen_pos = self.game.camera.world_to_screen(world_pos)
                
                self.game.map_surface.blit(scaled_map, screen_pos)
            
            except ValueError:
                # Fallback en cas d'erreur
                self._render_fallback()
    
    def _render_low_zoom(self):
        """Rendu avec cache pour petit zoom (<= 1.5)"""
        zoom_key = round(self.game.camera.zoom, 2)
        
        if zoom_key not in self.zoom_cache:
            scaled_width = int(self.game.map_width * self.game.camera.zoom)
            scaled_height = int(self.game.map_height * self.game.camera.zoom)
            
            scaled_map = pygame.transform.scale(self.game.map_image, (scaled_width, scaled_height))
            
            self.zoom_cache[zoom_key] = scaled_map
            
            # Limiter la taille du cache
            if len(self.zoom_cache) > 10:
                oldest = list(self.zoom_cache.keys())[0]
                del self.zoom_cache[oldest]
        
        scaled_map = self.zoom_cache[zoom_key]
        
        top_left_world = (0, 0)
        top_left_screen = self.game.camera.world_to_screen(top_left_world)
        
        self.game.map_surface.blit(scaled_map, top_left_screen)
    
    def _render_fallback(self):
        """Rendu de secours en cas d'erreur"""
        scaled_width = int(self.game.map_width * self.game.camera.zoom)
        scaled_height = int(self.game.map_height * self.game.camera.zoom)
        
        scaled_map = pygame.transform.scale(self.game.map_image, (scaled_width, scaled_height))
        top_left_world = (0, 0)
        top_left_screen = self.game.camera.world_to_screen(top_left_world)
        self.game.map_surface.blit(scaled_map, top_left_screen)
    
    def _get_visible_region(self):
        """Calcule la région visible de la carte en coordonnées monde"""
        top_left = self.game.camera.screen_to_world((0, 0))
        bottom_right = self.game.camera.screen_to_world(
            (self.game.camera.viewport_width, self.game.camera.viewport_height)
        )
        
        margin = 100 / self.game.camera.zoom
        
        x1 = max(0, top_left[0] - margin)
        y1 = max(0, top_left[1] - margin)
        x2 = min(self.game.map_width, bottom_right[0] + margin)
        y2 = min(self.game.map_height, bottom_right[1] + margin)
        
        return int(x1), int(y1), int(x2 - x1), int(y2 - y1)
    
    def _draw_ui_overlay(self):
        """Dessine tous les éléments UI par-dessus la carte"""
        # FPS (décalé pour ne pas toucher le bouton quit)
        if self.game.show_fps and self.fps_text_surface:
            fps_x = self.game.WINDOW_WIDTH - 120 - 84
            self.game.screen.blit(self.fps_text_surface, (fps_x, 20))
        
        # UI Manager
        self.game.manager.draw_ui(self.game.screen)
        
        # Boutons personnalisés avec coins arrondis
        self.game.ui.draw_button(self.game.screen)
    
    def _update_fps_display(self):
        """Met à jour l'affichage du FPS"""
        self.fps_update_counter += 1
        if self.fps_update_counter >= 15:
            self.fps_update_counter = 0
            fps = int(self.game.clock.get_fps())
            if fps != self.last_fps:
                self.last_fps = fps
                self.fps_text_surface = self.font.render(f"FPS: {fps}", True, (255, 255, 0))
    
    def clear_cache(self):
        """Vide tous les caches de rendu"""
        self.zoom_cache.clear()
        self.game.need_redraw = True
        logger.info("Render cache cleared")
