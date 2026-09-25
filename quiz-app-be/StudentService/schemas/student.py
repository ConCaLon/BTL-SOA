from pydantic import BaseModel, validator
from typing import Optional
import re


class CreateStudent(BaseModel):
    student_code: str
    student_name: Optional[str] = None
    name: Optional[str] = None
    class_name: Optional[str] = ""
    faculty: Optional[str] = ""

    @validator("student_code")
    def validate_student_code(cls, v):
        if not re.match(r"^\d{10}$", v):
            raise ValueError("Mã sinh viên phải gồm đúng 10 chữ số")
        return v


class UpdateStudent(BaseModel):
    student_code: str
    old_student_code: Optional[str] = None
    student_name: Optional[str] = None
    name: Optional[str] = None
    class_name: Optional[str] = ""
    faculty: Optional[str] = ""

    @validator("student_code")
    def validate_student_code(cls, v):
        if not re.match(r"^\d{10}$", v):
            raise ValueError("Mã sinh viên phải gồm đúng 10 chữ số")
        return v


class DeleteStudent(BaseModel):
    student_code: str


class GetStudent(BaseModel):
    student_code: str
