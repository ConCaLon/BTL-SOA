from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from schemas.task import StartTest, SubmitTest
from constants.all import QUESTION_SERVICE_URL, TEST_SERVICE_URL, STUDENT_SERVICE_URL, AUTHEN_SERVICE_URL, NOTIFICATION_SERVICE_URL
from configs.socket_manager import ConnectionManager
import httpx
import ssl

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

router = APIRouter(
    prefix="/task_service",
    tags=["task"]
)

manager = ConnectionManager()


@router.websocket("/ws/status/{student_code}")
async def websocket_endpoint(websocket: WebSocket, student_code: str):
    await manager.connect(websocket, student_code)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(data, student_code)
    except WebSocketDisconnect:
        manager.disconnect(student_code)


@router.post("/start_test")
async def start_test(data: StartTest):
    # Lấy mã sinh viên từ email
    student_code = data.email.lower().split("@")[0]

    async with httpx.AsyncClient(verify=False) as client:
        await manager.send_personal_message("Đang xác thực sinh viên...", student_code)

        authen_response = await client.post(
            url=f'{AUTHEN_SERVICE_URL}/validate_student',
            json={
                "email": data.email,
                "password": data.password,
                "full_name": data.full_name,
                "class_name": data.class_name
            }
        )

    if authen_response.status_code != 200:
        return {
            "status": "failed",
            "message": f"Lỗi xác thực (Mã {authen_response.status_code}): {authen_response.text}"
        }

    if authen_response.json().get("status") == "failed":
        error_msg = authen_response.json().get("message", "Xác thực thất bại!")
        return {
            "status": "failed",
            "message": error_msg
        }

    async with httpx.AsyncClient(verify=False) as client:
        await manager.send_personal_message("Đang lấy thông tin sinh viên...", student_code)

        # Tạo sinh viên nếu chưa tồn tại, rồi lấy thông tin
        await client.post(
            url=f'{STUDENT_SERVICE_URL}/create_student',
            json={
                "student_code": student_code,
                "student_name": data.full_name,
                "name": data.full_name,
                "class_name": data.class_name
            }
        )

        student_response = await client.post(
            url=f'{STUDENT_SERVICE_URL}/get_student',
            json={"student_code": student_code}
        )

    if student_response.status_code != 200:
        return {
            "status": "failed",
            "message": "Không tìm thấy thông tin sinh viên!"
        }

    async with httpx.AsyncClient(verify=False) as client:
        await manager.send_personal_message("Đang lấy thông tin bài thi...", student_code)

        test_response = await client.post(
            url=f'{TEST_SERVICE_URL}/get_test_by_code',
            json={"test_code": data.test_code}
        )

    if test_response.status_code != 200 or test_response.json().get("status") == "failed":
        return {
            "status": "failed",
            "message": "Mã đề không tồn tại!"
        }

    test_data = test_response.json()["data"]
    test = test_data["test"]
    student = student_response.json()["data"]
    
    # Hỗ trợ cả list_student và list_students
    allowed_students = test.get('list_students') or test.get('list_student') or []
    
    # Nếu danh sách được cấu hình (không rỗng) thì mới kiểm tra
    if len(allowed_students) > 0 and student.get('student_code') not in allowed_students:
        return {
            "status": "failed",
            "message": "Sinh viên không có quyền truy cập bài thi này!"
        }

    # Lấy ID của test để truyền đi lấy câu hỏi
    test_id = test["_id"]

    async with httpx.AsyncClient(verify=False) as client:
        await manager.send_personal_message("Đang lấy câu hỏi...", student_code)

        questions_response = await client.post(
            url=f'{QUESTION_SERVICE_URL}/get_questions',
            json={"test_id": test_id}
        )

    if questions_response.status_code != 200:
        return {
            "status": "failed",
            "message": "Không tìm thấy câu hỏi!"
        }

    # Thêm class_name vào student data trả về
    student_data = student_response.json()["data"]
    student_data["class_name"] = data.class_name

    return {
        "status": "success",
        "data": {
            "test": test,
            "questions": questions_response.json()["data"],
            "student": student_data
        }
    }


@router.post("/submit_test")
async def submit_test(data: SubmitTest):
    """
    Orchestrator: Nhận bài làm từ frontend → chuyển tiếp đến Test-Service để chấm điểm.
    """
    async with httpx.AsyncClient(verify=False) as client:
        await manager.send_personal_message("Đang nộp bài...", data.student_code)

        submit_response = await client.post(
            url=f'{TEST_SERVICE_URL}/submit_exam',
            json={
                "student_code": data.student_code,
                "test_id": data.test_id,
                "answers": [a.dict() for a in data.answers]
            }
        )

    if submit_response.status_code != 200:
        return {
            "status": "failed",
            "message": "Lỗi khi nộp bài!"
        }

    result = submit_response.json()

    if result.get("status") == "success":
        await manager.send_personal_message("Nộp bài thành công!", data.student_code)

        # Gửi thông báo kết quả qua Notification Service
        try:
            score = result.get("data", {}).get("score", 0)
            correct = result.get("data", {}).get("correct_count", 0)
            total = result.get("data", {}).get("total_questions", 0)
            async with httpx.AsyncClient(verify=False) as client:
                await client.post(
                    url=f'{NOTIFICATION_SERVICE_URL}/send',
                    json={
                        "student_code": data.student_code,
                        "message": f"Kết quả bài thi: {score}/10 ({correct}/{total} câu đúng)",
                        "notification_type": "result"
                    }
                )
        except Exception as e:
            print(f"Notification error: {e}")
            
    return result

@router.get("/admin/students")
async def admin_get_students():
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(f'{STUDENT_SERVICE_URL}/students')
    if response.status_code == 200:
        return response.json()
    return {"status": "failed", "message": "Lỗi lấy danh sách sinh viên"}


@router.post("/admin/students/create")
async def admin_create_student(data: dict):
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            url=f'{STUDENT_SERVICE_URL}/create_student',
            json=data
        )
    if response.status_code == 200:
        return response.json()
    return {"status": "failed", "message": "Lỗi tạo sinh viên"}


@router.put("/admin/students/update")
async def admin_update_student(data: dict):
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.put(
            url=f'{STUDENT_SERVICE_URL}/update_student',
            json=data
        )
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("status") == "success":
                old_code = data.get("old_student_code")
                new_code = data.get("student_code")
                if old_code and new_code and old_code != new_code:
                    try:
                        await client.put(
                            url=f'{TEST_SERVICE_URL}/cascade_update_student_code',
                            json={"old_student_code": old_code, "new_student_code": new_code}
                        )
                    except Exception as e:
                        print(f"Lỗi đồng bộ MSV sang Test-Service: {e}")
            return res_json
    return {"status": "failed", "message": "Lỗi cập nhật sinh viên"}


@router.delete("/admin/students/delete")
async def admin_delete_student(data: dict):
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.request(
            method="DELETE",
            url=f'{STUDENT_SERVICE_URL}/delete_student',
            json=data
        )
    if response.status_code == 200:
        return response.json()
    return {"status": "failed", "message": "Lỗi xóa sinh viên"}



@router.get("/student/history/{student_code}")
async def get_student_history(student_code: str):
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(f'{TEST_SERVICE_URL}/submissions/{student_code}')
    if response.status_code == 200:
        return response.json()
    return {"status": "failed", "message": "Lỗi lấy lịch sử bài thi sinh viên"}


@router.get("/admin/results")
async def admin_get_results():
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(f'{TEST_SERVICE_URL}/submissions')
    if response.status_code == 200:
        return response.json()
    return {"status": "failed", "message": "Lỗi lấy kết quả thi"}



@router.post("/admin/questions")
async def admin_get_questions(data: dict):
    # Dùng test_id để lấy toàn bộ câu hỏi kèm đáp án
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            url=f'{QUESTION_SERVICE_URL}/get_questions_with_answers',
            json={"test_id": data.get("test_id")}
        )
    if response.status_code == 200:
        return response.json()
    return {"status": "failed", "message": "Lỗi lấy câu hỏi"}


@router.post("/admin/questions/create")
async def admin_create_question(data: dict):
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            url=f'{QUESTION_SERVICE_URL}/create_question',
            json=data
        )
    if response.status_code == 200:
        return response.json()
    return {"status": "failed", "message": "Lỗi tạo câu hỏi"}


@router.put("/admin/questions/update")
async def admin_update_question(data: dict):
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.put(
            url=f'{QUESTION_SERVICE_URL}/update_question',
            json=data
        )
    if response.status_code == 200:
        return response.json()
    return {"status": "failed", "message": "Lỗi cập nhật câu hỏi"}


@router.delete("/admin/questions/delete")
async def admin_delete_question(data: dict):
    async with httpx.AsyncClient(verify=False) as client:
        # httpx delete không hỗ trợ body JSON mặc định tốt, nên dùng request method
        response = await client.request(
            method="DELETE",
            url=f'{QUESTION_SERVICE_URL}/delete_question',
            json=data
        )
    if response.status_code == 200:
        return response.json()
    return {"status": "failed", "message": "Lỗi xóa câu hỏi"}


# ==========================================
# ADMIN TESTS CRUD (MÃ ĐỀ)
# ==========================================
@router.get("/admin/tests")
async def admin_get_tests():
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(f'{TEST_SERVICE_URL}/tests')
    if response.status_code == 200:
        return response.json()
    return {"status": "failed", "message": "Lỗi lấy danh sách bài thi"}

@router.post("/admin/tests/create")
async def admin_create_test(data: dict):
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            url=f'{TEST_SERVICE_URL}/create_test',
            json=data
        )
    if response.status_code == 200:
        return response.json()
    return {"status": "failed", "message": "Lỗi tạo bài thi"}

@router.put("/admin/tests/update")
async def admin_update_test(data: dict):
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.put(
            url=f'{TEST_SERVICE_URL}/update_test',
            json=data
        )
    if response.status_code == 200:
        return response.json()
    return {"status": "failed", "message": "Lỗi cập nhật bài thi"}

@router.delete("/admin/tests/delete")
async def admin_delete_test(data: dict):
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.request(
            method="DELETE",
            url=f'{TEST_SERVICE_URL}/delete_test',
            json=data
        )
    if response.status_code == 200:
        return response.json()
    return {"status": "failed", "message": "Lỗi xóa bài thi"}
