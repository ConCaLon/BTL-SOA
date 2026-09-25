from datetime import datetime, timezone
from umongo import Document, fields
from configs.database import notification_instance


@notification_instance.register
class Notification(Document):
    student_code = fields.StringField(required=True)
    message = fields.StringField(required=True)
    notification_type = fields.StringField(default="result")
    created_at = fields.DateTimeField(default=lambda: datetime.now(timezone.utc))
    is_read = fields.BooleanField(default=False)

    class Meta:
        collection_name = "notifications"

    @classmethod
    async def create_notification(cls, data: dict):
        try:
            await cls.collection.insert_one(data)
            return True
        except Exception as e:
            print(e)
            return False

    @classmethod
    async def get_by_student(cls, student_code: str):
        notifications = await cls.collection.find(
            {'student_code': student_code}
        ).sort('created_at', -1).to_list(50)
        for n in notifications:
            n["_id"] = str(n["_id"])
        return notifications
