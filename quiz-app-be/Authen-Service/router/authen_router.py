from fastapi import APIRouter
from schemas.student import StudentInfo

router = APIRouter(
    prefix="/authen_service",
    tags=["Authen"]
)


@router.post("/validate_student")
async def validate_student(student: StudentInfo):
    """
    Xác thực sinh viên HUNRE:
    - Email: mã_sinh_viên@hunre.edu.vn (ví dụ: 2311060738@hunre.edu.vn)
    - Password: phải trùng với mã sinh viên (phần trước @)
    - Bắt buộc nhập Họ Tên và Lớp
    """
    # Lấy mã sinh viên từ email (10 chữ số trước @)
    student_code = student.email.split("@")[0]

    # Mật khẩu phải trùng với mã sinh viên trong email
    if student.password != student_code:
        return {
            "status": "failed",
            "message": "Mật khẩu phải trùng với mã sinh viên trong email!"
        }

    return {
        "status": "success",
        "message": "Xác thực thành công",
        "data": {
            "student_code": student_code,
            "email": student.email,
            "full_name": student.full_name,
            "class_name": student.class_name
        }
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
