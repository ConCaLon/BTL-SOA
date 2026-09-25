from pydantic import BaseModel


class SendNotification(BaseModel):
    student_code: str
    message: str
    notification_type: str = "result"  # result, info, warning
