import time
from app.capture.camera import Camera
from app.capture.motion import MotionDetector
from app.config import config
from app.utils.logger import get_logger
import random
from app.uploader.retry_queue import RetryQueue
from app.uploader.worker import UploadWorker
logger = get_logger()

class Orchestrator:

    def __init__(self):
        self.camera = Camera()
        self.motion = MotionDetector()
        self.queue = RetryQueue()
        logger.info("Orchestrator initialized")
        self.worker = UploadWorker()
        self.worker.start()

    def classify(self, image_path):
        # Temporary mock
        species = random.choice([
            "Visayan Spotted Deer",
            "Dog",
            "Cat"
        ])
        confidence = round(random.uniform(0.40, 0.95), 2)

        logger.info(f"Detected {species} ({confidence})")
        return species, confidence

    def run(self):
        logger.info("System armed. Waiting for motion...")

        while True:
            self.motion.wait_for_motion()

            image = self.camera.capture()
            if not image:
                continue

            species, confidence = self.classify(image)

            if confidence < config.MIN_CONFIDENCE_LOCAL:
                logger.info("Confidence below threshold. Discarding.")
                continue

            self.queue.add_event(image, species, confidence)

            # Small cooldown to prevent rapid retrigger
            time.sleep(5)