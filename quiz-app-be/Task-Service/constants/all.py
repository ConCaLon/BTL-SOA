from dotenv import load_dotenv
import os
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

FAPP_PORT = os.getenv("FAPP_PORT", "8000")
STUDENT_SERVICE_URL = os.getenv("STUDENT_SERVICE_URL", "http://127.0.0.1:8003/student_service")
TEST_SERVICE_URL = os.getenv("TEST_SERVICE_URL", "http://127.0.0.1:8002/test_service")
QUESTION_SERVICE_URL = os.getenv("QUESTION_SERVICE_URL", "http://127.0.0.1:8002/question_service")
AUTHEN_SERVICE_URL = os.getenv("AUTHEN_SERVICE_URL", "http://127.0.0.1:8001/authen_service")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://127.0.0.1:8005/notification_service")