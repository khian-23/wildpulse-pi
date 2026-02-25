import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEVICE_ID = os.getenv("DEVICE_ID", "pi-001")
    DEVICE_SECRET = os.getenv("DEVICE_SECRET", "")
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3000")
    DEVICE_MASTER_SECRET = os.getenv("DEVICE_MASTER_SECRET", "super_secret_key")
    MIN_CONFIDENCE_LOCAL = float(os.getenv("MIN_CONFIDENCE_LOCAL", 0.50))

    HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", 60))

config = Config()