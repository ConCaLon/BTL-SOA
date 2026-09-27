from motor.motor_asyncio import AsyncIOMotorClient
from constants.all import MONGODB_URL


def get_test_db():
    client = AsyncIOMotorClient(MONGODB_URL or "mongodb://localhost:27017")
    return client["TestService"], client["QuestionService"]
