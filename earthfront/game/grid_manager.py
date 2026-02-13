"""
Module de gestion de la grille de ressources
Gère l'affichage et la manipulation des cellules 10x10px
"""
import pygame
from utils.logger import Logger

logger = Logger()


class GridManager:
    """Gère la grille de ressources avec coloration et images"""
    
    def __init__(self, map_width, map_height, cell_size=10):
        """
        Initialise le gestionnaire de grille
        
        Args:
            map_width (int): Largeur de la carte en pixels
            map_height (int): Hauteur de la carte en pixels
            cell_size (int): Taille d'une cellule en pixels (défaut: 10)
        """
        self.map_width = map_width
        self.map_height = map_height
        self.cell_size = cell_size
        
        # Calculer le nombre de colonnes et lignes
        self.num_cols = map_width // cell_size
        self.num_rows = map_height // cell_size
        
        # Données des cellules (dict avec clé (x, y))
        self.grid_cells = {}  # Format: {(x, y): {'color': (r,g,b), 'alpha': 0-255, 'image': Surface}}
        
        # Cache des surfaces de cellules
        self.cell_cache = {}
        
        # Visibilité de la grille
        self.visible = False
        
        # Couleur de la grille
        self.grid_color = (121, 122, 125)
        self.grid_line_width = 1
        
        logger.info(f"GridManager initialized: {self.num_cols}x{self.num_rows} cells")
    
    def set_cell_color(self, x, y, color, alpha=180):
        """
        Colorie une cellule de la grille
        
        Args:
            x (int): Coordonnée X de la cellule
            y (int): Coordonnée Y de la cellule
            color (tuple): Couleur RGB (r, g, b)
            alpha (int): Transparence 0-255 (0=invisible, 255=opaque)
        
        Returns:
            bool: True si succès, False si hors limites
        """
        if not (0 <= x < self.num_cols and 0 <= y < self.num_rows):
            logger.warning(f"Cell ({x}, {y}) out of bounds (max: {self.num_cols-1}, {self.num_rows-1})")
            return False
        
        if (x, y) not in self.grid_cells:
            self.grid_cells[(x, y)] = {}
        
        self.grid_cells[(x, y)]['color'] = color
        self.grid_cells[(x, y)]['alpha'] = alpha
        
        # Invalider le cache pour cette cellule
        if (x, y) in self.cell_cache:
            del self.cell_cache[(x, y)]
        
        logger.debug(f"Cell ({x}, {y}) colored with {color}, alpha={alpha}")
        return True
    
    def set_cell_image(self, x, y, image_surface, alpha=255):
        """
        Place une image sur une cellule
        
        Args:
            x (int): Coordonnée X de la cellule
            y (int): Coordonnée Y de la cellule
            image_surface (pygame.Surface): Image à afficher
            alpha (int): Transparence de l'image 0-255
        
        Returns:
            bool: True si succès, False si hors limites
        """
        if not (0 <= x < self.num_cols and 0 <= y < self.num_rows):
            logger.warning(f"Cell ({x}, {y}) out of bounds (max: {self.num_cols-1}, {self.num_rows-1})")
            return False
        
        if (x, y) not in self.grid_cells:
            self.grid_cells[(x, y)] = {}
        
        # Redimensionner l'image pour qu'elle fasse cell_size x cell_size pixels
        scaled_image = pygame.transform.scale(image_surface, (self.cell_size, self.cell_size))
        scaled_image.set_alpha(alpha)
        
        self.grid_cells[(x, y)]['image'] = scaled_image
        self.grid_cells[(x, y)]['alpha'] = alpha
        
        # Invalider le cache pour cette cellule
        if (x, y) in self.cell_cache:
            del self.cell_cache[(x, y)]
        
        logger.debug(f"Cell ({x}, {y}) set with image, alpha={alpha}")
        return True
    
    def reset_cell(self, x, y):
        """
        Remet une cellule à son état par défaut
        
        Args:
            x (int): Coordonnée X de la cellule
            y (int): Coordonnée Y de la cellule
        
        Returns:
            bool: True si la cellule existait, False sinon
        """
        if (x, y) in self.grid_cells:
            del self.grid_cells[(x, y)]
            logger.debug(f"Cell ({x}, {y}) reset to default")
        
        if (x, y) in self.cell_cache:
            del self.cell_cache[(x, y)]
        
        return (x, y) in self.grid_cells
    
    def clear_all_cells(self):
        """Efface toutes les cellules colorées/avec images"""
        count = len(self.grid_cells)
        self.grid_cells.clear()
        self.cell_cache.clear()
        logger.info(f"All cells cleared ({count} cells)")
    
    def get_cell_at_world_position(self, world_x, world_y):
        """
        Retourne les coordonnées de la cellule à une position monde
        
        Args:
            world_x (float): Position X dans le monde
            world_y (float): Position Y dans le monde
        
        Returns:
            tuple: (x, y) de la cellule ou None si hors carte
        """
        x = int(world_x // self.cell_size)
        y = int(world_y // self.cell_size)
        
        if 0 <= x < self.num_cols and 0 <= y < self.num_rows:
            return (x, y)
        return None
    
    def toggle_visibility(self):
        """Bascule la visibilité de la grille"""
        self.visible = not self.visible
        logger.info(f"Grid visibility: {self.visible}")
        return self.visible
    
    def show(self):
        """Affiche la grille"""
        self.visible = True
    
    def hide(self):
        """Cache la grille"""
        self.visible = False
    
    def draw(self, surface, camera):
        """
        Dessine la grille sur une surface
        
        Args:
            surface (pygame.Surface): Surface sur laquelle dessiner
            camera (Camera): Objet caméra pour les conversions de coordonnées
        """
        if not self.visible:
            return
        
        # Calculer la région visible pour optimiser le rendu
        top_left = camera.screen_to_world((0, 0))
        bottom_right = camera.screen_to_world((camera.viewport_width, camera.viewport_height))
        
        # Déterminer les indices de début et fin pour les lignes visibles
        start_col = max(0, int(top_left[0] // self.cell_size) - 1)
        end_col = min(self.num_cols + 1, int(bottom_right[0] // self.cell_size) + 2)
        start_row = max(0, int(top_left[1] // self.cell_size) - 1)
        end_row = min(self.num_rows + 1, int(bottom_right[1] // self.cell_size) + 2)
        
        # Dessiner d'abord les cellules colorées/avec images
        self._draw_cells(surface, camera, start_row, end_row, start_col, end_col)
        
        # Dessiner les lignes de la grille par-dessus
        self._draw_grid_lines(surface, camera, start_row, end_row, start_col, end_col)
    
    def _draw_cells(self, surface, camera, start_row, end_row, start_col, end_col):
        """Dessine les cellules colorées et avec images"""
        for grid_y in range(start_row, end_row):
            for grid_x in range(start_col, end_col):
                if (grid_x, grid_y) not in self.grid_cells:
                    continue
                
                cell_data = self.grid_cells[(grid_x, grid_y)]
                
                # Position monde de la cellule
                world_x = grid_x * self.cell_size
                world_y = grid_y * self.cell_size
                
                # Convertir en position écran
                screen_pos = camera.world_to_screen((world_x, world_y))
                
                # Taille de la cellule à l'écran (dépend du zoom)
                cell_screen_size = int(self.cell_size * camera.zoom)
                
                # Dessiner la couleur si présente
                if 'color' in cell_data:
                    cell_surf = pygame.Surface((cell_screen_size, cell_screen_size), pygame.SRCALPHA)
                    color_with_alpha = (*cell_data['color'], cell_data.get('alpha', 180))
                    cell_surf.fill(color_with_alpha)
                    surface.blit(cell_surf, screen_pos)
                
                # Dessiner l'image si présente
                if 'image' in cell_data:
                    scaled_image = pygame.transform.scale(
                        cell_data['image'],
                        (cell_screen_size, cell_screen_size)
                    )
                    surface.blit(scaled_image, screen_pos)
    
    def _draw_grid_lines(self, surface, camera, start_row, end_row, start_col, end_col):
        """Dessine les lignes de la grille"""
        # Dessiner les lignes verticales
        for i in range(start_col, end_col):
            x = i * self.cell_size
            world_start = (x, max(0, start_row * self.cell_size))
            world_end = (x, min(self.map_height, end_row * self.cell_size))
            
            screen_start = camera.world_to_screen(world_start)
            screen_end = camera.world_to_screen(world_end)
            
            pygame.draw.line(surface, self.grid_color, screen_start, screen_end, self.grid_line_width)
        
        # Dessiner les lignes horizontales
        for i in range(start_row, end_row):
            y = i * self.cell_size
            world_start = (max(0, start_col * self.cell_size), y)
            world_end = (min(self.map_width, end_col * self.cell_size), y)
            
            screen_start = camera.world_to_screen(world_start)
            screen_end = camera.world_to_screen(world_end)
            
            pygame.draw.line(surface, self.grid_color, screen_start, screen_end, self.grid_line_width)
    
    def get_stats(self):
        """Retourne des statistiques sur la grille"""
        return {
            'total_cells': self.num_cols * self.num_rows,
            'modified_cells': len(self.grid_cells),
            'cached_cells': len(self.cell_cache),
            'grid_size': f"{self.num_cols}x{self.num_rows}",
            'cell_size': f"{self.cell_size}px",
            'visible': self.visible
        }
