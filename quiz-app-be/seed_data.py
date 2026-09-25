"""
Seed Data Script - Tao cau hoi trac nghiem cho ung dung Quiz
==============================================================
Chu de:
  1. Kien truc huong dich vu (SOA) - 20 cau
  2. Lap trinh Python co ban - 20 cau
  3. Co so du lieu - 20 cau

Cach su dung:
  python seed_data.py              # Seed tat ca chu de
  python seed_data.py --topic soa  # Chi seed chu de SOA
  python seed_data.py --topic python
  python seed_data.py --topic database
  python seed_data.py --list       # Xem danh sach bai thi hien co
  python seed_data.py --clear      # Xoa tat ca du lieu seed (tests + questions)

Script se ket noi truc tiep MongoDB (khong can cac service dang chay).
"""

import argparse
import sys
import io
from pymongo import MongoClient
from bson import ObjectId

# Fix encoding cho Windows terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ==========================================
# CAU HINH
# ==========================================
MONGODB_URL = "mongodb://localhost:27017"
TEST_DB_NAME = "TestService"
QUESTION_DB_NAME = "QuestionService"
TEST_COLLECTION = "tests"
QUESTION_COLLECTION = "questions"


# ==========================================
# DU LIEU CAU HOI
# ==========================================

SEED_TOPICS = {
    "soa": {
        "test_code": "SOA2024",
        "test_name": "Kien truc huong dich vu (SOA)",
        "time": "45",
        "questions": [
            {
                "text": "SOA la viet tat cua cum tu nao?",
                "answers": [
                    {"text": "Service-Oriented Architecture", "is_correct": True},
                    {"text": "Software-Oriented Application", "is_correct": False},
                    {"text": "System-Oriented Architecture", "is_correct": False},
                    {"text": "Service-Optimized Application", "is_correct": False},
                ]
            },
            {
                "text": "Dac diem nao KHONG phai la nguyen tac cua SOA?",
                "answers": [
                    {"text": "Cac dich vu phai duoc trien khai tren cung mot may chu", "is_correct": True},
                    {"text": "Loose coupling (lien ket long)", "is_correct": False},
                    {"text": "Tai su dung dich vu (Service reusability)", "is_correct": False},
                    {"text": "Kha nang tu tri cua dich vu (Service autonomy)", "is_correct": False},
                ]
            },
            {
                "text": "Trong SOA, 'Loose Coupling' co nghia la gi?",
                "answers": [
                    {"text": "Cac dich vu it phu thuoc vao nhau ve mat trien khai", "is_correct": True},
                    {"text": "Cac dich vu phai chia se cung mot co so du lieu", "is_correct": False},
                    {"text": "Cac dich vu khong the giao tiep voi nhau", "is_correct": False},
                    {"text": "Cac dich vu phai su dung cung ngon ngu lap trinh", "is_correct": False},
                ]
            },
            {
                "text": "Giao thuc nao thuong duoc su dung trong Web Service theo kien truc SOA?",
                "answers": [
                    {"text": "SOAP va REST", "is_correct": True},
                    {"text": "FTP va SSH", "is_correct": False},
                    {"text": "SMTP va POP3", "is_correct": False},
                    {"text": "Telnet va SNMP", "is_correct": False},
                ]
            },
            {
                "text": "WSDL trong SOA dung de lam gi?",
                "answers": [
                    {"text": "Mo ta giao dien va cach goi Web Service", "is_correct": True},
                    {"text": "Luu tru du lieu cua dich vu", "is_correct": False},
                    {"text": "Quan ly phien lam viec cua nguoi dung", "is_correct": False},
                    {"text": "Ma hoa du lieu truyen tai", "is_correct": False},
                ]
            },
            {
                "text": "ESB (Enterprise Service Bus) dong vai tro gi trong SOA?",
                "answers": [
                    {"text": "Trung gian ket noi va dieu phoi cac dich vu", "is_correct": True},
                    {"text": "Co so du lieu trung tam cho tat ca dich vu", "is_correct": False},
                    {"text": "Tuong lua bao ve he thong", "is_correct": False},
                    {"text": "Cong cu phat trien ung dung", "is_correct": False},
                ]
            },
            {
                "text": "Microservices khac SOA truyen thong o diem nao?",
                "answers": [
                    {"text": "Microservices nho gon hon, moi service co database rieng", "is_correct": True},
                    {"text": "Microservices khong su dung giao thuc HTTP", "is_correct": False},
                    {"text": "SOA khong ho tro giao tiep qua mang", "is_correct": False},
                    {"text": "Microservices khong the scale doc lap", "is_correct": False},
                ]
            },
            {
                "text": "REST API su dung phuong thuc HTTP nao de tao moi tai nguyen?",
                "answers": [
                    {"text": "POST", "is_correct": True},
                    {"text": "GET", "is_correct": False},
                    {"text": "DELETE", "is_correct": False},
                    {"text": "PATCH", "is_correct": False},
                ]
            },
            {
                "text": "Trong kien truc SOA, 'Service Contract' la gi?",
                "answers": [
                    {"text": "Ban mo ta chinh thuc ve chuc nang va cach tuong tac voi dich vu", "is_correct": True},
                    {"text": "Hop dong phap ly giua nha cung cap va khach hang", "is_correct": False},
                    {"text": "Ma nguon cua dich vu", "is_correct": False},
                    {"text": "Tai lieu huong dan nguoi dung cuoi", "is_correct": False},
                ]
            },
            {
                "text": "API Gateway trong kien truc microservices co chuc nang gi?",
                "answers": [
                    {"text": "Diem truy cap duy nhat, dinh tuyen request den cac service phu hop", "is_correct": True},
                    {"text": "Luu tru toan bo du lieu cua he thong", "is_correct": False},
                    {"text": "Bien dich ma nguon cua cac service", "is_correct": False},
                    {"text": "Tao giao dien nguoi dung tu dong", "is_correct": False},
                ]
            },
            {
                "text": "Mo hinh giao tiep nao phu hop khi mot service can thong bao su kien den nhieu service khac?",
                "answers": [
                    {"text": "Publish/Subscribe (Pub/Sub)", "is_correct": True},
                    {"text": "Request/Response dong bo", "is_correct": False},
                    {"text": "Polling lien tuc", "is_correct": False},
                    {"text": "FTP transfer", "is_correct": False},
                ]
            },
            {
                "text": "SOAP Message co cau truc co ban gom nhung phan nao?",
                "answers": [
                    {"text": "Envelope, Header, Body", "is_correct": True},
                    {"text": "Request, Response, Status", "is_correct": False},
                    {"text": "Input, Process, Output", "is_correct": False},
                    {"text": "Client, Server, Database", "is_correct": False},
                ]
            },
            {
                "text": "Service Registry (UDDI) trong SOA dung de lam gi?",
                "answers": [
                    {"text": "Dang ky va tim kiem cac dich vu co san", "is_correct": True},
                    {"text": "Luu tru ma nguon cua dich vu", "is_correct": False},
                    {"text": "Kiem tra loi cua dich vu", "is_correct": False},
                    {"text": "Tao ban sao luu dich vu", "is_correct": False},
                ]
            },
            {
                "text": "Trong RESTful API, ma trang thai HTTP 404 co y nghia gi?",
                "answers": [
                    {"text": "Tai nguyen khong tim thay (Not Found)", "is_correct": True},
                    {"text": "Yeu cau thanh cong (OK)", "is_correct": False},
                    {"text": "Loi may chu noi bo (Internal Server Error)", "is_correct": False},
                    {"text": "Khong co quyen truy cap (Forbidden)", "is_correct": False},
                ]
            },
            {
                "text": "Orchestration trong SOA khac Choreography o diem nao?",
                "answers": [
                    {"text": "Orchestration co mot bo dieu phoi trung tam, Choreography thi khong", "is_correct": True},
                    {"text": "Choreography nhanh hon Orchestration", "is_correct": False},
                    {"text": "Orchestration khong ho tro bat dong bo", "is_correct": False},
                    {"text": "Khong co su khac biet nao", "is_correct": False},
                ]
            },
            {
                "text": "JSON Web Token (JWT) thuong duoc su dung trong SOA de lam gi?",
                "answers": [
                    {"text": "Xac thuc va uy quyen giua cac dich vu", "is_correct": True},
                    {"text": "Nen du lieu truyen tai", "is_correct": False},
                    {"text": "Tao giao dien nguoi dung", "is_correct": False},
                    {"text": "Luu tru log cua he thong", "is_correct": False},
                ]
            },
            {
                "text": "Circuit Breaker Pattern dung de giai quyet van de gi?",
                "answers": [
                    {"text": "Ngan chan loi lan truyen khi mot service bi loi (cascading failure)", "is_correct": True},
                    {"text": "Tang toc do truy van co so du lieu", "is_correct": False},
                    {"text": "Ma hoa du lieu end-to-end", "is_correct": False},
                    {"text": "Tu dong scale dich vu", "is_correct": False},
                ]
            },
            {
                "text": "Trong SOA, 'Service Composability' nghia la gi?",
                "answers": [
                    {"text": "Cac dich vu co the duoc ket hop de tao thanh dich vu phuc tap hon", "is_correct": True},
                    {"text": "Cac dich vu phai viet bang mot ngon ngu duy nhat", "is_correct": False},
                    {"text": "Dich vu phai xu ly tat ca logic nghiep vu", "is_correct": False},
                    {"text": "Dich vu khong the tai su dung", "is_correct": False},
                ]
            },
            {
                "text": "Uu diem lon nhat cua kien truc SOA so voi kien truc monolithic la gi?",
                "answers": [
                    {"text": "Kha nang mo rong va bao tri de dang hon", "is_correct": True},
                    {"text": "Hieu suat luon cao hon", "is_correct": False},
                    {"text": "Chi phi trien khai thap hon", "is_correct": False},
                    {"text": "Khong can mang de hoat dong", "is_correct": False},
                ]
            },
            {
                "text": "Saga Pattern trong microservices dung de quan ly gi?",
                "answers": [
                    {"text": "Giao dich phan tan (distributed transaction) giua nhieu service", "is_correct": True},
                    {"text": "Giao dien nguoi dung", "is_correct": False},
                    {"text": "Cau hinh trien khai", "is_correct": False},
                    {"text": "Log he thong", "is_correct": False},
                ]
            },
        ]
    },

    "python": {
        "test_code": "PYTHON2024",
        "test_name": "Lap trinh Python co ban",
        "time": "30",
        "questions": [
            {
                "text": "Kieu du lieu nao trong Python dung de luu tru danh sach co thu tu va co the thay doi?",
                "answers": [
                    {"text": "list", "is_correct": True},
                    {"text": "tuple", "is_correct": False},
                    {"text": "set", "is_correct": False},
                    {"text": "frozenset", "is_correct": False},
                ]
            },
            {
                "text": "Ket qua cua bieu thuc: 10 // 3 la gi?",
                "answers": [
                    {"text": "3", "is_correct": True},
                    {"text": "3.33", "is_correct": False},
                    {"text": "4", "is_correct": False},
                    {"text": "1", "is_correct": False},
                ]
            },
            {
                "text": "Tu khoa nao dung de dinh nghia ham trong Python?",
                "answers": [
                    {"text": "def", "is_correct": True},
                    {"text": "function", "is_correct": False},
                    {"text": "func", "is_correct": False},
                    {"text": "define", "is_correct": False},
                ]
            },
            {
                "text": "Phuong thuc nao dung de them phan tu vao cuoi list?",
                "answers": [
                    {"text": "append()", "is_correct": True},
                    {"text": "add()", "is_correct": False},
                    {"text": "insert()", "is_correct": False},
                    {"text": "push()", "is_correct": False},
                ]
            },
            {
                "text": "Ket qua cua doan code: print(type(3.14)) la gi?",
                "answers": [
                    {"text": "<class 'float'>", "is_correct": True},
                    {"text": "<class 'int'>", "is_correct": False},
                    {"text": "<class 'double'>", "is_correct": False},
                    {"text": "<class 'decimal'>", "is_correct": False},
                ]
            },
            {
                "text": "Cach nao dung de tao dictionary trong Python?",
                "answers": [
                    {"text": "d = {'key': 'value'}", "is_correct": True},
                    {"text": "d = ['key': 'value']", "is_correct": False},
                    {"text": "d = ('key': 'value')", "is_correct": False},
                    {"text": "d = <'key': 'value'>", "is_correct": False},
                ]
            },
            {
                "text": "Vong lap nao dung khi biet truoc so lan lap?",
                "answers": [
                    {"text": "for", "is_correct": True},
                    {"text": "while", "is_correct": False},
                    {"text": "do-while", "is_correct": False},
                    {"text": "repeat", "is_correct": False},
                ]
            },
            {
                "text": "Ket qua cua: 'Hello'[1:4] la gi?",
                "answers": [
                    {"text": "'ell'", "is_correct": True},
                    {"text": "'Hel'", "is_correct": False},
                    {"text": "'ello'", "is_correct": False},
                    {"text": "'Hell'", "is_correct": False},
                ]
            },
            {
                "text": "Tu khoa nao dung de xu ly ngoai le (exception) trong Python?",
                "answers": [
                    {"text": "try-except", "is_correct": True},
                    {"text": "try-catch", "is_correct": False},
                    {"text": "catch-throw", "is_correct": False},
                    {"text": "handle-error", "is_correct": False},
                ]
            },
            {
                "text": "Cach nao dung de mo file trong Python?",
                "answers": [
                    {"text": "open('file.txt', 'r')", "is_correct": True},
                    {"text": "file.open('file.txt')", "is_correct": False},
                    {"text": "read('file.txt')", "is_correct": False},
                    {"text": "File.read('file.txt')", "is_correct": False},
                ]
            },
            {
                "text": "List comprehension nao tao danh sach cac so chan tu 0 den 9?",
                "answers": [
                    {"text": "[x for x in range(10) if x % 2 == 0]", "is_correct": True},
                    {"text": "[x for x in range(10) if x % 2 != 0]", "is_correct": False},
                    {"text": "[x for x in range(10) if x / 2 == 0]", "is_correct": False},
                    {"text": "[x % 2 for x in range(10)]", "is_correct": False},
                ]
            },
            {
                "text": "Decorator trong Python duoc ky hieu bang?",
                "answers": [
                    {"text": "@", "is_correct": True},
                    {"text": "#", "is_correct": False},
                    {"text": "$", "is_correct": False},
                    {"text": "&", "is_correct": False},
                ]
            },
            {
                "text": "Phuong thuc __init__ trong class Python dung de lam gi?",
                "answers": [
                    {"text": "Khoi tao doi tuong (constructor)", "is_correct": True},
                    {"text": "Huy doi tuong (destructor)", "is_correct": False},
                    {"text": "Chuyen doi kieu du lieu", "is_correct": False},
                    {"text": "In ra thong tin doi tuong", "is_correct": False},
                ]
            },
            {
                "text": "Ham lambda trong Python la gi?",
                "answers": [
                    {"text": "Ham an danh (anonymous function) viet tren mot dong", "is_correct": True},
                    {"text": "Ham chi chay mot lan duy nhat", "is_correct": False},
                    {"text": "Ham khong co tham so", "is_correct": False},
                    {"text": "Ham tu dong chay khi import module", "is_correct": False},
                ]
            },
            {
                "text": "Module nao cung cap ham de lam viec voi JSON trong Python?",
                "answers": [
                    {"text": "json", "is_correct": True},
                    {"text": "csv", "is_correct": False},
                    {"text": "pickle", "is_correct": False},
                    {"text": "xml", "is_correct": False},
                ]
            },
            {
                "text": "Ket qua cua: len([1, [2, 3], 4]) la bao nhieu?",
                "answers": [
                    {"text": "3", "is_correct": True},
                    {"text": "4", "is_correct": False},
                    {"text": "5", "is_correct": False},
                    {"text": "2", "is_correct": False},
                ]
            },
            {
                "text": "Toan tu nao kiem tra xem phan tu co trong list khong?",
                "answers": [
                    {"text": "in", "is_correct": True},
                    {"text": "has", "is_correct": False},
                    {"text": "contains", "is_correct": False},
                    {"text": "exists", "is_correct": False},
                ]
            },
            {
                "text": "Cach nao de cai dat thu vien ben ngoai trong Python?",
                "answers": [
                    {"text": "pip install <ten_thu_vien>", "is_correct": True},
                    {"text": "python install <ten_thu_vien>", "is_correct": False},
                    {"text": "import install <ten_thu_vien>", "is_correct": False},
                    {"text": "apt-get <ten_thu_vien>", "is_correct": False},
                ]
            },
            {
                "text": "Su khac biet giua '==' va 'is' trong Python la gi?",
                "answers": [
                    {"text": "'==' so sanh gia tri, 'is' so sanh identity (vung nho)", "is_correct": True},
                    {"text": "Khong co su khac biet", "is_correct": False},
                    {"text": "'==' chi dung cho so, 'is' dung cho chuoi", "is_correct": False},
                    {"text": "'is' so sanh gia tri, '==' so sanh kieu du lieu", "is_correct": False},
                ]
            },
            {
                "text": "Virtual environment (venv) trong Python dung de lam gi?",
                "answers": [
                    {"text": "Tao moi truong Python co lap cho tung du an", "is_correct": True},
                    {"text": "Chay Python tren may ao", "is_correct": False},
                    {"text": "Tang toc do thuc thi code", "is_correct": False},
                    {"text": "Bao mat ma nguon", "is_correct": False},
                ]
            },
        ]
    },

    "database": {
        "test_code": "CSDL2024",
        "test_name": "Co so du lieu",
        "time": "45",
        "questions": [
            {
                "text": "SQL la viet tat cua cum tu nao?",
                "answers": [
                    {"text": "Structured Query Language", "is_correct": True},
                    {"text": "Simple Query Language", "is_correct": False},
                    {"text": "Standard Query Logic", "is_correct": False},
                    {"text": "System Query Language", "is_correct": False},
                ]
            },
            {
                "text": "Lenh SQL nao dung de truy van du lieu tu bang?",
                "answers": [
                    {"text": "SELECT", "is_correct": True},
                    {"text": "GET", "is_correct": False},
                    {"text": "FETCH", "is_correct": False},
                    {"text": "RETRIEVE", "is_correct": False},
                ]
            },
            {
                "text": "Primary Key co dac diem nao?",
                "answers": [
                    {"text": "Gia tri duy nhat va khong duoc NULL", "is_correct": True},
                    {"text": "Co the trung lap gia tri", "is_correct": False},
                    {"text": "Co the chua NULL", "is_correct": False},
                    {"text": "Moi bang co the co nhieu Primary Key", "is_correct": False},
                ]
            },
            {
                "text": "Chuan hoa (Normalization) trong CSDL nham muc dich gi?",
                "answers": [
                    {"text": "Giam du thua du lieu va tranh bat thuong (anomaly)", "is_correct": True},
                    {"text": "Tang toc do truy van", "is_correct": False},
                    {"text": "Ma hoa du lieu", "is_correct": False},
                    {"text": "Nen du lieu de tiet kiem dung luong", "is_correct": False},
                ]
            },
            {
                "text": "JOIN nao tra ve tat ca ban ghi tu bang ben trai, ke ca khong khop?",
                "answers": [
                    {"text": "LEFT JOIN", "is_correct": True},
                    {"text": "INNER JOIN", "is_correct": False},
                    {"text": "RIGHT JOIN", "is_correct": False},
                    {"text": "CROSS JOIN", "is_correct": False},
                ]
            },
            {
                "text": "Thuoc tinh ACID trong transaction bao gom nhung gi?",
                "answers": [
                    {"text": "Atomicity, Consistency, Isolation, Durability", "is_correct": True},
                    {"text": "Access, Control, Integrity, Data", "is_correct": False},
                    {"text": "Authentication, Consistency, Index, Database", "is_correct": False},
                    {"text": "Atomicity, Cache, Isolation, Distribution", "is_correct": False},
                ]
            },
            {
                "text": "INDEX trong co so du lieu dung de lam gi?",
                "answers": [
                    {"text": "Tang toc do truy van du lieu", "is_correct": True},
                    {"text": "Bao mat du lieu", "is_correct": False},
                    {"text": "Nen du lieu", "is_correct": False},
                    {"text": "Sao luu du lieu tu dong", "is_correct": False},
                ]
            },
            {
                "text": "Foreign Key dung de lam gi?",
                "answers": [
                    {"text": "Tao moi quan he giua hai bang", "is_correct": True},
                    {"text": "Khoa bang khong cho ai truy cap", "is_correct": False},
                    {"text": "Ma hoa cot du lieu", "is_correct": False},
                    {"text": "Tu dong tao gia tri duy nhat", "is_correct": False},
                ]
            },
            {
                "text": "Lenh SQL nao dung de xoa toan bo du lieu trong bang ma KHONG xoa cau truc bang?",
                "answers": [
                    {"text": "TRUNCATE TABLE", "is_correct": True},
                    {"text": "DROP TABLE", "is_correct": False},
                    {"text": "REMOVE TABLE", "is_correct": False},
                    {"text": "DESTROY TABLE", "is_correct": False},
                ]
            },
            {
                "text": "NoSQL database khac SQL database o diem nao?",
                "answers": [
                    {"text": "NoSQL khong yeu cau schema co dinh va linh hoat hon", "is_correct": True},
                    {"text": "NoSQL luon nhanh hon SQL", "is_correct": False},
                    {"text": "NoSQL khong ho tro truy van", "is_correct": False},
                    {"text": "SQL khong the xu ly du lieu lon", "is_correct": False},
                ]
            },
            {
                "text": "MongoDB luu tru du lieu duoi dang gi?",
                "answers": [
                    {"text": "Document (BSON/JSON)", "is_correct": True},
                    {"text": "Bang (Table)", "is_correct": False},
                    {"text": "Graph", "is_correct": False},
                    {"text": "Key-Value don gian", "is_correct": False},
                ]
            },
            {
                "text": "Lenh GROUP BY trong SQL dung de lam gi?",
                "answers": [
                    {"text": "Nhom cac ban ghi theo gia tri cua cot de thuc hien ham tong hop", "is_correct": True},
                    {"text": "Sap xep du lieu theo thu tu tang dan", "is_correct": False},
                    {"text": "Loc du lieu theo dieu kien", "is_correct": False},
                    {"text": "Ket hop hai bang", "is_correct": False},
                ]
            },
            {
                "text": "VIEW trong SQL la gi?",
                "answers": [
                    {"text": "Bang ao duoc tao tu cau truy van SELECT", "is_correct": True},
                    {"text": "Giao dien nguoi dung", "is_correct": False},
                    {"text": "Ban sao luu cua bang", "is_correct": False},
                    {"text": "Index dac biet", "is_correct": False},
                ]
            },
            {
                "text": "Stored Procedure trong CSDL la gi?",
                "answers": [
                    {"text": "Tap hop cac cau lenh SQL duoc luu tru va co the goi lai nhieu lan", "is_correct": True},
                    {"text": "Quy trinh sao luu du lieu", "is_correct": False},
                    {"text": "Phuong thuc ma hoa du lieu", "is_correct": False},
                    {"text": "Cach luu tru file tren o dia", "is_correct": False},
                ]
            },
            {
                "text": "Dang chuan 3NF (Third Normal Form) yeu cau gi?",
                "answers": [
                    {"text": "Khong co phu thuoc bac cau (transitive dependency)", "is_correct": True},
                    {"text": "Tat ca cac cot phai la so", "is_correct": False},
                    {"text": "Moi bang chi co 3 cot", "is_correct": False},
                    {"text": "Bang phai co dung 3 ban ghi", "is_correct": False},
                ]
            },
            {
                "text": "Trigger trong CSDL la gi?",
                "answers": [
                    {"text": "Doan code tu dong thuc thi khi co su kien INSERT/UPDATE/DELETE", "is_correct": True},
                    {"text": "Nut bam tren giao dien", "is_correct": False},
                    {"text": "Lenh khoi dong database", "is_correct": False},
                    {"text": "Cong cu sao luu du lieu", "is_correct": False},
                ]
            },
            {
                "text": "Subquery (truy van con) trong SQL la gi?",
                "answers": [
                    {"text": "Cau truy van SELECT nam ben trong mot cau truy van khac", "is_correct": True},
                    {"text": "Cau truy van ngan duoi 10 ky tu", "is_correct": False},
                    {"text": "Cau truy van chi tra ve 1 ban ghi", "is_correct": False},
                    {"text": "Cau truy van khong co dieu kien WHERE", "is_correct": False},
                ]
            },
            {
                "text": "CAP Theorem noi rang he thong phan tan chi co the dam bao toi da may trong 3 thuoc tinh?",
                "answers": [
                    {"text": "2", "is_correct": True},
                    {"text": "1", "is_correct": False},
                    {"text": "3", "is_correct": False},
                    {"text": "0", "is_correct": False},
                ]
            },
            {
                "text": "Redis thuoc loai co so du lieu nao?",
                "answers": [
                    {"text": "Key-Value Store (In-Memory)", "is_correct": True},
                    {"text": "Relational Database", "is_correct": False},
                    {"text": "Graph Database", "is_correct": False},
                    {"text": "Column-Family Store", "is_correct": False},
                ]
            },
            {
                "text": "Lenh HAVING trong SQL khac WHERE o diem nao?",
                "answers": [
                    {"text": "HAVING loc sau GROUP BY, WHERE loc truoc GROUP BY", "is_correct": True},
                    {"text": "Khong co su khac biet", "is_correct": False},
                    {"text": "WHERE dung cho so, HAVING dung cho chuoi", "is_correct": False},
                    {"text": "HAVING nhanh hon WHERE", "is_correct": False},
                ]
            },
        ]
    },
}


def print_header():
    print("\n" + "=" * 60)
    print("  SEED DATA - UNG DUNG THI TRAC NGHIEM")
    print("=" * 60)


def get_mongo_client():
    """Ket noi MongoDB"""
    try:
        client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        return client
    except Exception as e:
        print(f"  [LOI] Khong the ket noi MongoDB tai {MONGODB_URL}")
        print(f"  Chi tiet: {e}")
        print(f"  -> Dam bao MongoDB dang chay!")
        sys.exit(1)


def list_existing_tests(client):
    """Lay danh sach bai thi hien co"""
    db = client[TEST_DB_NAME]
    tests = list(db[TEST_COLLECTION].find())
    for t in tests:
        t["_id"] = str(t["_id"])
    return tests


def create_test(client, test_code, test_name, time_minutes):
    """Tao bai thi moi trong TestService DB"""
    db = client[TEST_DB_NAME]

    # Kiem tra trung test_code
    existing = db[TEST_COLLECTION].find_one({"test_code": test_code})
    if existing:
        return str(existing["_id"]), False  # Da ton tai

    result = db[TEST_COLLECTION].insert_one({
        "test_code": test_code,
        "name": test_name,
        "time": time_minutes,
        "list_students": []
    })
    return str(result.inserted_id), True  # Moi tao


def create_questions(client, test_id, questions):
    """Tao nhieu cau hoi cho mot bai thi"""
    db = client[QUESTION_DB_NAME]

    docs = []
    for q in questions:
        docs.append({
            "test_id": test_id,
            "text": q["text"],
            "answers": q["answers"]
        })

    result = db[QUESTION_COLLECTION].insert_many(docs)
    return len(result.inserted_ids)


def count_questions_for_test(client, test_id):
    """Dem so cau hoi hien co cho mot bai thi"""
    db = client[QUESTION_DB_NAME]
    return db[QUESTION_COLLECTION].count_documents({"test_id": test_id})


def seed_topic(client, topic_key):
    """Seed cau hoi cho mot chu de"""
    topic = SEED_TOPICS.get(topic_key)
    if not topic:
        print(f"  [LOI] Khong tim thay chu de: {topic_key}")
        return False

    test_code = topic["test_code"]
    test_name = topic["test_name"]
    time_val = topic["time"]
    questions = topic["questions"]

    print(f"\n  [CHU DE] {test_name}")
    print(f"  Ma de: {test_code}")
    print(f"  Thoi gian: {time_val} phut")
    print(f"  So cau hoi: {len(questions)}")
    print("-" * 40)

    # Tao hoac lay test
    test_id, is_new = create_test(client, test_code, test_name, time_val)

    if is_new:
        print(f"  [OK] Tao bai thi moi thanh cong (ID: {test_id})")
    else:
        print(f"  [OK] Bai thi da ton tai (ID: {test_id})")

    # Kiem tra so cau hoi hien co
    existing_count = count_questions_for_test(client, test_id)
    if existing_count > 0:
        print(f"  [INFO] Bai thi da co {existing_count} cau hoi")
        print(f"  [INFO] Them {len(questions)} cau hoi moi...")

    # Tao cau hoi
    inserted = create_questions(client, test_id, questions)
    print(f"  [OK] Da them {inserted}/{len(questions)} cau hoi")

    total = count_questions_for_test(client, test_id)
    print(f"  [TONG] Bai thi hien co {total} cau hoi")

    return True


def clear_seed_data(client):
    """Xoa tat ca du lieu seed"""
    print("\n  [CANH BAO] Xoa tat ca du lieu seed...")

    test_db = client[TEST_DB_NAME]
    question_db = client[QUESTION_DB_NAME]

    # Xoa cau hoi cua cac test_code trong seed
    for topic in SEED_TOPICS.values():
        test_code = topic["test_code"]
        test = test_db[TEST_COLLECTION].find_one({"test_code": test_code})
        if test:
            test_id = str(test["_id"])
            q_deleted = question_db[QUESTION_COLLECTION].delete_many({"test_id": test_id})
            t_deleted = test_db[TEST_COLLECTION].delete_one({"_id": test["_id"]})
            print(f"  [OK] {test_code}: Xoa {q_deleted.deleted_count} cau hoi, {t_deleted.deleted_count} bai thi")
        else:
            print(f"  [--] {test_code}: Khong tim thay")

    print("  [OK] Xoa hoan tat!")


def main():
    parser = argparse.ArgumentParser(description="Seed data cho ung dung Quiz")
    parser.add_argument(
        "--topic",
        choices=["soa", "python", "database", "all"],
        default="all",
        help="Chu de can seed (mac dinh: all)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Liet ke danh sach bai thi hien co"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Xoa tat ca du lieu seed"
    )

    args = parser.parse_args()

    print_header()

    # Ket noi MongoDB
    print("\n  [INFO] Ket noi MongoDB...")
    client = get_mongo_client()
    print(f"  [OK] Da ket noi: {MONGODB_URL}")

    if args.clear:
        clear_seed_data(client)
        client.close()
        return

    if args.list:
        tests = list_existing_tests(client)
        print(f"\n  Danh sach bai thi hien co ({len(tests)} bai):")
        if tests:
            for t in tests:
                q_count = count_questions_for_test(client, t["_id"])
                print(f"    - [{t.get('test_code', 'N/A')}] {t.get('name', 'N/A')} | {q_count} cau hoi | ID: {t['_id']}")
        else:
            print("    (Chua co bai thi nao)")
        client.close()
        return

    # Seed data
    topics_to_seed = list(SEED_TOPICS.keys()) if args.topic == "all" else [args.topic]

    total_questions = sum(len(SEED_TOPICS[t]["questions"]) for t in topics_to_seed)
    print(f"\n  [BAT DAU] Seed {len(topics_to_seed)} chu de, tong {total_questions} cau hoi...")

    for topic_key in topics_to_seed:
        seed_topic(client, topic_key)

    print("\n" + "=" * 60)
    print("  SEED DATA HOAN TAT!")
    print("=" * 60)

    # Hien thi tong ket
    tests = list_existing_tests(client)
    print(f"\n  Tong ket:")
    for t in tests:
        q_count = count_questions_for_test(client, t["_id"])
        print(f"    - [{t.get('test_code', 'N/A')}] {t.get('name', 'N/A')}: {q_count} cau hoi")

    print(f"\n  Su dung cac lenh:")
    print(f"    python seed_data.py --list     # Xem danh sach bai thi")
    print(f"    python seed_data.py --clear    # Xoa du lieu seed")
    print()

    client.close()


if __name__ == "__main__":
    main()
