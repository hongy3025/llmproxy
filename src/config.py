import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        self.BACKEND_URL = os.getenv("BACKEND_URL", "http://192.168.1.2:18085/v1").rstrip("/")
        self.LISTEN_HOST = os.getenv("LISTEN_HOST", "0.0.0.0")
        self.LISTEN_PORT = int(os.getenv("LISTEN_PORT", "8080"))
        self.LOG_DIR = os.getenv("LOG_DIR", "logs")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.ENABLE_CHAT_LOGS = os.getenv("ENABLE_CHAT_LOGS", "False").lower() == "true"

config = Config()
