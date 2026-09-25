from pydantic import BaseModel
from typing import Optional


class StartTest(BaseModel):
    test_code: str
    email: str
    password: str
    full_name: str
    class_name: str


class AnswerSubmission(BaseModel):
    question_id: str
    selected_answer: str


class SubmitTest(BaseModel):
    test_id: str
    student_code: str
    answers: list[AnswerSubmission]