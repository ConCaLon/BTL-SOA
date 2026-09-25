from fastapi import APIRouter
from schemas.question import CreateQuestion, GetQuestions, UpdateQuestion, DeleteQuestion
from models.question import Question

router = APIRouter(
    prefix="/question_service",
    tags=["question"]
)


@router.post("/create_question")
async def create_question(data: CreateQuestion):
    await Question.create(data)
    return {"message": "Question created successfully"}


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
    Lấy câu hỏi KÈM đáp án đúng — chỉ dùng nội bộ (server-to-server) để chấm điểm.
    Không gọi từ frontend.
    """
    questions = await Question.get_by_test_id_with_answers(request)
    return {
        "status": "success",
        "data": questions,
    }


@router.put("/update_question")
async def update_question(data: UpdateQuestion):
    from schemas.question import UpdateQuestion
    update_data = {
        "text": data.text,
        "answers": [a.dict() for a in data.answers]
    }
    success = await Question.update_question(data.question_id, update_data)
    if success:
        return {"status": "success", "message": "Cập nhật câu hỏi thành công"}
    return {"status": "failed", "message": "Lỗi cập nhật câu hỏi"}


@router.delete("/delete_question")
async def delete_question(data: DeleteQuestion):
    from schemas.question import DeleteQuestion
    success = await Question.delete_question(data.question_id)
    if success:
        return {"status": "success", "message": "Xóa câu hỏi thành công"}
    return {"status": "failed", "message": "Lỗi xóa câu hỏi"}
