from dotenv import load_dotenv
import os
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

FAPP_PORT = os.getenv("FAPP_PORT", "8006")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
QUESTION_SERVICE_URL = os.getenv("QUESTION_SERVICE_URL", "http://127.0.0.1:8002/question_service")
