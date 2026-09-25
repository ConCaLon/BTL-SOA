<script setup>
import { ref, computed } from "vue"
import axios from "axios";
import ExamsHeader from '@/components/ExamsHeader.vue';
import Question from "../components/Question.vue";
import Result from "../components/Result.vue";

const questions = ref([])
const student = ref({})
const test = ref({})
const time = ref(0)
const show = ref(false)
const alert = ref(false)
const showResult = ref(false)
const examResult = ref(null)
const submitted = ref(false)

const email = ref("")
const password = ref("")
const fullName = ref("")
const className = ref("")
const testCode = ref("")

const wait = ref(false)
const status_text = ref("Đang xử lý...")
const messageAlert = ref("")

// Lưu đáp án sinh viên chọn
const studentAnswers = ref([])

// Modal Lịch sử thi của sinh viên
const showHistoryModal = ref(false)
const historyLoading = ref(false)
const studentHistoryList = ref([])

// Cổng API Gateway 8000
const API_BASE = "http://localhost:8000"

const answeredCount = computed(() => studentAnswers.value.length)

function onAnswersUpdate(answers) {
    studentAnswers.value = answers
}

async function handleSubmit() {
    if (submitted.value) return
    submitted.value = true

    try {
        const studentCode = email.value.toLowerCase().split("@")[0]
        status_text.value = "Đang nộp bài..."
        wait.value = true
        show.value = false

        const response = await axios.post(`${API_BASE}/task_service/submit_test`, {
            "test_id": test.value._id,
            "student_code": studentCode,
            "answers": studentAnswers.value
        });

        if (response.status === 200 && response.data.status === "success") {
            examResult.value = response.data.data
            showResult.value = true
            wait.value = false
        } else {
            alert.value = true
            messageAlert.value = response.data.message || "Có lỗi khi nộp bài!"
            wait.value = false
            submitted.value = false
        }
    } catch (error) {
        console.error('Lỗi nộp bài:', error)
        alert.value = true
        messageAlert.value = "Có lỗi kết nối khi nộp bài!"
        wait.value = false
        submitted.value = false
    }
}

function onTimeUp() {
    if (!submitted.value) {
        handleSubmit()
    }
}

const handleClick = async () => {
    if (!testCode.value || !email.value || !password.value || !fullName.value || !className.value) {
        alert.value = true;
        messageAlert.value = "Vui lòng nhập đầy đủ thông tin!";
        return;
    }

    if (!email.value.toLowerCase().endsWith("@hunre.edu.vn")) {
        alert.value = true;
        messageAlert.value = "Email phải có đuôi @hunre.edu.vn (ví dụ: 2311060738@hunre.edu.vn)";
        return;
    }

    const studentCode = email.value.toLowerCase().split("@")[0];
    if (!/^\d{10}$/.test(studentCode)) {
        alert.value = true;
        messageAlert.value = "Mã sinh viên (phần trước @hunre.edu.vn) phải gồm đúng 10 chữ số!";
        return;
    }

    try {
        wait.value = true;
        alert.value = false;

        // Kết nối WebSocket qua ApiGateway (cổng 8000)
        const socket = new WebSocket(`ws://localhost:8000/task_service/ws/status/${studentCode}`);

        socket.onmessage = (event) => {
            console.log('Dữ liệu WebSocket nhận được:', event.data);
            status_text.value = event.data;
        }

        const response = await axios.post(`${API_BASE}/task_service/start_test`, {
            "test_code": testCode.value,
            "email": email.value.toLowerCase(),
            "password": password.value,
            "full_name": fullName.value,
            "class_name": className.value
        });

        if (response.status === 200) {
            if (response.data.status == 'failed') {
                wait.value = false;
                alert.value = true;
                messageAlert.value = response.data.message || "Có lỗi xảy ra!";
                return;
            }
            show.value = true
            wait.value = false
            questions.value = response.data.data.questions;
            student.value = response.data.data.student;
            test.value = response.data.data.test;
            time.value = test.value.time;
            alert.value = false;
        } else {
            wait.value = false;
            status_text.value = "";
        }
    } catch (error) {
        console.error('Lỗi khởi tạo bài thi:', error);
        wait.value = false;
        alert.value = true;
        messageAlert.value = "Có lỗi kết nối đến API Gateway (Port 8000)! Vui lòng kiểm tra lại dịch vụ backend.";
    }
}

async function fetchStudentHistory() {
    if (!email.value) {
        alert.value = true
        messageAlert.value = "Vui lòng nhập Email sinh viên trước để tra cứu lịch sử thi!"
        return
    }
    const studentCode = email.value.toLowerCase().split("@")[0]
    if (!/^\d{10}$/.test(studentCode)) {
        alert.value = true
        messageAlert.value = "Mã sinh viên (phần trước @hunre.edu.vn) phải gồm đúng 10 chữ số!"
        return
    }
    historyLoading.value = true
    try {
        const res = await axios.get(`${API_BASE}/task_service/student/history/${studentCode}`)
        if (res.data.status === 'success') {
            studentHistoryList.value = res.data.data || []
            showHistoryModal.value = true
        } else {
            alert.value = true
            messageAlert.value = res.data.message || "Chưa tìm thấy lịch sử bài thi!"
        }
    } catch (error) {
        console.error("Lỗi lấy lịch sử sinh viên:", error)
        alert.value = true
        messageAlert.value = "Không thể lấy lịch sử thi lúc này!"
    } finally {
        historyLoading.value = false
    }
}
</script>

<template>
    <div class="main-wrapper">
        <n-space vertical :size="12" class="alert-container" v-if="alert">
            <n-alert title="Thông báo" type="error" closable @close="alert = false">
                {{ messageAlert }}
            </n-alert>
        </n-space>

        <!-- Nút Admin & Lịch sử -->
        <div class="top-nav-buttons" v-if="!show && !showResult">
            <n-button type="info" ghost size="medium" @click="fetchStudentHistory" style="margin-right: 10px; color: #fff; border-color: rgba(255,255,255,0.6);">
                📜 Tra cứu lịch sử thi
            </n-button>
            <router-link to="/admin" class="admin-link">
                <n-button type="default" ghost circle title="Trang quản trị Admin">
                    <template #icon>
                        <span>⚙️</span>
                    </template>
                </n-button>
            </router-link>
        </div>

        <!-- Hiển thị kết quả sau khi nộp bài -->
        <transition name="fade" mode="out-in">
            <div v-if="showResult && examResult" key="result">
                <Result :result="examResult" />
            </div>

            <!-- Hiển thị bài thi -->
            <div v-else-if="show && questions.length > 0" class="exam-view" key="exam">
                <div class="sticky-header">
                    <ExamsHeader 
                        :student="student" 
                        :time="time" 
                        :name="test.name" 
                        :totalQuestions="questions.length"
                        :answeredCount="answeredCount"
                        @time-up="onTimeUp" 
                    />
                </div>
                <div class="question-container">
                    <Question 
                        :questions="questions" 
                        @update:answers="onAnswersUpdate" 
                        @submit="handleSubmit" 
                    />
                </div>
            </div>

            <!-- Form đăng nhập -->
            <div class="container-main" v-else key="login">
                <div class="glass-card">
                    <div v-if="wait" class="card-spinner">
                        <n-spin size="large" stroke="#667eea" />
                        <p class="loading-text">{{ status_text }}</p>
                    </div>
                    <div class="login-form" v-else>
                        <h2 class="title">Đăng Nhập Thi Trắc Nghiệm</h2>
                        <p class="subtitle">Hệ thống Thi trực tuyến HUNRE Microservices (SOA)</p>

                        <div class="input-group">
                            <n-input v-model:value="testCode" size="large" type="text" placeholder="Mã đề thi (VD: SOA_01)" />
                        </div>
                        <div class="input-group">
                            <n-input v-model:value="email" size="large" type="text" placeholder="Email (VD: 2311060738@hunre.edu.vn)" />
                        </div>
                        <div class="input-group">
                            <n-input v-model:value="password" size="large" type="password" show-password-on="click" placeholder="Mật khẩu (Mã sinh viên)" />
                        </div>
                        <div class="input-group">
                            <n-input v-model:value="fullName" size="large" type="text" placeholder="Họ và Tên" />
                        </div>
                        <div class="input-group">
                            <n-input v-model:value="className" size="large" type="text" placeholder="Lớp (VD: ĐH CNTT K23A)" />
                        </div>

                        <n-button @click="handleClick" class="submit-btn" type="primary" size="large" block>
                            Bắt đầu làm bài
                        </n-button>
                    </div>
                </div>
            </div>
        </transition>

        <!-- Modal Tra cứu Lịch sử bài thi -->
        <n-modal 
            v-model:show="showHistoryModal" 
            preset="card" 
            title="📜 Lịch sử các bài thi đã nộp" 
            style="width: 600px; max-width: 90vw; border-radius: 16px;"
        >
            <div v-if="studentHistoryList.length === 0" style="text-align: center; padding: 20px; color: #64748b;">
                Chưa có lịch sử làm bài thi nào cho sinh viên này.
            </div>
            <div v-else class="history-list">
                <div v-for="(item, idx) in studentHistoryList" :key="idx" class="history-item">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>Mã bài thi (ID): {{ item.test_id }}</strong>
                        <n-tag :type="item.score >= 5 ? 'success' : 'error'">
                            Điểm: {{ item.score }}/10
                        </n-tag>
                    </div>
                    <div style="font-size: 13px; color: #64748b; margin-top: 6px;">
                        <span>Số câu đúng: {{ item.correct_count }}/{{ item.total_questions }}</span> • 
                        <span>Ngày nộp: {{ new Date(item.submitted_at).toLocaleString() }}</span>
                    </div>
                </div>
            </div>
        </n-modal>
    </div>
</template>

<style scoped>
.main-wrapper {
    min-height: 100vh;
    width: 100vw;
    background: linear-gradient(-45deg, #1e1b4b, #312e81, #0f172a, #1e293b);
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
    position: relative;
    overflow-x: hidden;
}

@keyframes gradientBG {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.alert-container {
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9999;
    width: 90%;
    max-width: 500px;
}

.top-nav-buttons {
    position: absolute;
    top: 20px;
    right: 20px;
    z-index: 100;
    display: flex;
    align-items: center;
}

.admin-link {
    display: inline-block;
}

.container-main {
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}

.glass-card {
    background: rgba(255, 255, 255, 0.12);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.18);
    padding: 40px;
    width: 90%;
    max-width: 480px;
    transition: transform 0.3s ease;
}

.glass-card:hover {
    transform: translateY(-4px);
}

.title {
    color: #fff;
    font-size: 26px;
    font-weight: 800;
    margin-bottom: 8px;
    text-align: center;
}

.subtitle {
    color: rgba(255, 255, 255, 0.85);
    text-align: center;
    margin-bottom: 28px;
    font-size: 14px;
}

.input-group {
    margin-bottom: 16px;
}

:deep(.n-input) {
    background-color: rgba(255, 255, 255, 0.92) !important;
    border-radius: 10px;
}

.submit-btn {
    margin-top: 10px;
    height: 50px;
    font-size: 18px;
    font-weight: bold;
    border-radius: 10px;
    background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
    border: none;
    transition: all 0.3s;
}

.submit-btn:hover {
    box-shadow: 0 5px 15px rgba(99, 102, 241, 0.4);
    transform: scale(1.02);
}

.card-spinner {
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    height: 300px;
}

.loading-text {
    color: #fff;
    margin-top: 20px;
    font-size: 18px;
    font-weight: 500;
}

.exam-view {
    background-color: #f8fafc;
    min-height: 100vh;
}

.sticky-header {
    position: sticky;
    top: 0;
    z-index: 1000;
}

.question-container {
    padding: 24px;
    max-width: 1050px;
    margin: 0 auto;
}

.history-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.history-item {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 18px;
}

.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.4s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}
</style>