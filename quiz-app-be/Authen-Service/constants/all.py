from dotenv import load_dotenv
import os
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

FAPP_PORT = os.getenv("FAPP_PORT", "8001")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
QLDT_LOGIN_URL = os.getenv("QLDT_LOGIN_URL", "")
QLDT_DSSV_URL = os.getenv("QLDT_DSSV_URL", "")

# Câu 6 & 7: JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "quiz-app-soa-secret-key-hunre-2024")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")