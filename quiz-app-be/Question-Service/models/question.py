import uuid
from bson import ObjectId
from umongo import Document, fields

from schemas.question import CreateQuestion, GetQuestions
from configs.database import question_instance


@question_instance.register
class Question(Document):
    test_id = fields.StringField(required=True)
    text = fields.StrField(required=True)
    answers = fields.ListField(fields.DictField(), default=[])

    class Meta:
        collection_name = "questions"

    @classmethod
    async def create(cls, data: CreateQuestion):
        try:
            answers_list = []
            for a in data.answers:
                if hasattr(a, "dict"):
                    answers_list.append(a.dict())
                elif hasattr(a, "model_dump"):
                    answers_list.append(a.model_dump())
                else:
                    answers_list.append(dict(a))

            doc = {
                "test_id": str(data.test_id),
                "text": data.text,
                "answers": answers_list
            }
            await cls.collection.insert_one(doc)
            return True
        except Exception as e:
            print(f"Error creating question: {e}")
            return False

    @classmethod
    async def get_by_test_id(cls, request: GetQuestions):
        """Lấy câu hỏi KHÔNG kèm đáp án đúng (dùng cho frontend)"""
        test_id_str = str(request.test_id)
        query = {"test_id": test_id_str}
        if ObjectId.is_valid(test_id_str):
            query = {"$or": [{"test_id": test_id_str}, {"test_id": ObjectId(test_id_str)}]}

        questions = await cls.collection.find(query).to_list(None)
        for question in questions:
            question["_id"] = str(question["_id"])
            if "test_id" in question:
                question["test_id"] = str(question["test_id"])
            answers = []
            for answer in question.get("answers", []):
                answers.append({
                    "text": answer["text"]
                })
            question["answers"] = answers
        return questions

    @classmethod
    async def get_by_test_id_with_answers(cls, request: GetQuestions):
        """Lấy câu hỏi KÈM đáp án đúng (dùng nội bộ để chấm điểm và hiển thị admin)"""
        test_id_str = str(request.test_id)
        query = {"test_id": test_id_str}
        if ObjectId.is_valid(test_id_str):
            query = {"$or": [{"test_id": test_id_str}, {"test_id": ObjectId(test_id_str)}]}

        questions = await cls.collection.find(query).to_list(None)
        for question in questions:
            question["_id"] = str(question["_id"])
            if "test_id" in question:
                question["test_id"] = str(question["test_id"])
        return questions

    @classmethod
    async def update_question(cls, question_id: str, data: dict):
        try:
            if not ObjectId.is_valid(question_id):
                return False
            result = await cls.collection.update_one(
                {"_id": ObjectId(question_id)},
                {"$set": data}
            )
            return result.matched_count > 0 or result.modified_count > 0
        except Exception as e:
            print(f"Error updating question: {e}")
            return False

    @classmethod
    async def delete_question(cls, question_id: str):
        try:
            if not ObjectId.is_valid(question_id):
                return False
            result = await cls.collection.delete_one({"_id": ObjectId(question_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting question: {e}")
            return False