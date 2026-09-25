from umongo import Document, fields
from schemas.student import CreateStudent, GetStudent
from configs.database import student_instance


@student_instance.register
class Student(Document):
    student_code = fields.StringField(required=True, unique=True)
    student_name = fields.StringField(required=True)
    class_name = fields.StringField(default="")
    faculty = fields.StringField(default="")

    class Meta:
        collection_name = "students"

    @classmethod
    async def create_student(cls, data: dict):
        try:
            student_code = data.get("student_code")
            if not student_code or len(student_code) != 10 or not student_code.isdigit():
                return False, "Mã sinh viên phải gồm đúng 10 chữ số"

            student_name = data.get("student_name") or data.get("name") or ""
            class_name = data.get("class_name") or ""
            faculty = data.get("faculty") or ""

            existing = await cls.collection.find_one({"student_code": student_code})
            if existing:
                # Nếu đã tồn tại thì cập nhật thông tin
                update_doc = {}
                if student_name:
                    update_doc["student_name"] = student_name
                if class_name:
                    update_doc["class_name"] = class_name
                if faculty:
                    update_doc["faculty"] = faculty

                if update_doc:
                    await cls.collection.update_one(
                        {"student_code": student_code},
                        {"$set": update_doc}
                    )
                return True, "Cập nhật sinh viên thành công"

            student_doc = {
                "student_code": student_code,
                "student_name": student_name,
                "class_name": class_name,
                "faculty": faculty
            }
            await cls.collection.insert_one(student_doc)
            return True, "Thêm sinh viên thành công"
        except Exception as e:
            print(f"Error creating student: {e}")
            return False, f"Lỗi thêm sinh viên: {str(e)}"

    @classmethod
    async def update_student(cls, target_code: str, data: dict):
        try:
            new_student_code = data.get("student_code")
            if new_student_code and (len(new_student_code) != 10 or not new_student_code.isdigit()):
                return False, "Mã sinh viên phải gồm đúng 10 chữ số"

            student_name = data.get("student_name") or data.get("name")
            class_name = data.get("class_name")
            faculty = data.get("faculty")

            existing = await cls.collection.find_one({"student_code": target_code})
            if not existing:
                return False, "Không tìm thấy sinh viên"

            if new_student_code and new_student_code != target_code:
                duplicate = await cls.collection.find_one({"student_code": new_student_code})
                if duplicate:
                    return False, "Mã sinh viên mới đã tồn tại trên hệ thống"

            update_doc = {}
            if new_student_code:
                update_doc["student_code"] = new_student_code
            if student_name is not None:
                update_doc["student_name"] = student_name
            if class_name is not None:
                update_doc["class_name"] = class_name
            if faculty is not None:
                update_doc["faculty"] = faculty

            if not update_doc:
                return True, "Không có thông tin thay đổi"

            await cls.collection.update_one(
                {"student_code": target_code},
                {"$set": update_doc}
            )
            return True, "Cập nhật sinh viên thành công"
        except Exception as e:
            print(f"Error updating student: {e}")
            return False, f"Lỗi cập nhật sinh viên: {str(e)}"

    @classmethod
    async def delete_student(cls, student_code: str):
        try:
            result = await cls.collection.delete_one({"student_code": student_code})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting student: {e}")
            return False

    @classmethod
    async def get_by_test_student_code(cls, request: GetStudent):
        student = await cls.collection.find_one({'student_code': request.student_code})
        if student:
            student["_id"] = str(student["_id"])
            return student
        else:
            return {}

    @classmethod
    async def get_all_students(cls):
        students = await cls.collection.find().to_list(1000)
        for s in students:
            s["_id"] = str(s["_id"])
        return students
