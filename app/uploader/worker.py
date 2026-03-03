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

    def _is_upload_ack_valid(self, response):
        if response.status_code not in (200, 201):
            return False

        try:
            payload = response.json()
        except ValueError:
            logger.warning("Upload returned non-JSON success response.")
            return False

        # Accept either explicit message or saved capture object/id
        message = str(payload.get("message", "")).lower()
        capture = payload.get("capture")
        has_capture_id = isinstance(capture, dict) and (
            capture.get("_id") or capture.get("id")
        )

        # Backend can validly discard captures via rule engine; do not retry forever.
        if "capture discarded by rule engine" in message:
            return True

        return (
            "upload received" in message
            or "capture accepted" in message
            or bool(has_capture_id)
        )

    def upload_event(self, event):
        event_id, image_path, species, confidence, retry_count = event

        if not os.path.exists(image_path):
            logger.warning(f"Image not found, will retry event {event_id}: {image_path}")
            self.queue.mark_failed(event_id)
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

            if self._is_upload_ack_valid(response):
                logger.info(f"Upload success for event {event_id} ({response.status_code})")
                self.queue.mark_uploaded(event_id)
                try:
                    os.remove(image_path)
                    logger.info(f"Deleted local image after successful upload: {image_path}")
                except OSError as remove_err:
                    logger.error(f"Uploaded but failed to delete image {image_path}: {remove_err}")
            else:
                body_preview = (response.text or "")[:300]
                logger.warning(
                    f"Upload not acknowledged for event {event_id}: "
                    f"status={response.status_code}, body={body_preview}"
                )
                self.queue.mark_failed(event_id)

        except requests.RequestException as e:
            logger.error(f"Upload request exception for event {event_id}: {e}")
            self.queue.mark_failed(event_id)
        except Exception as e:
            logger.error(f"Unexpected upload exception for event {event_id}: {e}")
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
