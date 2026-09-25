from .mongo_config import get_umongo_instance
from constants.all import MONGODB_URL

notification_instance = get_umongo_instance(MONGODB_URL, "NotificationService")
