import time
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import (
    MobileNetV2,
    preprocess_input,
    decode_predictions
)

from app.capture.camera import Camera
from app.capture.motion import MotionDetector
from app.config import config
from app.utils.logger import get_logger
from app.uploader.retry_queue import RetryQueue
from app.uploader.worker import UploadWorker

logger = get_logger()


class Orchestrator:

    def __init__(self):
        self.camera = Camera()
        self.motion = MotionDetector()
        self.queue = RetryQueue()
        self.worker = UploadWorker()
        self.worker.start()

        logger.info("Loading MobileNetV2 model...")
        self.model = MobileNetV2(weights="imagenet")
        logger.info("MobileNetV2 model loaded successfully")

        logger.info("Orchestrator initialized")

    def classify(self, image_path):
        try:
            # Load image
            img = Image.open(image_path).convert("RGB")
            img = img.resize((224, 224))

            # Convert to numpy array
            img_array = np.array(img)
            img_array = np.expand_dims(img_array, axis=0)

            # Preprocess for MobileNetV2
            img_array = preprocess_input(img_array)

            # Run inference
            predictions = self.model.predict(img_array, verbose=0)

            # Decode top prediction
            decoded = decode_predictions(predictions, top=1)[0][0]

            species = decoded[1].replace("_", " ").title()
            confidence = float(decoded[2])

            logger.info(f"Detected {species} ({confidence:.2f})")

            return species, confidence

        except Exception as e:
            logger.error(f"Classification error: {e}")
            return "Unknown", 0.0

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