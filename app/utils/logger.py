import logging
import os

LOG_DIR = "data/logs"
os.makedirs(LOG_DIR, exist_ok=True)

def get_logger():
    logger = logging.getLogger("wildpulse")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    # File handler
    fh = logging.FileHandler(f"{LOG_DIR}/wildpulse.log")
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger