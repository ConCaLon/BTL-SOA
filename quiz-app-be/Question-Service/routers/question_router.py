from fastapi import APIRouter, Body
from schemas.question import CreateQuestion, GetQuestions, UpdateQuestion, DeleteQuestion
from models.question import Question

router = APIRouter(
    prefix="/question_service",
    tags=["question"]
)


@router.post("/create_question")
async def create_question(data: CreateQuestion):
    success = await Question.create(data)
    if success:
        return {"status": "success", "message": "Tạo câu hỏi thành công"}
    return {"status": "failed", "message": "Lỗi tạo câu hỏi trong cơ sở dữ liệu"}


@router.post("/get_questions")
async def get_questions(request: GetQuestions):
    questions = await Question.get_by_test_id(request)
    return {
        "status": "success",
        "data": questions,
    }


@router.post("/get_questions_with_answers")
async def get_questions_with_answers(request: GetQuestions):
    """
    Lấy câu hỏi KÈM đáp án đúng — dùng nội bộ để chấm điểm và hiển thị trang Admin.
    """
    questions = await Question.get_by_test_id_with_answers(request)
    return {
        "status": "success",
        "data": questions,
    }


@router.put("/update_question")
async def update_question(data: UpdateQuestion):
    answers_list = []
    for a in data.answers:
        if hasattr(a, "dict"):
            answers_list.append(a.dict())
        elif hasattr(a, "model_dump"):
            answers_list.append(a.model_dump())
        else:
            answers_list.append(dict(a))

    update_data = {
        "text": data.text,
        "answers": answers_list
    }
    success = await Question.update_question(data.question_id, update_data)
    if success:
        return {"status": "success", "message": "Cập nhật câu hỏi thành công"}
    return {"status": "failed", "message": "Lỗi cập nhật câu hỏi"}


@router.delete("/delete_question")
async def delete_question(data: DeleteQuestion = Body(...)):
    success = await Question.delete_question(data.question_id)
    if success:
        return {"status": "success", "message": "Xóa câu hỏi thành công"}
    return {"status": "failed", "message": "Lỗi xóa câu hỏi"}


@router.get("/settings/background")
async def get_background_setting():
    try:
        db = Question.collection.database
        doc = await db["system_settings"].find_one({"key": "login_background"})
        if doc:
            return {
                "status": "success",
                "data": {
                    "image": doc.get("image", ""),
                    "dim": doc.get("dim", 40),
                    "blur": doc.get("blur", 0)
                }
            }
        return {"status": "success", "data": None}
    except Exception as e:
        return {"status": "failed", "message": str(e)}


@router.post("/settings/background")
async def save_background_setting(data: dict = Body(...)):
    try:
        db = Question.collection.database
        await db["system_settings"].update_one(
            {"key": "login_background"},
            {"$set": {
                "key": "login_background",
                "image": data.get("image", ""),
                "dim": data.get("dim", 40),
                "blur": data.get("blur", 0)
            }},
            upsert=True
        )
        return {"status": "success", "message": "Lưu cấu hình hình nền thành công"}
    except Exception as e:
        return {"status": "failed", "message": str(e)}

