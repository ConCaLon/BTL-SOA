<script setup>
import { ref } from 'vue'
import { NButton, NTag } from 'naive-ui'

const { result } = defineProps(['result'])

const showDetailModal = ref(false)

const goHome = () => {
    window.location.reload()
}
</script>

<template>
    <div class="result-container">
        <div class="result-card">
            <div class="result-icon">{{ result.score >= 5 ? '🎉' : '📖' }}</div>
            <h2 class="result-title">Kết Quả Bài Thi</h2>

            <div class="score-circle" :class="{ 'pass': result.score >= 5, 'fail': result.score < 5 }">
                <span class="score-number">{{ result.score }}</span>
                <span class="score-label">/ 10</span>
            </div>

            <div class="result-details">
                <div class="detail-row">
                    <span class="detail-label">✅ Số câu đúng:</span>
                    <span class="detail-value correct">{{ result.correct_count }} câu</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">❌ Số câu sai:</span>
                    <span class="detail-value wrong">{{ result.total_questions - result.correct_count }} câu</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">📝 Tổng số câu hỏi:</span>
                    <span class="detail-value">{{ result.total_questions }} câu</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">📊 Tỷ lệ chính xác:</span>
                    <span class="detail-value">
                        {{ result.total_questions > 0 ? Math.round((result.correct_count / result.total_questions) * 100) : 0 }}%
                    </span>
                </div>
            </div>

            <div class="result-message" v-if="result.score >= 5">
                <p style="color: #10b981;">🎊 Chúc mừng! Bạn đã hoàn thành xuất sắc bài thi.</p>
            </div>
            <div class="result-message" v-else>
                <p style="color: #ef4444;">😔 Bạn chưa đạt điểm chuẩn, hãy cố gắng học tập thêm nhé!</p>
            </div>

            <div class="button-group">
                <n-button 
                    v-if="result.answers && result.answers.length > 0"
                    type="info" 
                    ghost 
                    size="large" 
                    @click="showDetailModal = true"
                    style="border-radius: 10px; flex: 1;"
                >
                    Xem chi tiết bài làm
                </n-button>
                <n-button 
                    type="primary" 
                    size="large" 
                    @click="goHome" 
                    style="border-radius: 10px; flex: 1; background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);"
                >
                    Về Trang Chủ
                </n-button>
            </div>
        </div>

        <!-- Modal Xem Chi Tiết Đáp Án -->
        <n-modal 
            v-model:show="showDetailModal" 
            preset="card" 
            title="Chi tiết đáp án bài thi" 
            style="width: 700px; max-width: 90vw; border-radius: 16px;"
        >
            <div class="detail-answers-list">
                <div 
                    v-for="(ans, idx) in result.answers" 
                    :key="idx" 
                    class="answer-item-card"
                    :class="{ 'is-correct': ans.is_correct, 'is-wrong': !ans.is_correct }"
                >
                    <div class="ans-header">
                        <strong>Câu {{ idx + 1 }}:</strong>
                        <n-tag :type="ans.is_correct ? 'success' : 'error'" size="small">
                            {{ ans.is_correct ? 'Đúng (+1)' : 'Sai (0 điểm)' }}
                        </n-tag>
                    </div>
                    <div class="ans-body">
                        <p><strong>Đáp án bạn chọn:</strong> <span :class="ans.is_correct ? 'text-green' : 'text-red'">{{ ans.selected_answer || '(Chưa chọn)' }}</span></p>
                        <p v-if="!ans.is_correct"><strong>Đáp án đúng:</strong> <span class="text-green">{{ ans.correct_answer }}</span></p>
                    </div>
                </div>
            </div>
            <template #footer>
                <div style="text-align: right;">
                    <n-button @click="showDetailModal = false">Đóng</n-button>
                </div>
            </template>
        </n-modal>
    </div>
</template>

<style scoped>
.result-container {
    width: 100vw;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    padding: 40px 20px;
}

.result-card {
    background: white;
    border-radius: 24px;
    padding: 40px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.08);
    text-align: center;
    width: 100%;
    max-width: 520px;
}

.result-icon {
    font-size: 56px;
    margin-bottom: 6px;
}

.result-title {
    color: #0f172a;
    margin-bottom: 24px;
    font-size: 26px;
    font-weight: 800;
}

.score-circle {
    width: 130px;
    height: 130px;
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin: 0 auto 30px;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.score-circle.pass {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.score-circle.fail {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.score-number {
    color: white;
    font-size: 42px;
    font-weight: 900;
    line-height: 1;
}

.score-label {
    color: rgba(255, 255, 255, 0.85);
    font-size: 16px;
    font-weight: 700;
    margin-top: 4px;
}

.result-details {
    text-align: left;
    padding: 20px 24px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    margin-bottom: 24px;
}

.detail-row {
    display: flex;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px solid #f1f5f9;
}

.detail-row:last-child {
    border-bottom: none;
}

.detail-label {
    color: #475569;
    font-size: 15px;
    font-weight: 500;
}

.detail-value {
    font-weight: 700;
    font-size: 15px;
    color: #1e293b;
}

.detail-value.correct {
    color: #10b981;
}

.detail-value.wrong {
    color: #ef4444;
}

.result-message {
    margin-top: 15px;
    font-size: 16px;
    font-weight: 700;
}

.button-group {
    display: flex;
    gap: 12px;
    margin-top: 28px;
}

/* Modal detail styling */
.detail-answers-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-height: 60vh;
    overflow-y: auto;
}

.answer-item-card {
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    background: #f8fafc;
}

.answer-item-card.is-correct {
    border-left: 4px solid #10b981;
}

.answer-item-card.is-wrong {
    border-left: 4px solid #ef4444;
}

.ans-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.ans-body p {
    margin: 4px 0;
    font-size: 14px;
}

.text-green { color: #10b981; font-weight: 700; }
.text-red { color: #ef4444; font-weight: 700; }
</style>
