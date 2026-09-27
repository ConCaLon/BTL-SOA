from fastapi import APIRouter, Body
from models.test import Test
from schemas.test import CreateTest, UpdateTest, DeleteTest, GetTestByCode, SubmitExam, CascadeUpdateStudent

router = APIRouter(
    prefix="/test_service",
    tags=["test"]
)


@router.get("/tests")
async def get_all_tests():
    """Lấy danh sách tất cả mã đề thi"""
    try:
        tests = await Test.get_all_tests()
        return {
            "status": "success",
            "data": tests
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Lỗi lấy danh sách bài thi: {str(e)}"
        }


@router.post("/create_test")
async def create_test(data: CreateTest):
    """Tạo mới một mã đề thi"""
    try:
        success, message, created_doc = await Test.create_test(data.dict())
        if success:
            return {
                "status": "success",
                "message": message,
                "data": created_doc
            }
        return {
            "status": "failed",
            "message": message
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Lỗi tạo bài thi: {str(e)}"
        }


@router.put("/update_test")
async def update_test(data: UpdateTest):
    """Cập nhật thông tin mã đề thi"""
    try:
        success, message = await Test.update_test(data.test_id, data.dict())
        if success:
            return {
                "status": "success",
                "message": message
            }
        return {
            "status": "failed",
            "message": message
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Lỗi cập nhật bài thi: {str(e)}"
        }


@router.delete("/delete_test")
async def delete_test(data: DeleteTest = Body(...)):
    """Xóa mã đề thi và các câu hỏi liên quan"""
    try:
        success, message = await Test.delete_test(data.test_id)
        if success:
            return {
                "status": "success",
                "message": message
            }
        return {
            "status": "failed",
            "message": message
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Lỗi xóa bài thi: {str(e)}"
        }


@router.post("/get_test_by_code")
async def get_test_by_code(data: GetTestByCode):
    """Lấy thông tin bài thi bằng mã đề"""
    try:
        test = await Test.get_by_code(data.test_code)
        if not test:
            return {
                "status": "failed",
                "message": f"Mã đề '{data.test_code}' không tồn tại!"
            }
        return {
            "status": "success",
            "data": {
                "test": test
            }
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Lỗi tìm bài thi: {str(e)}"
        }


@router.post("/get_test")
async def get_test(data: dict):
    """Lấy thông tin bài thi bằng ID"""
    try:
        test_id = data.get("id") or data.get("test_id")
        test = await Test.get_by_id(test_id)
        if not test:
            return {
                "status": "failed",
                "message": "Không tìm thấy bài thi!"
            }
        return {
            "status": "success",
            "data": test
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Lỗi lấy bài thi: {str(e)}"
        }


@router.post("/submit_exam")
async def submit_exam(data: SubmitExam):
    """Nộp bài thi, chấm điểm và lưu kết quả"""
    try:
        answers_dict = [a.dict() for a in data.answers]
        result = await Test.submit_exam(data.student_code, data.test_id, answers_dict)
        return {
            "status": "success",
            "message": "Nộp bài thành công!",
            "data": result
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Lỗi nộp bài thi: {str(e)}"
        }


@router.get("/submissions")
async def get_all_submissions():
    """Lấy toàn bộ kết quả nộp bài cho Admin"""
    try:
        subs = await Test.get_all_submissions()
        return {
            "status": "success",
            "data": subs
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Lỗi lấy kết quả bài thi: {str(e)}"
        }


@router.get("/submissions/{student_code}")
async def get_student_submissions(student_code: str):
    """Lấy lịch sử thi của sinh viên"""
    try:
        subs = await Test.get_student_history(student_code)
        return {
            "status": "success",
            "data": subs
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Lỗi lấy lịch sử sinh viên: {str(e)}"
        }


@router.put("/cascade_update_student_code")
async def cascade_update_student_code(data: CascadeUpdateStudent):
    """Đồng bộ mã sinh viên sang danh sách đề thi và bài nộp"""
    try:
        await Test.cascade_update_student_code(data.old_student_code, data.new_student_code)
        return {
            "status": "success",
            "message": "Đồng bộ mã sinh viên thành công"
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Lỗi đồng bộ mã sinh viên: {str(e)}"
        }
