import os
os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio"
from app.services.orchestrator import Orchestrator
from app.utils.logger import get_logger

logger = get_logger()

def main():
    logger.info("WildPulse Pi Agent Starting...")
    orchestrator = Orchestrator()
    orchestrator.run()

if __name__ == "__main__":
    main()