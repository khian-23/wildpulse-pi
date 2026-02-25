from gpiozero import MotionSensor
from app.utils.logger import get_logger

logger = get_logger()

class MotionDetector:

    def __init__(self, pin=17):
        self.sensor = MotionSensor(pin)
        logger.info(f"Motion sensor initialized on GPIO {pin}")

    def wait_for_motion(self):
        logger.info("Waiting for motion...")
        self.sensor.wait_for_motion()
        logger.info("Motion detected!")
        return True