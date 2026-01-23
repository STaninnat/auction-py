import logging
import sys

from decouple import config
from pythonjsonlogger import json


class LoggerSetup:
    """
    Application logging configuration utility.
    Centralized logger initialization and formatter setup.
    """

    def __init__(self):
        self.debug = config("DEBUG", default=False, cast=bool)
        self.log_level = config("LOG_LEVEL", default="INFO")
        self.logger = logging.getLogger()

    def configure(self):
        # Clear existing handlers (to prevent duplicate log entries).
        if self.logger.handlers:
            self.logger.handlers = []

        # Create Handlers
        handler = logging.StreamHandler(sys.stdout)

        # Select Formatter (Polymorphismish behavior based on Env)
        if self.debug:
            # Dev
            formatter = logging.Formatter(fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
        else:
            # Prod
            formatter = json.JsonFormatter(fmt="%(asctime)s %(levelname)s %(name)s %(message)s")

        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(self.log_level)

        # Silence noisy libraries
        logging.getLogger("uvicorn.access").handlers = []

        return self.logger
