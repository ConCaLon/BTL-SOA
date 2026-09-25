<template>
    <main class="questions-wrapper">
        <div class="exam-layout">
            <!-- Cột Danh sách câu hỏi -->
            <div class="questions-column">
                <div 
                    class="list" 
                    v-for="(ques, index) in questions" 
                    :key="ques._id || index" 
                    :id="`question-${index}`"
                    :class="{ 'flagged-card': flaggedQuestions[ques._id] }"
                >
                    <div class="question-header-row">
                        <div class="question-title">
                            <span class="q-badge">Câu {{ index + 1 }}</span>
                            <span class="q-text">{{ ques.text }}</span>
                        </div>
                        <n-button 
                            size="small" 
                            :type="flaggedQuestions[ques._id] ? 'warning' : 'default'" 
                            secondary 
                            circle
                            @click="toggleFlag(ques._id)"
                            title="Đặt cờ theo dõi câu này"
                        >
                            <template #icon>
                                <span>{{ flaggedQuestions[ques._id] ? '⭐' : '☆' }}</span>
                            </template>
                        </n-button>
                    </div>

                    <div class="answers-container">
                        <n-radio-group 
                            :value="selectedOptions[ques._id]"
                            @update:value="(val) => selectOption(ques._id, val)" 
                            :name="`group-${index}`"
                        >
                            <n-grid cols="1" x-gap="12" y-gap="12">
                                <n-gi v-for="(option, idx) in ques.answers" :key="idx">
                                    <div 
                                        class="radio-card" 
                                        :class="{ 'selected': selectedOptions[ques._id] === option.text }" 
                                        @click="selectOption(ques._id, option.text)"
                                    >
                                        <n-radio 
                                            :value="option.text"
                                            :label="`${String.fromCharCode(65 + idx)}. ${option.text}`" 
                                        />
                                    </div>
                                </n-gi>
                            </n-grid>
                        </n-radio-group>
                    </div>
                </div>

                <div class="btn-end">
                    <n-button class="submit-btn" size="large" @click="openConfirmModal">
                        Nộp Bài Thi
                    </n-button>
                </div>
            </div>

            <!-- Cột Checklist / Question Palette -->
            <div class="checklist-column">
                <div class="checklist-card">
                    <h3 class="checklist-title">🎯 Bảng câu hỏi</h3>
                    <div class="checklist-summary">
                        <span>Đã làm: <strong>{{ answeredCount }} / {{ questions.length }}</strong></span>
                    </div>

                    <div class="checklist-grid">
                        <div 
                            v-for="(ques, index) in questions" 
                            :key="index"
                            class="checklist-item"
                            :class="{ 
                                'answered': selectedOptions[ques._id],
                                'flagged': flaggedQuestions[ques._id]
                            }"
                            @click="scrollToQuestion(index)"
                        >
                            {{ index + 1 }}
                            <span v-if="flaggedQuestions[ques._id]" class="star-icon">★</span>
                        </div>
                    </div>

                    <div class="checklist-status">
                        <div class="status-item"><div class="box answered-box"></div> Đã làm</div>
                        <div class="status-item"><div class="box flagged-box"></div> Đặt cờ</div>
                        <div class="status-item"><div class="box default-box"></div> Chưa làm</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal xác nhận nộp bài -->
        <n-modal 
            v-model:show="showConfirmModal" 
            preset="card" 
            title="Xác nhận nộp bài thi" 
            style="width: 480px; border-radius: 16px;"
        >
            <div class="confirm-modal-content">
                <p style="font-size: 16px; color: #334155;">Bạn có chắc chắn muốn nộp bài thi ngay bây giờ?</p>
                
                <div class="stat-box">
                    <div class="stat-line">
                        <span>Tổng số câu hỏi:</span>
                        <strong>{{ questions.length }} câu</strong>
                    </div>
                    <div class="stat-line" style="color: #10b981;">
                        <span>Số câu đã làm:</span>
                        <strong>{{ answeredCount }} câu</strong>
                    </div>
                    <div class="stat-line" style="color: #ef4444;" v-if="unansweredCount > 0">
                        <span>Số câu chưa làm:</span>
                        <strong>{{ unansweredCount }} câu</strong>
                    </div>
                    <div class="stat-line" style="color: #f59e0b;" v-if="flaggedCount > 0">
                        <span>Số câu đặt cờ:</span>
                        <strong>{{ flaggedCount }} câu</strong>
                    </div>
                </div>

                <div v-if="unansweredCount > 0" class="warning-alert">
                    ⚠️ <strong>Lưu ý:</strong> Bạn vẫn còn <strong>{{ unansweredCount }}</strong> câu chưa trả lời.
                </div>
            </div>

            <template #footer>
                <div style="display: flex; justify-content: flex-end; gap: 12px;">
                    <n-button @click="showConfirmModal = false" size="large">
                        Tiếp tục làm bài
                    </n-button>
                    <n-button type="primary" size="large" @click="confirmSubmit" style="background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);">
                        Nộp bài ngay
                    </n-button>
                </div>
            </template>
        </n-modal>
    </main>
</template>

<script setup>
import { ref, computed, defineProps, defineEmits } from "vue"

const props = defineProps(['questions'])
const emit = defineEmits(['submit', 'update:answers'])

const selectedOptions = ref({})
const flaggedQuestions = ref({})
const showConfirmModal = ref(false)

const answeredCount = computed(() => Object.keys(selectedOptions.value).length)
const unansweredCount = computed(() => (props.questions ? props.questions.length : 0) - answeredCount.value)
const flaggedCount = computed(() => Object.values(flaggedQuestions.value).filter(Boolean).length)

function selectOption(questionId, optionText) {
    selectedOptions.value[questionId] = optionText
    const answersArray = Object.entries(selectedOptions.value).map(([qId, ans]) => ({
        question_id: qId,
        selected_answer: ans
    }))
    emit('update:answers', answersArray)
}

function toggleFlag(questionId) {
    flaggedQuestions.value[questionId] = !flaggedQuestions.value[questionId]
}

function scrollToQuestion(index) {
    const el = document.getElementById(`question-${index}`)
    if (el) {
        const y = el.getBoundingClientRect().top + window.scrollY - 105
        window.scrollTo({ top: y, behavior: 'smooth' })
    }
}

function openConfirmModal() {
    showConfirmModal.value = true
}

function confirmSubmit() {
    showConfirmModal.value = false
    emit('submit')
}
</script>

<style scoped>
.questions-wrapper {
    padding-bottom: 60px;
}

.exam-layout {
    display: flex;
    gap: 24px;
    align-items: flex-start;
}

.questions-column {
    flex: 3;
}

.checklist-column {
    flex: 1;
    position: sticky;
    top: 105px;
}

.checklist-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
    border: 1px solid #e2e8f0;
}

.checklist-title {
    margin-top: 0;
    margin-bottom: 8px;
    font-size: 16px;
    color: #1e293b;
    text-align: center;
    font-weight: 700;
}

.checklist-summary {
    text-align: center;
    font-size: 13px;
    color: #64748b;
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid #f1f5f9;
}

.checklist-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(42px, 1fr));
    gap: 10px;
}

.checklist-item {
    aspect-ratio: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    background-color: #f1f5f9;
    color: #475569;
    font-weight: 700;
    cursor: pointer;
    border: 1px solid #cbd5e1;
    transition: all 0.2s ease;
    position: relative;
}

.checklist-item:hover {
    background-color: #e2e8f0;
    transform: scale(1.06);
}

.checklist-item.answered {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
    border-color: transparent;
    box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.checklist-item.flagged {
    border: 2px solid #f59e0b;
}

.checklist-item.answered.flagged {
    background: linear-gradient(135deg, #10b981 0%, #d97706 100%);
}

.star-icon {
    position: absolute;
    top: -4px;
    right: -4px;
    font-size: 10px;
    color: #f59e0b;
}

.checklist-status {
    margin-top: 20px;
    display: flex;
    justify-content: space-around;
    font-size: 12px;
    color: #64748b;
    font-weight: 500;
}

.status-item {
    display: flex;
    align-items: center;
    gap: 6px;
}

.box {
    width: 14px;
    height: 14px;
    border-radius: 4px;
}

.answered-box {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.flagged-box {
    background: #fef3c7;
    border: 2px solid #f59e0b;
}

.default-box {
    background-color: #f1f5f9;
    border: 1px solid #cbd5e1;
}

.list {
    background: #ffffff;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
    border: 1px solid #e2e8f0;
    transition: all 0.2s ease;
}

.list.flagged-card {
    border-left: 5px solid #f59e0b;
    background: #fffdf5;
}

.question-header-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 18px;
}

.question-title {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    flex: 1;
}

.q-badge {
    background: #e0e7ff;
    color: #4338ca;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 14px;
    white-space: nowrap;
}

.q-text {
    font-weight: 700;
    font-size: 17px;
    color: #1e293b;
    line-height: 1.5;
}

.answers-container {
    padding-left: 5px;
}

.radio-card {
    padding: 14px 18px;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    background-color: #f8fafc;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
}

.radio-card:hover {
    background-color: #f1f5f9;
    border-color: #cbd5e1;
}

.radio-card.selected {
    background-color: #eff6ff;
    border-color: #3b82f6;
    box-shadow: 0 2px 10px rgba(59, 130, 246, 0.15);
}

:deep(.n-radio) {
    width: 100%;
}

.btn-end {
    display: flex;
    justify-content: center;
    margin-top: 36px;
}

.submit-btn {
    height: 52px;
    padding: 0 45px;
    font-size: 18px;
    font-weight: bold;
    border-radius: 26px;
    background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
    color: white;
    border: none;
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35);
    transition: all 0.3s;
}

.submit-btn:hover {
    transform: translateY(-2px) scale(1.03);
    box-shadow: 0 10px 25px rgba(99, 102, 241, 0.45);
    color: white;
}

/* Modal styling */
.stat-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px;
    margin: 16px 0;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.stat-line {
    display: flex;
    justify-content: space-between;
    font-size: 15px;
}

.warning-alert {
    background: #fef3c7;
    border: 1px solid #fde68a;
    color: #b45309;
    padding: 12px;
    border-radius: 8px;
    font-size: 14px;
}
</style>