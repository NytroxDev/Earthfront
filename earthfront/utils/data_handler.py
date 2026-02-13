import json
import os.path
from pathlib import Path
from typing import  Optional
import dataclasses
from earthfront.utils.color_converter import rgb_to_hex, hex_to_rgb
from earthfront.path import PATH
from earthfront.utils.logger import Logger
logger = Logger()

@dataclasses.dataclass
class Config:
    window_width: int = 1280
    window_height: int = 720
    window_x: int = 0
    window_y: int = 0
    panel_width: int = 180
    show_fps: bool = True
    fps: int = 60
    full_screen: bool = False

    def to_dict(self):
        return dataclasses.asdict(self)

    def from_dict(self, data):
        if not isinstance(data, dict):
            raise ValueError("data must be a dictionary")
        for key, value in data.items():
            setattr(self, key, value)

    def update(self, data):
        if not isinstance(data, dict):
            raise ValueError("data must be a dictionary")
        for key, value in data.items():
            setattr(self, key, value)

class Color:
    def __init__(self, rgb: tuple[int, ...] = None, hexa: str = None):
        if not rgb and not hex:
            raise ValueError("Vous devez fournir un tuple RGB ou une valeur hex")
        if rgb:
            self.r, self.g, self.b = rgb
        if hexa:
            self.r, self.g, self.b = hex_to_rgb(hex)

    @staticmethod
    def parse_color_from_str(text: str):
        if not text.startswith("Color("):
            raise ValueError("Le texte doit commencer par 'Color('")
        texte = text.lstrip("Color(").rstrip(")")
        rgb = tuple(int(x) for x in texte.split(", "))
        return Color(rgb=rgb)

    @property
    def rgb(self):
        return (self.r, self.g, self.b)

    @property
    def hex(self):
        return rgb_to_hex(self.rgb)

    def get_hex(self):
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"

    def get_rgb(self):
        return (self.r, self.g, self.b)

    def get_rgba(self, a):
        return (self.r, self.g, self.b, a)

    def __str__(self):
        return f"Color({self.r}, {self.g}, {self.b})"

    def __repr__(self):
        return f"Color({self.r}, {self.g}, {self.b})"

@dataclasses.dataclass
class Theme:
    BackgroundPanel: Color = Color((20, 20, 30))
    TextMainMenu: Color = Color((255, 255, 255))
    ButtonPlay: Color = Color((0, 255, 0))
    ButtonQuit: Color = Color((255, 0, 0))
    ButtonOption: Color = Color((255, 255, 255))
    BackgroundMainMenu: Color = Color((20, 20, 30))

    def to_dict(self):
        for key, value in self.__dict__.items():
            if isinstance(value, Color):
                self.__dict__[key] = value.rgb
        return dataclasses.asdict(self)

    def from_dict(self, data):
        if not isinstance(data, dict):
            raise ValueError("data must be a dictionary")
        for key, value in data.items():
            setattr(self, key, value)

    def update(self, data):
        if not isinstance(data, dict):
            raise ValueError("data must be a dictionary")
        for key, value in data.items():
            setattr(self, key, value)

class DataManager:
    def __init__(self):
        self.base = Path(os.path.join(PATH, "data/"))
        self.config = self.base / "config.json"
        self.theme = self.base / "theme.json"
        self.saves = self.base / "saves.json"

        self.check_file_exists()

    @staticmethod
    def _write_default(file):
        with open(file, "w") as f:
            json.dump({}, f)

    @staticmethod
    def _get_content(file):
        with open(file, "r") as f:
            return f.read()

    def check_file_exists(self) -> tuple[bool, Optional[Exception]]:
        all_files = [self.config, self.theme, self.saves]
        try:
            for f in all_files:
                if not f.exists():
                    f.touch(exist_ok=True)
                else:
                    if not self._get_content(f):
                        self._write_default(f)
        except Exception as e:
            logger.error(f"Error creating files: {e}")
            return False, e
        return True, None

    ########################
    ######## CONFIG ########
    ########################

    def load_config(self, _e = None):
        logger.info("Loading config...")

        with open(self.config, "r") as f:
            try:
                texte = f.read()
                if not texte or texte == "{}":
                    with open(self.config, "w") as f:
                        json.dump(Config().to_dict(), f)

                    logger.error("Config file created")

                    if _e:
                        logger.error("Error loading config, retrying...")

                    return self.load_config(_e=1) if not _e else Config()

                cfg = Config()

                cfg.update(data=json.loads(texte))

                return cfg
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                return Config()

    def save_config(self, config):
        logger.info("Saving config...")
        if not isinstance(config, Config):
            raise ValueError("config must be an instance of Config")
        with open(self.config, "w") as f:
            json.dump(config.to_dict(), f)

    ########################
    ######## THEME #########
    ########################

    def save_default_theme(self):
        with open(self.theme, "w") as f:
            json.dump(Theme().to_dict(), f)

    def save_theme(self, theme: Theme):
        logger.info("Saving theme...")
        with open(self.theme, "w") as f:
            json.dump(theme, f)

    def load_theme(self):
        logger.info("Loading theme...")
        with open(self.theme, "r") as f:
            data = json.load(f)
            for key, value in data.items():
                if isinstance(value, str):
                    try:
                        data[key] = Color.parse_color_from_str(value)
                    except Exception as e:
                        logger.error(f"Error parsing color: {e}")
                if isinstance(value, list):
                    data[key] = tuple(value)
            theme = Theme()
            theme.update(data=data)
            return theme

if __name__ == "__main__":
    DataManager().save_default_theme()