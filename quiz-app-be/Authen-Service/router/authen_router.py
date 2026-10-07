"""
Authen-Service Router
=====================
Câu 6: JWT Authentication - Phát access token + refresh token khi xác thực thành công
Câu 7: Token Revocation - Thu hồi token qua denylist, refresh token
"""

from fastapi import APIRouter
from schemas.student import StudentInfo
from configs.jwt_config import (
    create_access_token, create_refresh_token,
    validate_and_decode, revoke_token
)
from constants.all import ADMIN_USERNAME, ADMIN_PASSWORD

router = APIRouter(
    prefix="/authen_service",
    tags=["Authen"]
)


@router.post("/validate_student")
async def validate_student(student: StudentInfo):
    """
    Xác thực sinh viên HUNRE (Câu 3: Tập trung validate tại Authen-Service):
    - Email: mã_sinh_viên@hunre.edu.vn (ví dụ: 2311060738@hunre.edu.vn)
    - Password: phải trùng với mã sinh viên (phần trước @)
    - Bắt buộc nhập Họ Tên và Lớp
    - Phát JWT token nếu xác thực thành công (Câu 6)
    """
    # Lấy mã sinh viên từ email (10 chữ số trước @)
    student_code = student.email.split("@")[0]

    # Mật khẩu phải trùng với mã sinh viên trong email
    if student.password != student_code:
        return {
            "status": "failed",
            "message": "Mật khẩu phải trùng với mã sinh viên trong email!"
        }

    # Câu 6: Phát JWT token khi xác thực thành công
    access_token = create_access_token(student_code, role="student")
    refresh_token = create_refresh_token(student_code, role="student")

    return {
        "status": "success",
        "message": "Xác thực thành công",
        "data": {
            "student_code": student_code,
            "email": student.email,
            "full_name": student.full_name,
            "class_name": student.class_name
        },
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.post("/admin/login")
async def admin_login(data: dict):
    """
    Câu 6: Đăng nhập Admin → phát JWT với role=admin
    """
    username = data.get("username", "")
    password = data.get("password", "")

    if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
        return {
            "status": "failed",
            "message": "Tên đăng nhập hoặc mật khẩu Admin không đúng!"
        }

    access_token = create_access_token(username, role="admin")
    refresh_token = create_refresh_token(username, role="admin")

    return {
        "status": "success",
        "message": "Đăng nhập Admin thành công",
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.post("/refresh_token")
async def refresh_token_endpoint(data: dict):
    """
    Câu 7: Refresh token → cấp access token mới khi token cũ hết hạn
    """
    token = data.get("refresh_token", "")
    if not token:
        return {"status": "failed", "message": "Thiếu refresh token!"}

    payload = await validate_and_decode(token)
    if payload is None:
        return {"status": "failed", "message": "Refresh token không hợp lệ hoặc đã bị thu hồi!"}

    if payload.get("type") != "refresh":
        return {"status": "failed", "message": "Token không phải loại refresh!"}

    # Cấp access token mới
    student_code = payload.get("sub", "")
    role = payload.get("role", "student")
    new_access_token = create_access_token(student_code, role=role)

    return {
        "status": "success",
        "access_token": new_access_token
    }


@router.post("/revoke_token")
async def revoke_token_endpoint(data: dict):
    """
    Câu 7: Thu hồi token còn hạn → thêm jti vào denylist
    Dùng khi: đăng xuất, phát hiện token bị lộ, thay đổi quyền
    """
    token = data.get("token", "")
    if not token:
        return {"status": "failed", "message": "Thiếu token cần thu hồi!"}

    payload = await validate_and_decode(token)
    if payload is None:
        return {"status": "failed", "message": "Token không hợp lệ hoặc đã hết hạn!"}

    jti = payload.get("jti")
    if jti:
        await revoke_token(jti)

    return {
        "status": "success",
        "message": "Token đã được thu hồi thành công"
    }


@router.post("/verify_eligibility")
async def verify_eligibility(data: dict):
    """
    Verify Microservice (theo README mục 11 & 12):
    Xác minh sinh viên có quyền thi hay không.
    Input: student_code, list_students (danh sách SV được phép thi)
    """
    student_code = data.get("student_code", "")
    list_students = data.get("list_students", [])

    if not student_code:
        return {
            "status": "failed",
            "eligible": False,
            "message": "Thiếu mã sinh viên!"
        }

    if student_code in list_students:
        return {
            "status": "success",
            "eligible": True,
            "message": "Sinh viên được phép thi"
        }
    else:
        return {
            "status": "failed",
            "eligible": False,
            "message": "Sinh viên không nằm trong danh sách được phép thi!"
        }
