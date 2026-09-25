<script setup>
import { ref, computed, onBeforeUnmount, defineEmits, defineProps } from "vue";

const emit = defineEmits(['time-up'])

const props = defineProps({
    student: { type: Object, default: () => ({}) },
    time: { type: [Number, String], default: 45 },
    name: { type: String, default: "Bài thi" },
    totalQuestions: { type: Number, default: 0 },
    answeredCount: { type: Number, default: 0 }
})

const timeLeftInSeconds = ref(Number(props.time) * 60);

const formattedTime = computed(() => {
    const minutes = Math.floor(timeLeftInSeconds.value / 60);
    const seconds = timeLeftInSeconds.value % 60;
    return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
});

const progressPercentage = computed(() => {
    if (!props.totalQuestions || props.totalQuestions === 0) return 0;
    return Math.round((props.answeredCount / props.totalQuestions) * 100);
});

const isWarning = computed(() => timeLeftInSeconds.value <= 300); // < 5 mins
const isDanger = computed(() => timeLeftInSeconds.value <= 60); // < 1 min

const interval = setInterval(() => {
    timeLeftInSeconds.value -= 1;
    if (timeLeftInSeconds.value <= 0) {
        clearInterval(interval);
        emit('time-up');
    }
}, 1000);

onBeforeUnmount(() => {
    clearInterval(interval);
});
</script>

<template>
    <main class="header-wrapper">
        <div class="header-container">
            <div class="student-info">
                <div class="avatar">
                    {{ (student.student_name || student.name || 'S').charAt(0).toUpperCase() }}
                </div>
                <div class="details">
                    <span class="name">{{ student.student_name || student.name }}</span>
                    <span class="subtext">{{ student.student_code }} • {{ student.class_name || 'Học sinh' }}</span>
                </div>
            </div>

            <div class="name-test">
                <h2>{{ name }}</h2>
                <div class="progress-bar-wrapper">
                    <div class="progress-bar-fill" :style="{ width: `${progressPercentage}%` }"></div>
                </div>
                <span class="progress-text">Tiến độ: {{ answeredCount }}/{{ totalQuestions }} câu ({{ progressPercentage }}%)</span>
            </div>

            <div class="timer-container" :class="{ 'warning': isWarning, 'danger': isDanger }">
                <div class="timer-badge">
                    <span class="icon">⏱️</span>
                    <span class="timex">{{ formattedTime }}</span>
                </div>
            </div>
        </div>
    </main>
</template>

<style scoped>
.header-wrapper {
    width: 100%;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.header-container {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(12px);
    display: flex;
    height: 85px;
    align-items: center;
    padding: 0 30px;
    justify-content: space-between;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.student-info {
    display: flex;
    align-items: center;
    gap: 14px;
    flex: 1;
}

.avatar {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    font-weight: bold;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.35);
}

.details {
    display: flex;
    flex-direction: column;
}

.details .name {
    font-weight: 700;
    color: #1e293b;
    font-size: 16px;
}

.details .subtext {
    font-size: 13px;
    color: #64748b;
    font-weight: 500;
}

.name-test {
    flex: 2;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.name-test h2 {
    color: #0f172a;
    font-weight: 700;
    font-size: 19px;
    margin: 0 0 6px 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 450px;
}

.progress-bar-wrapper {
    width: 260px;
    height: 6px;
    background: #e2e8f0;
    border-radius: 10px;
    overflow: hidden;
}

.progress-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #10b981 0%, #059669 100%);
    border-radius: 10px;
    transition: width 0.3s ease;
}

.progress-text {
    font-size: 11px;
    color: #64748b;
    margin-top: 3px;
    font-weight: 600;
}

.timer-container {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: flex-end;
}

.timer-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #f1f5f9;
    padding: 8px 18px;
    border-radius: 30px;
    font-size: 22px;
    font-weight: 800;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    transition: all 0.3s ease;
}

.timer-container.warning .timer-badge {
    background: #fef3c7;
    color: #d97706;
    border-color: #fde68a;
}

.timer-container.danger .timer-badge {
    background: #fee2e2;
    color: #dc2626;
    border-color: #fca5a5;
    animation: pulse 1s infinite;
}

.timer-badge .icon {
    font-size: 20px;
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.04); }
    100% { transform: scale(1); }
}
</style>