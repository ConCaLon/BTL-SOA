"""
Proctoring Service - Dịch vụ giám sát chống gian lận thi cử
===========================================================
- Port: 8007 (Host: 127.0.0.1)
- Database: MongoDB 'ProctoringService' (độc lập hoàn toàn, không đụng chạm các DB khác)
- Quản lý cảnh báo và ghi log vi phạm thi cử (chuyển tab, thoát fullscreen, mở DevTools,...)
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pymongo
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

# ==========================================
# CẤU HÌNH BIẾN MÔI TRƯỜNG
# ==========================================
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

PORT = int(os.getenv("PORT", "8007"))
HOST = os.getenv("HOST", "127.0.0.1")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "ProctoringService")

# Client & Database references
client: Optional[AsyncIOMotorClient] = None
db = None
collection = None


# ==========================================
# LIFESPAN (KHỞI TẠO VÀ ĐÁNH INDEX MONGODB)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, db, collection
    try:
        # Khởi tạo kết nối MongoDB Async bằng Motor
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DB_NAME]
        collection = db["proctoring_logs"]

        # Tự động đánh index cho collection proctoring_logs:
        # 1. Index kép: ("test_id", 1, "student_code", 1) phục vụ truy vấn đếm vi phạm nhanh
        await collection.create_index(
            [("test_id", pymongo.ASCENDING), ("student_code", pymongo.ASCENDING)],
            name="test_student_idx",
            background=True
        )

        # 2. Index thời gian: ("created_at", -1) phục vụ sắp xếp thời gian vi phạm mới nhất
        await collection.create_index(
            [("created_at", pymongo.DESCENDING)],
            name="created_at_idx",
            background=True
        )

        print(f"[Proctoring-Service] Kết nối MongoDB thành công vào DB '{DB_NAME}' & Đã tạo index.")
    except Exception as e:
        print(f"[Proctoring-Service] Cảnh báo lỗi khởi tạo kết nối/index: {e}")

    yield

    # Đóng kết nối khi ứng dụng dừng
    if client:
        client.close()
        print("[Proctoring-Service] Đã ngắt kết nối MongoDB.")


# ==========================================
# KHỞI TẠO FASTAPI APP
# ==========================================
app = FastAPI(
    title="Proctoring Service",
    description="Dịch vụ giám sát & ghi log chống gian lận thi cử thời gian thực",
    version="1.0.0",
    lifespan=lifespan
)

# ==========================================
# CẤU HÌNH CORS
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# SCHEMAS (PYDANTIC MODELS)
# ==========================================
class ViolationLogRequest(BaseModel):
    test_id: str = Field(..., description="Mã bài thi hoặc ID bài thi")
    student_code: str = Field(..., description="Mã sinh viên")
    student_name: Optional[str] = Field(None, description="Họ tên sinh viên (tùy chọn)")
    violation_type: str = Field(
        ...,
        description="Loại vi phạm: 'TAB_SWITCH' | 'EXIT_FULLSCREEN' | 'DEVTOOLS_OPEN' hoặc khác"
    )
    details: Optional[str] = Field(None, description="Thông tin chi tiết về sự kiện vi phạm")


# ==========================================
# ENDPOINTS
# ==========================================

@app.get("/health", tags=["System"])
async def health_check():
    """Kiểm tra tình trạng hoạt động của service và kết nối cơ sở dữ liệu ProctoringService."""
    db_connected = False
    db_error = None

    if client:
        try:
            # Ping database MongoDB để xác nhận kết nối sống
            await client.admin.command("ping")
            db_connected = True
        except Exception as e:
            db_error = str(e)
    else:
        db_error = "Client chưa được khởi tạo"

    return {
        "status": "healthy" if db_connected else "unhealthy",
        "service": "Proctoring-Service",
        "port": PORT,
        "database": DB_NAME,
        "db_connected": db_connected,
        "db_error": db_error
    }


@app.post("/proctoring/log-violation", tags=["Proctoring"])
async def log_violation(data: ViolationLogRequest):
    """
    Ghi nhận hành vi vi phạm của sinh viên trong quá trình làm bài thi.
    - Đếm số lần vi phạm trước đó trong bài thi.
    - Lưu bản ghi mới kèm warning_count và timestamp.
    - Nếu warning_count >= 3 thì cờ should_terminate = True (yêu cầu thu hồi bài thi).
    """
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cơ sở dữ liệu ProctoringService chưa sẵn sàng."
        )

    try:
        # 1. Đếm số lần vi phạm trước đó của sinh viên này trong cùng đề thi
        prev_count = await collection.count_documents({
            "test_id": data.test_id,
            "student_code": data.student_code
        })

        new_warning_count = prev_count + 1
        max_warnings = 3
        should_terminate = new_warning_count >= max_warnings

        # 2. Tạo bản ghi vi phạm mới
        now = datetime.now(timezone.utc)
        record = {
            "test_id": data.test_id,
            "student_code": data.student_code,
            "student_name": data.student_name,
            "violation_type": data.violation_type,
            "details": data.details or "",
            "warning_count": new_warning_count,
            "created_at": now
        }

        insert_result = await collection.insert_one(record)

        # 3. Tạo thông báo phù hợp
        if should_terminate:
            message = (
                f"CẢNH BÁO: Sinh viên {data.student_code} đã vi phạm lần thứ {new_warning_count} "
                f"(đạt ngưỡng tối đa {max_warnings}). Bài thi sẽ bị đình chỉ và thu bài tự động!"
            )
        else:
            message = (
                f"Cảnh báo vi phạm lần {new_warning_count}/{max_warnings}: "
                f"Hành vi '{data.violation_type}' đã được ghi lại vào hệ thống giám sát."
            )

        return {
            "status": "success",
            "current_warning": new_warning_count,
            "max_warnings": max_warnings,
            "should_terminate": should_terminate,
            "message": message,
            "log_id": str(insert_result.inserted_id)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi ghi nhận vi phạm: {str(e)}"
        )


@app.get("/proctoring/violations/{test_id}", tags=["Proctoring"])
async def get_test_violations(test_id: str):
    """
    Truy vấn toàn bộ log vi phạm của đề thi theo test_id.
    - Sắp xếp bản ghi mới nhất lên đầu (created_at DESC).
    - Giới hạn tối đa 500 bản ghi.
    - Chuyển đổi ObjectId thành string và định dạng created_at thành 'HH:MM:SS DD/MM/YYYY'.
    """
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cơ sở dữ liệu ProctoringService chưa sẵn sàng."
        )

    try:
        cursor = collection.find({"test_id": test_id}).sort("created_at", pymongo.DESCENDING).limit(500)
        logs = []

        async for doc in cursor:
            created_at_val = doc.get("created_at")
            if isinstance(created_at_val, datetime):
                # Định dạng thành string 'HH:MM:SS DD/MM/YYYY'
                formatted_time = created_at_val.strftime("%H:%M:%S %d/%m/%Y")
            else:
                formatted_time = str(created_at_val) if created_at_val else ""

            logs.append({
                "id": str(doc["_id"]),
                "test_id": doc.get("test_id", ""),
                "student_code": doc.get("student_code", ""),
                "student_name": doc.get("student_name") or "",
                "violation_type": doc.get("violation_type", ""),
                "details": doc.get("details", ""),
                "warning_count": doc.get("warning_count", 0),
                "created_at": formatted_time
            })

        return {
            "status": "success",
            "test_id": test_id,
            "total": len(logs),
            "data": logs
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi truy vấn danh sách vi phạm: {str(e)}"
        )


# ==========================================
# ENTRY POINT
# ==========================================
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=True
    )
