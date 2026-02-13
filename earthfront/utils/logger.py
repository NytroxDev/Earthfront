import threading
import sys
from datetime import datetime
from enum import IntEnum
import inspect


class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


COLOR_CODES = {
    LogLevel.DEBUG: "\033[37m",    # Blanc
    LogLevel.INFO: "\033[36m",     # Cyan
    LogLevel.WARNING: "\033[33m",  # Jaune
    LogLevel.ERROR: "\033[31m",    # Rouge
    LogLevel.CRITICAL: "\033[41m", # Rouge fond
}
RESET_COLOR = "\033[0m"


class Logger:
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        level=LogLevel.INFO,
        stream=sys.stdout,
        file_path=None,
        time_format="%H:%M:%S",
        use_color=True,
        show_caller=True
    ):
        if hasattr(self, "_initialized"):
            return

        self.level = level
        self.stream = stream
        self.file_path = file_path
        self.time_format = time_format
        self.use_color = use_color
        self.show_caller = show_caller
        self._lock = threading.Lock()

        self._initialized = True

    def set_level(self, level: LogLevel):
        self.level = level

    def _get_caller(self):
        # inspect.stack()[2] → celui qui a appelé la fonction de log
        frame = inspect.stack()[3]
        filename = frame.filename.split("/")[-1]  # juste le nom du fichier
        line_no = frame.lineno
        return f"{filename}:{line_no}"

    def _log(self, level: LogLevel, message: str):
        if level < self.level:
            return

        now = datetime.now().strftime(self.time_format)
        color = COLOR_CODES.get(level, "") if self.use_color else ""
        reset = RESET_COLOR if self.use_color else ""
        caller = self._get_caller() if self.show_caller else ""
        caller_str = f" [{caller}]" if caller else ""

        log_line = f"{color}[{now}] [{level.name}]{caller_str} {message}{reset}"

        with self._lock:
            print(log_line, file=self.stream, flush=True)

            if self.file_path:
                # écriture dans fichier sans couleur
                with open(self.file_path, "a", encoding="utf-8") as f:
                    f.write(f"[{now}] [{level.name}]{caller_str} {message}\n")

    def debug(self, msg): self._log(LogLevel.DEBUG, msg)
    def info(self, msg): self._log(LogLevel.INFO, msg)
    def warning(self, msg): self._log(LogLevel.WARNING, msg)
    def error(self, msg): self._log(LogLevel.ERROR, msg)
    def critical(self, msg): self._log(LogLevel.CRITICAL, msg)
