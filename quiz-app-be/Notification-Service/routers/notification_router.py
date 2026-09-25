from fastapi import APIRouter
from schemas.notification import SendNotification
from models.notification import Notification
from datetime import datetime, timezone

router = APIRouter(
    prefix="/notification_service",
    tags=["notification"]
)


@router.post("/send")
async def send_notification(data: SendNotification):
    """Ghi thông báo kết quả bài thi vào MongoDB"""
    notification_data = {
        "student_code": data.student_code,
        "message": data.message,
        "notification_type": data.notification_type,
        "created_at": datetime.now(timezone.utc),
        "is_read": False
    }
    await Notification.create_notification(notification_data)
    return {
        "status": "success",
        "message": "Thông báo đã được gửi thành công!"
    }


@router.post("/get_notifications")
async def get_notifications(data: dict):
    """Lấy danh sách thông báo của sinh viên"""
    student_code = data.get("student_code", "")
    notifications = await Notification.get_by_student(student_code)
    return {
        "status": "success",
        "data": notifications
    }
