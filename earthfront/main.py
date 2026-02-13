from game.game import Game
from utils.logger import Logger
from path import PATH
import os

path_log_file = os.path.join(PATH, "data/logs/latest.log")

if not os.path.exists(path_log_file):
    os.makedirs(os.path.dirname(path_log_file), exist_ok=True)

logger = Logger(file_path=path_log_file)

if __name__ == "__main__":
    logger.info("Starting game...")
    while True:
        logger.info("Initializing class Game...")
        game = Game()
        logger.info("Running game...")
        result = game.run()
        logger.info(f"Game result: {result}")
        if result == "RESTART":
            logger.info("Restarting game...")
            continue
        else:
            logger.info("Exiting game...")
            break