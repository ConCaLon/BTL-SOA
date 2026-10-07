from pydantic import BaseModel
from typing import Optional, List, Union


class CreateTest(BaseModel):
    test_code: str
    name: str
    time: Union[int, str] = 45
    list_students: Optional[List[str]] = []
    # Câu 5: Giới hạn số lượng sinh viên được thi
    max_students: Optional[int] = 0  # 0 = không giới hạn


class UpdateTest(BaseModel):
    test_id: str
    test_code: str
    name: str
    time: Union[int, str] = 45
    list_students: Optional[List[str]] = []
    # Câu 5: Giới hạn số lượng sinh viên được thi
    max_students: Optional[int] = 0  # 0 = không giới hạn


class DeleteTest(BaseModel):
    test_id: str


class GetTestByCode(BaseModel):
    test_code: str


class SubmitAnswerItem(BaseModel):
    question_id: str
    selected_answer: Optional[str] = ""


class SubmitExam(BaseModel):
    student_code: str
    test_id: str
    answers: List[SubmitAnswerItem] = []
    # Câu 9: Idempotency key để ngăn nộp bài trùng
    idempotency_key: Optional[str] = ""


class CascadeUpdateStudent(BaseModel):
    old_student_code: str
    new_student_code: str
