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
        self.map_width  = map_width
        self.map_height = map_height
        self.cell_size  = cell_size

        self.num_cols = map_width  // cell_size
        self.num_rows = map_height // cell_size

        # Données brutes des cellules {(x, y): {'color': (r,g,b), 'alpha': int, 'image': Surface}}
        self.grid_cells = {}

        # Visibilité
        self.visible = False

        # Couleur des lignes de grille
        self.grid_color      = (121, 122, 125)
        self.grid_line_width = 1

        # ── Overlay précalculée ──────────────────────────────────────────────
        # Surface SRCALPHA à la résolution de la carte (1px = 1px monde).
        # Elle est redessinée seulement quand grid_cells change, pas à chaque frame.
        self._overlay: pygame.Surface | None = None
        self._overlay_dirty = True

        logger.info(f"GridManager initialized: {self.num_cols}x{self.num_rows} cells")

    # ── API publique ─────────────────────────────────────────────────────────

    def set_cell_color(self, x, y, color, alpha=180):
        if not (0 <= x < self.num_cols and 0 <= y < self.num_rows):
            logger.warning(f"Cell ({x}, {y}) out of bounds")
            return False

        cell = self.grid_cells.setdefault((x, y), {})
        cell['color'] = color
        cell['alpha'] = alpha
        self._overlay_dirty = True
        return True

    def set_cell_image(self, x, y, image_surface, alpha=255):
        if not (0 <= x < self.num_cols and 0 <= y < self.num_rows):
            logger.warning(f"Cell ({x}, {y}) out of bounds")
            return False

        scaled = pygame.transform.scale(image_surface, (self.cell_size, self.cell_size))
        scaled.set_alpha(alpha)

        cell = self.grid_cells.setdefault((x, y), {})
        cell['image'] = scaled
        cell['alpha'] = alpha
        self._overlay_dirty = True
        return True

    def reset_cell(self, x, y):
        existed = (x, y) in self.grid_cells
        if existed:
            del self.grid_cells[(x, y)]
            self._overlay_dirty = True
        return existed

    def clear_all_cells(self):
        count = len(self.grid_cells)
        self.grid_cells.clear()
        self._overlay_dirty = True
        logger.info(f"All cells cleared ({count} cells)")

    def get_cell_at_world_position(self, world_x, world_y):
        x = int(world_x // self.cell_size)
        y = int(world_y // self.cell_size)
        if 0 <= x < self.num_cols and 0 <= y < self.num_rows:
            return x, y
        return None

    def get_cell_color(self, x, y):
        cell = self.grid_cells.get((x, y))
        if cell and 'color' in cell:
            return cell['color'], cell.get('alpha', 255)
        return None, None

    def toggle_visibility(self):
        self.visible = not self.visible
        logger.info(f"Grid visibility: {self.visible}")
        return self.visible

    def show(self): self.visible = True
    def hide(self): self.visible = False

    def get_stats(self):
        return {
            'total_cells':    self.num_cols * self.num_rows,
            'modified_cells': len(self.grid_cells),
            'grid_size':      f"{self.num_cols}x{self.num_rows}",
            'cell_size':      f"{self.cell_size}px",
            'visible':        self.visible,
            'overlay_dirty':  self._overlay_dirty,
        }

    # ── Rendu ────────────────────────────────────────────────────────────────

    def draw(self, surface, camera):
        if not self.visible:
            return

        top_left     = camera.screen_to_world((0, 0))
        bottom_right = camera.screen_to_world((camera.viewport_width, camera.viewport_height))

        start_col = max(0,             int(top_left[0]     // self.cell_size) - 1)
        end_col   = min(self.num_cols, int(bottom_right[0] // self.cell_size) + 2)
        start_row = max(0,             int(top_left[1]     // self.cell_size) - 1)
        end_row   = min(self.num_rows, int(bottom_right[1] // self.cell_size) + 2)

        # 1) Overlay des cellules colorées (un seul blit par frame)
        self._draw_cells_overlay(surface, camera)

        # 2) Lignes de grille par-dessus
        self._draw_grid_lines(surface, camera, start_row, end_row, start_col, end_col)

    def _rebuild_overlay(self):
        """
        Reconstruit l'overlay à la résolution de la carte (1px monde = 1px).
        Appelée une seule fois après chaque modification des données,
        pas à chaque frame.
        """
        self._overlay = pygame.Surface((self.map_width, self.map_height), pygame.SRCALPHA)
        self._overlay.fill((0, 0, 0, 0))

        cs = self.cell_size
        for (gx, gy), cell in self.grid_cells.items():
            px = gx * cs
            py = gy * cs

            if 'color' in cell:
                r, g, b = cell['color']
                a = cell.get('alpha', 180)
                self._overlay.fill((r, g, b, a), pygame.Rect(px, py, cs, cs))

            if 'image' in cell:
                self._overlay.blit(cell['image'], (px, py))

        self._overlay_dirty = False
        logger.debug(f"Overlay rebuilt ({len(self.grid_cells)} cells)")

    def _draw_cells_overlay(self, surface, camera):
        """
        Scale et blit l'overlay visible en un seul appel par frame.
        Remplace les N allocations de Surface + N blits de l'ancienne version.
        """
        if not self.grid_cells:
            return

        if self._overlay_dirty or self._overlay is None:
            self._rebuild_overlay()

        # Région monde visible
        top_left     = camera.screen_to_world((0, 0))
        bottom_right = camera.screen_to_world((camera.viewport_width, camera.viewport_height))

        src_x = max(0, int(top_left[0]) - 1)
        src_y = max(0, int(top_left[1]) - 1)
        src_w = min(self.map_width,  int(bottom_right[0]) + 2) - src_x
        src_h = min(self.map_height, int(bottom_right[1]) + 2) - src_y

        if src_w <= 0 or src_h <= 0:
            return

        # Extraire uniquement la portion visible (évite de scaler toute la carte)
        src_rect    = pygame.Rect(src_x, src_y, src_w, src_h)
        visible_sub = self._overlay.subsurface(src_rect)

        # Calculer la taille de destination en pixels entiers
        sx0, sy0 = camera.world_to_screen((src_x, src_y))
        sx1, sy1 = camera.world_to_screen((src_x + src_w, src_y + src_h))

        dst_w = round(sx1) - round(sx0)
        dst_h = round(sy1) - round(sy0)

        if dst_w <= 0 or dst_h <= 0:
            return

        # 1 scale + 1 blit = tout ce qu'on fait par frame
        scaled = pygame.transform.scale(visible_sub, (dst_w, dst_h))
        surface.blit(scaled, (round(sx0), round(sy0)))

    def _draw_grid_lines(self, surface, camera, start_row, end_row, start_col, end_col):
        for i in range(start_col, end_col + 1):
            x = i * self.cell_size
            world_start = (x, max(0,               start_row * self.cell_size))
            world_end   = (x, min(self.map_height, end_row   * self.cell_size))
            pygame.draw.line(surface, self.grid_color,
                             camera.world_to_screen(world_start),
                             camera.world_to_screen(world_end),
                             self.grid_line_width)

        for i in range(start_row, end_row + 1):
            y = i * self.cell_size
            world_start = (max(0,              start_col * self.cell_size), y)
            world_end   = (min(self.map_width, end_col   * self.cell_size), y)
            pygame.draw.line(surface, self.grid_color,
                             camera.world_to_screen(world_start),
                             camera.world_to_screen(world_end),
                             self.grid_line_width)