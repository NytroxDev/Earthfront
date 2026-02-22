import pygame
import sys
import os
from game.game import Game
from utils.logger import Logger
from utils.data_handler import DataManager
from path import PATH

path_log_file = os.path.join(PATH, "data/logs/latest.log")
if not os.path.exists(path_log_file):
    os.makedirs(os.path.dirname(path_log_file), exist_ok=True)

logger = Logger(file_path=path_log_file)


def make_screen(config):
    """Crée ou recrée la surface d'affichage selon la config."""
    if config.full_screen:
        flags = pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
        return pygame.display.set_mode((config.window_width, config.window_height), flags)
    else:
        return pygame.display.set_mode((config.window_width, config.window_height), pygame.RESIZABLE)


def main():
    logger.info("Starting game...")

    # ── Init pygame UNE SEULE FOIS ──────────────────────────────────────────
    pygame.init()
    pygame.display.set_caption("Earthfront - v1.0")

    data_manager = DataManager()
    config = data_manager.load_config()
    screen = make_screen(config)

    # ── Boucle principale : menu → jeu → menu sans recréer de fenêtre ───────
    while True:
        config = data_manager.load_config()

        logger.info("Initializing Game...")
        game = Game(screen=screen, config=config)
        logger.info("Running game...")
        result = game.run()
        logger.info(f"Game result: {result}")

        if result == "EXIT":
            logger.info("Exiting game...")
            break

        if result == "RESTART":
            # Les settings ont changé — on recharge la config
            # et on adapte la fenêtre si besoin (plein écran, résolution)
            logger.info("Restarting (retour au menu)...")
            config = data_manager.load_config()
            screen = make_screen(config)
            continue

        # result == None → l'utilisateur a fermé via la croix/ESC en jeu
        # → on retourne simplement au menu
        logger.info("Retour au menu...")
        continue

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()