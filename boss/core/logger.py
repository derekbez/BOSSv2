"""
Central Logger for B.O.S.S.
Initializes logging for all modules, supports log rotation and configurable levels.
"""
import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'boss.log')

os.makedirs(LOG_DIR, exist_ok=True)

def get_logger(name: str = "BOSS", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = RotatingFileHandler(LOG_FILE, maxBytes=1024*1024, backupCount=3)
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger
