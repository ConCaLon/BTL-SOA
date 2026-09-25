from .mongo_config import get_umongo_instance
from constants.all import MONGODB_URL

question_instance = get_umongo_instance(MONGODB_URL, "QuestionService")