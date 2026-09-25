from fastapi import APIRouter
from schemas.student import CreateStudent, UpdateStudent, DeleteStudent, GetStudent
from models.student import Student

router = APIRouter(
    prefix="/student_service",
    tags=["student"]
)


@router.post("/create_student")
async def create_student(data: CreateStudent):
    success, message = await Student.create_student(data.dict())
    if success:
        return {"status": "success", "message": message}
    return {"status": "failed", "message": message}


@router.put("/update_student")
async def update_student(data: UpdateStudent):
    target_code = data.old_student_code or data.student_code
    success, message = await Student.update_student(target_code, data.dict())
    if success:
        return {"status": "success", "message": message}
    return {"status": "failed", "message": message}


@router.delete("/delete_student")
async def delete_student(data: DeleteStudent):
    success = await Student.delete_student(data.student_code)
    if success:
        return {"status": "success", "message": "Xóa sinh viên thành công"}
    return {"status": "failed", "message": "Lỗi xóa sinh viên"}


@router.post("/get_student")
async def get_student(request: GetStudent):
    student = await Student.get_by_test_student_code(request)
    return {
        "status": "success",
        "data": student,
    }


@router.get("/students")
async def get_all_students():
    students = await Student.get_all_students()
    return {
        "status": "success",
        "data": students
    }
