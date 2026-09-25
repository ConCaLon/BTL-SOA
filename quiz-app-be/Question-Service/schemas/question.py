from pydantic import BaseModel


class Answer(BaseModel):
    text: str
    is_correct: bool


class CreateQuestion(BaseModel):
    test_id: str
    text: str
    answers: list[Answer]


class GetQuestions(BaseModel):
    test_id: str


class UpdateQuestion(BaseModel):
    question_id: str
    text: str
    answers: list[Answer]


class DeleteQuestion(BaseModel):
    question_id: str
