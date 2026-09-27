import asyncio
from datetime import datetime, timezone
import re
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from constants.all import MONGODB_URL


def get_dbs():
    """Lấy async database instances đảm bảo tương thích mọi event loop"""
    client = AsyncIOMotorClient(MONGODB_URL or "mongodb://localhost:27017")
    return client["TestService"], client["QuestionService"]


class Test:
    @classmethod
    def get_collections(cls):
        test_db, question_db = get_dbs()
        return test_db["tests"], test_db["submissions"], question_db["questions"]

    @classmethod
    async def get_all_tests(cls):
        """Lấy tất cả bài thi kèm số lượng câu hỏi hiện có"""
        tests_col, _, questions_col = cls.get_collections()
        tests = await tests_col.find().to_list(1000)
        result = []
        for t in tests:
            t_id = str(t["_id"])
            q_count = await questions_col.count_documents({
                "$or": [{"test_id": t_id}, {"test_id": t["_id"]}]
            })
            list_students = t.get("list_students") or t.get("list_student") or []
            result.append({
                "_id": t_id,
                "test_code": t.get("test_code", ""),
                "name": t.get("name", ""),
                "time": int(t.get("time", 45)) if str(t.get("time", 45)).isdigit() else 45,
                "list_students": list_students,
                "question_count": q_count
            })
        return result

    @classmethod
    async def get_by_code(cls, test_code: str):
        """Tìm bài thi theo mã đề (hỗ trợ case-insensitive)"""
        tests_col, _, _ = cls.get_collections()
        code = test_code.strip()
        test = await tests_col.find_one({"test_code": code})
        if not test:
            test = await tests_col.find_one({
                "test_code": {"$regex": f"^{re.escape(code)}$", "$options": "i"}
            })
        if not test:
            return None
        
        test["_id"] = str(test["_id"])
        test["list_students"] = test.get("list_students") or test.get("list_student") or []
        test["time"] = int(test.get("time", 45)) if str(test.get("time", 45)).isdigit() else 45
        return test

    @classmethod
    async def get_by_id(cls, test_id: str):
        """Lấy bài thi theo id"""
        tests_col, _, _ = cls.get_collections()
        if not ObjectId.is_valid(test_id):
            return None
        test = await tests_col.find_one({"_id": ObjectId(test_id)})
        if not test:
            return None
        test["_id"] = str(test["_id"])
        test["list_students"] = test.get("list_students") or test.get("list_student") or []
        test["time"] = int(test.get("time", 45)) if str(test.get("time", 45)).isdigit() else 45
        return test

    @classmethod
    async def create_test(cls, data: dict):
        """Tạo bài thi mới, kiểm tra trùng test_code"""
        tests_col, _, _ = cls.get_collections()
        test_code = (data.get("test_code") or "").strip()
        if not test_code:
            return False, "Mã đề không được để trống!", None

        existing = await tests_col.find_one({
            "test_code": {"$regex": f"^{re.escape(test_code)}$", "$options": "i"}
        })
        if existing:
            return False, f"Mã đề '{test_code}' đã tồn tại trên hệ thống!", None

        time_val = data.get("time", 45)
        try:
            time_int = int(time_val)
        except (ValueError, TypeError):
            time_int = 45

        doc = {
            "test_code": test_code,
            "name": (data.get("name") or "").strip(),
            "time": time_int,
            "list_students": data.get("list_students") or []
        }
        res = await tests_col.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        return True, "Tạo mã đề thành công!", doc

    @classmethod
    async def update_test(cls, test_id: str, data: dict):
        """Cập nhật bài thi theo test_id"""
        tests_col, _, _ = cls.get_collections()
        if not ObjectId.is_valid(test_id):
            return False, "ID bài thi không hợp lệ!"

        test_code = (data.get("test_code") or "").strip()
        if not test_code:
            return False, "Mã đề không được để trống!"

        existing = await tests_col.find_one({
            "test_code": {"$regex": f"^{re.escape(test_code)}$", "$options": "i"},
            "_id": {"$ne": ObjectId(test_id)}
        })
        if existing:
            return False, f"Mã đề '{test_code}' đã được sử dụng bởi bài thi khác!"

        time_val = data.get("time", 45)
        try:
            time_int = int(time_val)
        except (ValueError, TypeError):
            time_int = 45

        update_fields = {
            "test_code": test_code,
            "name": (data.get("name") or "").strip(),
            "time": time_int,
            "list_students": data.get("list_students") or []
        }

        result = await tests_col.update_one(
            {"_id": ObjectId(test_id)},
            {"$set": update_fields}
        )
        if result.matched_count > 0:
            return True, "Cập nhật bài thi thành công!"
        return False, "Không tìm thấy bài thi để cập nhật!"

    @classmethod
    async def delete_test(cls, test_id: str):
        """Xóa bài thi và xóa toàn bộ câu hỏi thuộc bài thi đó"""
        tests_col, _, questions_col = cls.get_collections()
        if not ObjectId.is_valid(test_id):
            return False, "ID bài thi không hợp lệ!"

        res = await tests_col.delete_one({"_id": ObjectId(test_id)})
        # Xóa câu hỏi liên quan để tránh mồ côi
        await questions_col.delete_many({
            "$or": [{"test_id": test_id}, {"test_id": ObjectId(test_id)}]
        })
        if res.deleted_count > 0:
            return True, "Xóa bài thi thành công!"
        return False, "Không tìm thấy bài thi để xóa!"

    @classmethod
    async def submit_exam(cls, student_code: str, test_id: str, submitted_answers: list):
        """Chấm điểm bài làm và lưu vào collection submissions"""
        tests_col, submissions_col, questions_col = cls.get_collections()
        query = {"test_id": test_id}
        if ObjectId.is_valid(test_id):
            query = {"$or": [{"test_id": test_id}, {"test_id": ObjectId(test_id)}]}
        
        all_questions = await questions_col.find(query).to_list(1000)
        total_questions = len(all_questions)

        correct_map = {}
        for q in all_questions:
            q_id = str(q["_id"])
            correct_ans = next((a["text"] for a in q.get("answers", []) if a.get("is_correct")), None)
            correct_map[q_id] = correct_ans

        user_ans_map = {}
        for a in submitted_answers:
            q_id = str(a.get("question_id", ""))
            user_ans_map[q_id] = a.get("selected_answer", "")

        detailed_answers = []
        correct_count = 0

        for q in all_questions:
            q_id = str(q["_id"])
            selected = user_ans_map.get(q_id, "")
            correct = correct_map.get(q_id)
            is_correct = (selected == correct) and (correct is not None)
            if is_correct:
                correct_count += 1
            detailed_answers.append({
                "question_id": q_id,
                "question_text": q.get("text", ""),
                "selected_answer": selected,
                "correct_answer": correct,
                "is_correct": is_correct
            })

        score = round((correct_count / total_questions) * 10, 2) if total_questions > 0 else 0

        submission_doc = {
            "student_code": student_code,
            "test_id": test_id,
            "score": score,
            "correct_count": correct_count,
            "total_questions": total_questions,
            "answers": detailed_answers,
            "submitted_at": datetime.now(timezone.utc)
        }
        await submissions_col.insert_one(submission_doc)

        return {
            "score": score,
            "correct_count": correct_count,
            "total_questions": total_questions,
            "student_code": student_code,
            "test_id": test_id,
            "answers": detailed_answers
        }

    @classmethod
    async def get_all_submissions(cls):
        """Lấy tất cả lượt nộp bài cho admin dashboard"""
        _, submissions_col, _ = cls.get_collections()
        subs = await submissions_col.find().sort("submitted_at", -1).to_list(500)
        for s in subs:
            s["_id"] = str(s["_id"])
            if "submitted_at" in s and isinstance(s["submitted_at"], datetime):
                s["submitted_at"] = s["submitted_at"].isoformat()
        return subs

    @classmethod
    async def get_student_history(cls, student_code: str):
        """Lấy lịch sử thi của sinh viên"""
        _, submissions_col, _ = cls.get_collections()
        subs = await submissions_col.find({"student_code": student_code}).sort("submitted_at", -1).to_list(100)
        for s in subs:
            s["_id"] = str(s["_id"])
            if "submitted_at" in s and isinstance(s["submitted_at"], datetime):
                s["submitted_at"] = s["submitted_at"].isoformat()
        return subs

    @classmethod
    async def cascade_update_student_code(cls, old_code: str, new_code: str):
        """Đồng bộ khi sinh viên đổi mã số SV"""
        tests_col, submissions_col, _ = cls.get_collections()
        await tests_col.update_many(
            {"list_students": old_code},
            {"$set": {"list_students.$": new_code}}
        )
        await submissions_col.update_many(
            {"student_code": old_code},
            {"$set": {"student_code": new_code}}
        )
        return True
