from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from schemas.task import StartTest, SubmitTest
from constants.all import QUESTION_SERVICE_URL, TEST_SERVICE_URL, STUDENT_SERVICE_URL, AUTHEN_SERVICE_URL, NOTIFICATION_SERVICE_URL, REPORT_SERVICE_URL
from configs.socket_manager import ConnectionManager
import httpx
import ssl
import asyncio
from datetime import datetime

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
    """Lấy danh sách bài nộp kèm tên bài thi và họ tên sinh viên cho Admin Dashboard"""
    try:
        async with httpx.AsyncClient(verify=False) as client:
            # Gọi song song 3 service để lấy submissions, tests, students
            sub_res, test_res, stu_res = await asyncio.gather(
                client.get(f'{TEST_SERVICE_URL}/submissions'),
                client.get(f'{TEST_SERVICE_URL}/tests'),
                client.get(f'{STUDENT_SERVICE_URL}/students'),
                return_exceptions=True
            )

        # Parse submissions
        if isinstance(sub_res, Exception) or sub_res.status_code != 200:
            return {"status": "failed", "message": "Lỗi lấy kết quả thi"}

        sub_data = sub_res.json()
        if sub_data.get("status") != "success":
            return sub_data

        submissions = sub_data.get("data", [])

        # Build test_id -> title map từ Test-Service
        test_map = {}
        if not isinstance(test_res, Exception) and test_res.status_code == 200:
            test_json = test_res.json()
            if test_json.get("status") == "success":
                for t in test_json.get("data", []):
                    test_map[t.get("_id", "")] = t.get("name", "")

        # Build student_code -> student_name map từ Student-Service
        student_map = {}
        if not isinstance(stu_res, Exception) and stu_res.status_code == 200:
            stu_json = stu_res.json()
            if stu_json.get("status") == "success":
                for s in stu_json.get("data", []):
                    code = s.get("student_code", "")
                    if code:
                        student_map[code] = s.get("student_name") or s.get("name") or ""

        # Ghép dữ liệu trả về cho frontend
        enriched = []
        for s in submissions:
            test_id = s.get("test_id", "")
            student_code = s.get("student_code", "")

            # Định dạng submitted_at thành dd/mm/yyyy hh:mm:ss
            submitted_at_raw = s.get("submitted_at", "")
            submitted_at_formatted = submitted_at_raw
            try:
                if submitted_at_raw:
                    dt = datetime.fromisoformat(submitted_at_raw.replace("Z", "+00:00"))
                    submitted_at_formatted = dt.strftime("%d/%m/%Y %H:%M:%S")
            except Exception:
                pass

            enriched.append({
                "id": s.get("_id", ""),
                "student_code": student_code,
                "student_name": student_map.get(student_code, ""),
                "test_id": test_id,
                "test_title": test_map.get(test_id, test_id),
                "score": s.get("score", 0),
                "correct_answers": s.get("correct_count", 0),
                "total_questions": s.get("total_questions", 0),
                "submitted_at": submitted_at_formatted
            })

        return {
            "status": "success",
            "data": enriched
        }
    except Exception as e:
        return {"status": "failed", "message": f"Lỗi lấy kết quả thi: {str(e)}"}



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
    try:
        msg = response.json().get("message", "Lỗi lấy câu hỏi")
    except Exception:
        msg = "Lỗi lấy câu hỏi"
    return {"status": "failed", "message": msg}


@router.post("/admin/questions/create")
async def admin_create_question(data: dict):
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            url=f'{QUESTION_SERVICE_URL}/create_question',
            json=data
        )
    if response.status_code == 200:
        return response.json()
    try:
        msg = response.json().get("message", "Lỗi tạo câu hỏi")
    except Exception:
        msg = "Lỗi tạo câu hỏi"
    return {"status": "failed", "message": msg}


@router.put("/admin/questions/update")
async def admin_update_question(data: dict):
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.put(
            url=f'{QUESTION_SERVICE_URL}/update_question',
            json=data
        )
    if response.status_code == 200:
        return response.json()
    try:
        msg = response.json().get("message", "Lỗi cập nhật câu hỏi")
    except Exception:
        msg = "Lỗi cập nhật câu hỏi"
    return {"status": "failed", "message": msg}


@router.delete("/admin/questions/delete")
async def admin_delete_question(data: dict):
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.request(
            method="DELETE",
            url=f'{QUESTION_SERVICE_URL}/delete_question',
            json=data
        )
    if response.status_code == 200:
        return response.json()
    try:
        msg = response.json().get("message", "Lỗi xóa câu hỏi")
    except Exception:
        msg = "Lỗi xóa câu hỏi"
    return {"status": "failed", "message": msg}


# ==========================================
# ADMIN TESTS CRUD (MÃ ĐỀ)
# ==========================================
@router.get("/admin/tests")
async def admin_get_tests():
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(f'{TEST_SERVICE_URL}/tests')
    if response.status_code == 200:
        return response.json()
    try:
        msg = response.json().get("message", "Lỗi lấy danh sách bài thi")
    except Exception:
        msg = "Lỗi lấy danh sách bài thi"
    return {"status": "failed", "message": msg}

@router.post("/admin/tests/create")
async def admin_create_test(data: dict):
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            url=f'{TEST_SERVICE_URL}/create_test',
            json=data
        )
    if response.status_code == 200:
        return response.json()
    try:
        msg = response.json().get("message", "Lỗi tạo bài thi")
    except Exception:
        msg = "Lỗi tạo bài thi"
    return {"status": "failed", "message": msg}

@router.put("/admin/tests/update")
async def admin_update_test(data: dict):
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.put(
            url=f'{TEST_SERVICE_URL}/update_test',
            json=data
        )
    if response.status_code == 200:
        return response.json()
    try:
        msg = response.json().get("message", "Lỗi cập nhật bài thi")
    except Exception:
        msg = "Lỗi cập nhật bài thi"
    return {"status": "failed", "message": msg}

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
    try:
        msg = response.json().get("message", "Lỗi xóa bài thi")
    except Exception:
        msg = "Lỗi xóa bài thi"
    return {"status": "failed", "message": msg}


@router.get("/settings/background")
async def get_background_setting():
    async with httpx.AsyncClient(verify=False) as client:
        try:
            response = await client.get(
                url=f'{QUESTION_SERVICE_URL}/settings/background',
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
    return {"status": "failed", "message": "Không thể lấy cấu hình ảnh nền"}


@router.post("/settings/background")
async def save_background_setting(data: dict):
    async with httpx.AsyncClient(verify=False) as client:
        try:
            response = await client.post(
                url=f'{QUESTION_SERVICE_URL}/settings/background',
                json=data,
                timeout=15.0
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            return {"status": "failed", "message": f"Lỗi lưu ảnh nền: {str(e)}"}
    return {"status": "failed", "message": "Không thể lưu cấu hình ảnh nền"}


# ==========================================
# REPORT SERVICE (Xuất báo cáo / bảng điểm)
# ==========================================

@router.get("/report/export/all")
async def report_export_all():
    """Xuất toàn bộ bảng điểm tất cả bài thi ra Excel."""
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        response = await client.get(f"{REPORT_SERVICE_URL}/export/all")
    if response.status_code == 200:
        from fastapi.responses import StreamingResponse
        import io
        filename = response.headers.get("content-disposition", "attachment; filename=report.xlsx")
        return StreamingResponse(
            io.BytesIO(response.content),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": filename}
        )
    return {"status": "failed", "message": "Lỗi xuất báo cáo tổng hợp"}


@router.get("/report/export/by_test/{test_id}")
async def report_export_by_test(test_id: str):
    """Xuất bảng điểm của một bài thi cụ thể (theo test_id)."""
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        response = await client.get(f"{REPORT_SERVICE_URL}/export/by_test/{test_id}")
    if response.status_code == 200:
        from fastapi.responses import StreamingResponse
        import io
        filename = response.headers.get("content-disposition", f"attachment; filename=BangDiem_{test_id}.xlsx")
        return StreamingResponse(
            io.BytesIO(response.content),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": filename}
        )
    return {"status": "failed", "message": "Lỗi xuất báo cáo bài thi"}


@router.get("/report/export/by_student/{student_code}")
async def report_export_by_student(student_code: str):
    """Xuất lịch sử thi của một sinh viên."""
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        response = await client.get(f"{REPORT_SERVICE_URL}/export/by_student/{student_code}")
    if response.status_code == 200:
        from fastapi.responses import StreamingResponse
        import io
        filename = response.headers.get("content-disposition", f"attachment; filename=LichSuThi_{student_code}.xlsx")
        return StreamingResponse(
            io.BytesIO(response.content),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": filename}
        )
    return {"status": "failed", "message": "Lỗi xuất lịch sử thi sinh viên"}


@router.get("/report/stats")
async def report_stats():
    """Lấy thống kê tổng hợp (JSON) để hiển thị trên dashboard."""
    async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
        try:
            response = await client.get(f"{REPORT_SERVICE_URL}/stats")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            return {"status": "failed", "message": f"Lỗi kết nối Report Service: {str(e)}"}
    return {"status": "failed", "message": "Lỗi lấy thống kê"}
