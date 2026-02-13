import os
from earthfront.utils.logger import Logger
from earthfront.path import PATH
logger = Logger()

class Images:
    BASE = os.path.join(PATH, "src")
    print(BASE)
    CARTES = f"{BASE}/carte.png"
    ICON_RESOURCES = f"{BASE}/icon_resources.png"
    ICON_QUIT = f"{BASE}/icon_quit.png"

def check_path():
    logger.info("Checking paths...")
    """Vérifie que les fichiers d'images existent"""
    os.makedirs(Images.BASE, exist_ok=True)
    for img in [Images.CARTES, Images.ICON_RESOURCES]:
        if not os.path.exists(img):
            logger.error(f"Fichier manquant : {img}")
            raise FileNotFoundError(f"Fichier manquant : {img}")
    logger.info("Paths checked")