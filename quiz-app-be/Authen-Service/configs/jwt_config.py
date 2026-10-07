"""
JWT Configuration & Utilities for Authen-Service
=================================================
Câu 6: JWT Authentication - Phát token khi xác thực thành công
Câu 7: Token Revocation - Denylist theo jti, refresh token
"""


import jwt
import uuid
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from constants.all import MONGODB_URL, JWT_SECRET, JWT_ALGORITHM

# ==========================================
# KẾT NỐI MONGODB CHO DENYLIST
# ==========================================
client = AsyncIOMotorClient(MONGODB_URL or "mongodb://localhost:27017")
auth_db = client["AuthenService"]
revoked_tokens_col = auth_db["revoked_tokens"]

# ==========================================
# CẤU HÌNH TOKEN
# ==========================================
ACCESS_TOKEN_EXPIRE_MINUTES = 60      # Token ngắn hạn: 60 phút
REFRESH_TOKEN_EXPIRE_DAYS = 7         # Refresh token: 7 ngày


# ==========================================
# TẠO TOKEN
# ==========================================
def create_access_token(student_code: str, role: str = "student") -> str:
    """Tạo access token ngắn hạn với jti unique"""
    jti = str(uuid.uuid4())
    payload = {
        "sub": student_code,
        "role": role,
        "jti": jti,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(student_code: str, role: str = "student") -> str:
    """Tạo refresh token dài hạn với jti unique"""
    jti = str(uuid.uuid4())
    payload = {
        "sub": student_code,
        "role": role,
        "jti": jti,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# ==========================================
# GIẢI MÃ & XÁC THỰC TOKEN
# ==========================================
def decode_token(token: str) -> dict:
    """Giải mã JWT token, raise exception nếu hết hạn hoặc không hợp lệ"""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


async def is_token_revoked(jti: str) -> bool:
    """Kiểm tra token đã bị thu hồi chưa (denylist theo jti)"""
    doc = await revoked_tokens_col.find_one({"jti": jti})
    return doc is not None


async def revoke_token(jti: str):
    """Thu hồi token bằng cách thêm jti vào denylist"""
    await revoked_tokens_col.update_one(
        {"jti": jti},
        {"$set": {"jti": jti, "revoked_at": datetime.now(timezone.utc)}},
        upsert=True
    )


async def validate_and_decode(token: str) -> dict:
    """
    Xác thực token đầy đủ:
    1. Giải mã JWT (kiểm tra chữ ký + hạn)
    2. Kiểm tra denylist (token đã bị thu hồi chưa)
    """
    try:
        payload = decode_token(token)
        jti = payload.get("jti")
        if jti and await is_token_revoked(jti):
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
