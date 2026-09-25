import uuid
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
            await cls.collection.insert_one(data.dict())
            return True
        except Exception as e:
            print(e)
            return False

    @classmethod
    async def get_by_test_id(cls, request: GetQuestions):
        """Lấy câu hỏi KHÔNG kèm đáp án đúng (dùng cho frontend)"""
        questions = await cls.collection.find({'test_id': request.test_id}).to_list(None)
        for question in questions:
            question["_id"] = str(question["_id"])
            answers = []
            for answer in question["answers"]:
                answers.append({
                    "text": answer["text"]
                })
            question["answers"] = answers
        return questions

    @classmethod
    async def get_by_test_id_with_answers(cls, request: GetQuestions):
        """Lấy câu hỏi KÈM đáp án đúng (dùng nội bộ để chấm điểm)"""
        questions = await cls.collection.find({'test_id': request.test_id}).to_list(None)
        for question in questions:
            question["_id"] = str(question["_id"])
        return questions

    @classmethod
    async def update_question(cls, question_id: str, data: dict):
        from bson import ObjectId
        try:
            result = await cls.collection.update_one(
                {"_id": ObjectId(question_id)},
                {"$set": data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(e)
            return False

    @classmethod
    async def delete_question(cls, question_id: str):
        from bson import ObjectId
        try:
            result = await cls.collection.delete_one({"_id": ObjectId(question_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(e)
            return False