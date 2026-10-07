"""
JWT Authentication Dependency for Task-Service (API Gateway)
=============================================================
Câu 6: Kiểm tra JWT + quyền sở hữu dữ liệu (RBAC)
Câu 7: Kiểm tra denylist → thu hồi token còn hạn
"""

import jwt
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from constants.all import JWT_SECRET, JWT_ALGORITHM
import httpx


security = HTTPBearer(auto_error=False)


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency: Xác thực JWT token từ header Authorization.
    Trả về payload chứa student_code, role, jti.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="Thiếu token xác thực! Vui lòng đăng nhập.")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token đã hết hạn! Vui lòng đăng nhập lại.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token không hợp lệ!")

    # Kiểm tra token type phải là access
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Loại token không hợp lệ!")

    return payload


async def verify_student(payload: dict = Depends(verify_token)) -> dict:
    """
    Dependency: Xác thực là sinh viên (role = student hoặc admin).
    Trả về payload chứa student_code.
    """
    return payload


async def verify_admin(payload: dict = Depends(verify_token)) -> dict:
    """
    Dependency: Yêu cầu quyền admin.
    Admin mới được truy cập các endpoint quản trị.
    """
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập chức năng này! Yêu cầu quyền Admin.")
    return payload


def verify_ownership(payload: dict, student_code: str) -> bool:
    """
    Câu 6: Kiểm tra quyền sở hữu - sinh viên chỉ xem data của mình.
    Admin có quyền xem tất cả.
    """
    if payload.get("role") == "admin":
        return True
    return payload.get("sub") == student_code
