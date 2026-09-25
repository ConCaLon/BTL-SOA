from pydantic import BaseModel, EmailStr, field_validator
import re


class StudentInfo(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    class_name: str

    @field_validator("email")
    @classmethod
    def must_be_hunre_email(cls, v: str) -> str:
        v = v.lower().strip()
        if not v.endswith("@hunre.edu.vn"):
            raise ValueError("Email phải có đuôi @hunre.edu.vn")
        # Mã sinh viên phải đúng 10 chữ số
        student_code = v.split("@")[0]
        if not re.match(r"^\d{10}$", student_code):
            raise ValueError("Mã sinh viên phải gồm đúng 10 chữ số, ví dụ: 2311060738@hunre.edu.vn")
        return v

    @field_validator("password")
    @classmethod
    def password_must_be_10_digits(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^\d{10}$", v):
            raise ValueError("Mật khẩu phải là mã sinh viên gồm đúng 10 chữ số")
        return v

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Họ và tên không được để trống")
        return v.strip()

    @field_validator("class_name")
    @classmethod
    def class_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Lớp không được để trống")
        return v.strip()