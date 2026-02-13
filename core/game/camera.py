from core.logger import Logger
logger = Logger()

class Camera:
    """Gère position et zoom de la caméra dans une zone définie (carte à droite du panel)"""

    def __init__(self, map_width, map_height, viewport_width, viewport_height):
        logger.info("Initializing Camera...")

        logger.info(f"map_width: {map_width}")
        logger.info(f"map_height: {map_height}")
        logger.info(f"viewport_width: {viewport_width}")
        logger.info(f"viewport_height: {viewport_height}")

        self.map_width = map_width
        self.map_height = map_height
        self.viewport_width = viewport_width  # zone disponible pour la carte
        self.viewport_height = viewport_height

        # Centre initial
        self.x = map_width / 2
        self.y = map_height / 2

        logger.info(f"x: {self.x}")
        logger.info(f"y: {self.y}")

        # Zoom
        self.zoom = 3.0
        self.max_zoom = 15.0
        self.min_zoom = 0.1
        self.update_min_zoom()

        logger.info(f"zoom: {self.zoom}")
        logger.info(f"max_zoom: {self.max_zoom}")
        logger.info(f"min_zoom: {self.min_zoom}")

        logger.info("Camera initialized")

    def update_viewport_size(self, width, height):
        """Met à jour la zone de rendu de la carte"""
        self.viewport_width = width
        self.viewport_height = height
        self.update_min_zoom()
        self.clamp_position()

    def update_min_zoom(self):
        """Zoom minimum pour voir toute la carte dans le viewport"""
        zoom_x = self.viewport_width / self.map_width
        zoom_y = self.viewport_height / self.map_height
        self.min_zoom = min(zoom_x, zoom_y)
        if self.zoom < self.min_zoom:
            self.zoom = self.min_zoom

    def apply_zoom(self, zoom_factor, mouse_pos_screen):
        """Zoom centré sur la position de la souris dans le viewport"""
        old_zoom = self.zoom
        new_zoom = old_zoom * zoom_factor
        new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))

        if old_zoom != new_zoom:
            # Calculer la position monde sous le curseur AVANT le zoom
            world_x_before = self.x + (mouse_pos_screen[0] - self.viewport_width / 2) / old_zoom
            world_y_before = self.y + (mouse_pos_screen[1] - self.viewport_height / 2) / old_zoom

            # Appliquer le nouveau zoom
            self.zoom = new_zoom

            # Calculer où devrait être la caméra pour que ce point monde
            # reste sous le curseur après le zoom
            self.x = world_x_before - (mouse_pos_screen[0] - self.viewport_width / 2) / new_zoom
            self.y = world_y_before - (mouse_pos_screen[1] - self.viewport_height / 2) / new_zoom

            self.clamp_position()

    def move(self, dx, dy):
        """Déplace la caméra"""
        self.x += dx
        self.y += dy
        self.clamp_position()

    def clamp_position(self):
        """Empêche la caméra de sortir de la carte"""
        half_w = (self.viewport_width / 2) / self.zoom
        half_h = (self.viewport_height / 2) / self.zoom

        min_x = half_w
        max_x = self.map_width - half_w
        min_y = half_h
        max_y = self.map_height - half_h

        if min_x > max_x:
            self.x = self.map_width / 2
        else:
            self.x = max(min_x, min(max_x, self.x))

        if min_y > max_y:
            self.y = self.map_height / 2
        else:
            self.y = max(min_y, min(max_y, self.y))

    def world_to_screen(self, world_pos):
        """Convertit une position monde en position écran dans le viewport"""
        screen_x = (world_pos[0] - self.x) * self.zoom + self.viewport_width / 2
        screen_y = (world_pos[1] - self.y) * self.zoom + self.viewport_height / 2
        return screen_x, screen_y

    def screen_to_world(self, screen_pos):
        """Convertit une position écran dans le viewport en position monde"""
        world_x = self.x + (screen_pos[0] - self.viewport_width / 2) / self.zoom
        world_y = self.y + (screen_pos[1] - self.viewport_height / 2) / self.zoom
        return world_x, world_y