import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BACKEND_URL = os.getenv("BACKEND_URL", "http://192.168.1.2:18085/v1").rstrip("/")
    LISTEN_HOST = os.getenv("LISTEN_HOST", "0.0.0.0")
    LISTEN_PORT = int(os.getenv("LISTEN_PORT", "8080"))
    LOG_DIR = os.getenv("LOG_DIR", "logs")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

config = Config()
