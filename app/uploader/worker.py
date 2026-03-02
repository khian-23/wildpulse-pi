import threading
import time
import os
import requests
from app.uploader.retry_queue import RetryQueue
from app.config import config
from app.utils.logger import get_logger

logger = get_logger()


class UploadWorker:

    def __init__(self):
        self.queue = RetryQueue()
        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        logger.info("Starting upload worker thread...")
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

    def upload_event(self, event):
        event_id, image_path, species, confidence, retry_count = event

        if not os.path.exists(image_path):
            logger.warning(f"Image not found: {image_path}")
            self.queue.mark_uploaded(event_id)
            return

        try:
            with open(image_path, "rb") as img:
                files = {
                    "image": ("capture.jpg", img, "image/jpeg")
                }
                data = {
                    "device_id": config.DEVICE_ID,
                    "species": species,
                    "confidence": float(confidence)
                }
                headers = {
                    "x-device-key": config.DEVICE_MASTER_SECRET
                }

                response = requests.post(
                    f"{config.BACKEND_URL}/captures/upload",
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=30
                )

                if response.status_code in (200, 201):
                    logger.info(f"Upload success for event {event_id} ({response.status_code})")
                    self.queue.mark_uploaded(event_id)
                    os.remove(image_path)
                else:
                    logger.warning(f"Upload failed: {response.status_code}")
                    self.queue.mark_failed(event_id)

        except Exception as e:
            logger.error(f"Upload exception: {e}")
            self.queue.mark_failed(event_id)

    def run(self):
        while self.running:
            events = self.queue.get_pending_events(limit=1)

            if not events:
                time.sleep(5)
                continue

            for event in events:
                self.upload_event(event)

            time.sleep(2)