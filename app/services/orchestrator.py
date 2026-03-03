import time
from app.capture.camera import Camera
from app.capture.motion import MotionDetector
from app.config import config
from app.utils.logger import get_logger
from app.uploader.retry_queue import RetryQueue
from app.uploader.worker import UploadWorker

from ultralytics import YOLO

logger = get_logger()


class Orchestrator:

    def __init__(self):
        self.camera = Camera()
        self.motion = MotionDetector()
        self.queue = RetryQueue()

        logger.info("Orchestrator initialized")

        logger.info("Loading YOLOv8 Nano model...")
        self.model = YOLO("yolov8n.pt")

        self.worker = UploadWorker()
        self.worker.start()

    def classify(self, image_path):
        results = self.model(image_path, verbose=False)

        if not results or len(results[0].boxes) == 0:
            logger.info("No objects detected.")
            return None, 0.0

        boxes = results[0].boxes
        names = results[0].names

        best_conf = 0
        best_label = None

        for box in boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            label = names[cls_id]

            if conf > best_conf:
                best_conf = conf
                best_label = label

        logger.info(f"Detected {best_label} ({round(best_conf, 2)})")
        return best_label, round(best_conf, 2)

    def run(self):
        logger.info("System armed. Waiting for motion...")

        while True:
            self.motion.wait_for_motion()

            image = self.camera.capture()
            if not image:
                continue

            species, confidence = self.classify(image)

            if not species:
                continue

            if confidence < config.MIN_CONFIDENCE_LOCAL:
                logger.info("Confidence below threshold. Discarding.")
                continue

            self.queue.add_event(image, species, confidence)

            time.sleep(5)