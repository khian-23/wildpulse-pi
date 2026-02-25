import subprocess
import os
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger()

IMAGE_DIR = "data/images"
os.makedirs(IMAGE_DIR, exist_ok=True)


class Camera:

    def capture(self):
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{IMAGE_DIR}/capture_{timestamp}.jpg"

        command = [
            "rpicam-still",
            "--zsl",
            "-o", filename,
            "--timeout", "1000",
            "--nopreview"
        ]

        try:
            subprocess.run(command, check=True)
            logger.info(f"Image saved: {filename}")
            return filename
        except subprocess.CalledProcessError as e:
            logger.error(f"Camera capture failed: {e}")
            return None