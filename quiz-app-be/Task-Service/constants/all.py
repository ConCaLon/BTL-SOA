from dotenv import load_dotenv
import os
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

FAPP_PORT = os.getenv("FAPP_PORT")
STUDENT_SERVICE_URL = os.getenv("STUDENT_SERVICE_URL")
TEST_SERVICE_URL = os.getenv("TEST_SERVICE_URL")
QUESTION_SERVICE_URL= os.getenv("QUESTION_SERVICE_URL")
AUTHEN_SERVICE_URL = os.getenv("AUTHEN_SERVICE_URL")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL")