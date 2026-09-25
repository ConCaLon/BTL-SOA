from dotenv import load_dotenv
import os
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

FAPP_PORT = os.getenv("FAPP_PORT")
MONGODB_URL = os.getenv("MONGODB_URL")
QLDT_LOGIN_URL=os.getenv("QLDT_LOGIN_URL")
QLDT_DSSV_URL=os.getenv("QLDT_DSSV_URL")