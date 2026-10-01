<script setup>
import { ref, onMounted, computed, h } from 'vue'
import { NButton, NPopconfirm, NSpace, NTag, NCard, NGrid, NGi, NStatistic, NInput } from 'naive-ui'
import axios from 'axios'
import * as XLSX from 'xlsx'
import { Eye } from '@lucide/vue'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

// Cổng API Gateway 8000
const API_BASE = "http://localhost:8000"
const activeTab = ref('dashboard')

// Auth state
const isAuthenticated = ref(false)
const username = ref('')
const password = ref('')
const loginError = ref('')

// Dữ liệu
const students = ref([])
const results = ref([])
const questions = ref([])
const tests = ref([])
const selectedTestId = ref(null)
const loading = ref(false)

const currentSelectedTest = computed(() => {
    return tests.value.find(t => t._id === selectedTestId.value) || null
})

function navigateToQuestions(testId) {
    selectedTestId.value = testId
    activeTab.value = 'questions'
    fetchQuestions()
}

// Search filters
const testSearchQuery = ref('')
const resultSearchQuery = ref('')
const studentSearchQuery = ref('')

// Student History Modal
const showStudentHistoryModal = ref(false)
const selectedStudentCode = ref('')
const studentHistoryData = ref([])

// Submission Detail Modal
const showSubmissionDetailModal = ref(false)
const selectedSubmission = ref(null)

// Test Filter cho bảng kết quả
const selectedTestFilter = ref(null)

const testFilterOptions = computed(() => {
    const uniqueTests = new Map()
    results.value.forEach(r => {
        if (r.test_id && !uniqueTests.has(r.test_id)) {
            uniqueTests.set(r.test_id, r.test_title || r.test_id)
        }
    })
    const options = [{ label: 'Tất cả bài thi', value: null }]
    uniqueTests.forEach((title, id) => {
        options.push({ label: title, value: id })
    })
    return options
})

function openSubmissionDetail(row) {
    selectedSubmission.value = row
    showSubmissionDetailModal.value = true
}

// CRUD Test state
const showTestModal = ref(false)
const isEditingTest = ref(false)
const editingTestId = ref(null)
const testForm = ref({
    test_code: '',
    name: '',
    time: "45",
    list_students: ''
})

// Excel Import State cho Danh sách MSV
const excelFileInputRef = ref(null)
const studentExcelInputRef = ref(null)
const excelStatusMessage = ref('')
const showExcelModeModal = ref(false)
const pendingExtractedMSVs = ref([])
const pendingExtractedStudents = ref([])
const excelFileName = ref('')

// CRUD Student state
const showStudentModal = ref(false)
const isEditingStudent = ref(false)
const originalStudentCode = ref('')
const studentForm = ref({
    student_code: '',
    student_name: '',
    class_name: '',
    faculty: ''
})

// CRUD Question state
const showQuestionModal = ref(false)
const isEditing = ref(false)
const editingQuestionId = ref(null)
const questionForm = ref({
    text: '',
    answers: [
        { text: '', is_correct: true },
        { text: '', is_correct: false },
        { text: '', is_correct: false },
        { text: '', is_correct: false }
    ]
})

// Computed Dashboard Stats
const totalStudentsCount = computed(() => students.value.length)
const totalTestsCount = computed(() => tests.value.length)
const totalSubmissionsCount = computed(() => results.value.length)
const averageScore = computed(() => {
    if (results.value.length === 0) return 0
    const sum = results.value.reduce((acc, r) => acc + (r.score || 0), 0)
    return (sum / results.value.length).toFixed(2)
})

// Biểu đồ phổ điểm
const scoreDistributionData = computed(() => {
    let weak = 0, avg = 0, good = 0, excellent = 0
    results.value.forEach(r => {
        const s = r.score || 0
        if (s < 4) weak++
        else if (s < 6.5) avg++
        else if (s < 8) good++
        else excellent++
    })
    return {
        labels: ['Yếu (< 4.0)', 'Trung bình (4.0 - 6.4)', 'Khá (6.5 - 7.9)', 'Giỏi (8.0 - 10.0)'],
        datasets: [{
            label: 'Số lượt nộp',
            data: [weak, avg, good, excellent],
            backgroundColor: ['#ef4444', '#f59e0b', '#3b82f6', '#10b981'],
            borderRadius: 8,
            borderSkipped: false,
            barPercentage: 0.6,
            categoryPercentage: 0.7
        }]
    }
})

const scoreChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: {
            backgroundColor: '#1e293b',
            titleFont: { size: 13, weight: '600' },
            bodyFont: { size: 13 },
            padding: 10,
            cornerRadius: 8,
            callbacks: {
                label: (ctx) => `  ${ctx.parsed.y} lượt nộp`
            }
        }
    },
    scales: {
        x: {
            grid: { display: false },
            ticks: { color: '#64748b', font: { size: 12, weight: '500' } }
        },
        y: {
            beginAtZero: true,
            ticks: {
                color: '#94a3b8',
                font: { size: 12 },
                stepSize: 1,
                precision: 0
            },
            grid: { color: '#f1f5f9' }
        }
    }
}

// Computed Filtered Lists
const filteredTests = computed(() => {
    if (!testSearchQuery.value) return tests.value
    const q = testSearchQuery.value.toLowerCase()
    return tests.value.filter(t => 
        (t.test_code && t.test_code.toLowerCase().includes(q)) ||
        (t.name && t.name.toLowerCase().includes(q))
    )
})

const filteredResults = computed(() => {
    let data = results.value

    // Lọc theo bài thi
    if (selectedTestFilter.value) {
        data = data.filter(r => r.test_id === selectedTestFilter.value)
    }

    // Lọc theo từ khóa tìm kiếm
    if (resultSearchQuery.value) {
        const q = resultSearchQuery.value.toLowerCase()
        data = data.filter(r =>
            (r.student_code && r.student_code.toLowerCase().includes(q)) ||
            (r.student_name && r.student_name.toLowerCase().includes(q)) ||
            (r.test_title && r.test_title.toLowerCase().includes(q))
        )
    }

    return data
})

const filteredStudents = computed(() => {
    if (!studentSearchQuery.value) return students.value
    const q = studentSearchQuery.value.toLowerCase()
    return students.value.filter(s => 
        (s.student_code && s.student_code.toLowerCase().includes(q)) ||
        (s.student_name && s.student_name.toLowerCase().includes(q)) ||
        (s.class_name && s.class_name.toLowerCase().includes(q)) ||
        (s.faculty && s.faculty.toLowerCase().includes(q))
    )
})

// Columns cho Data Table
const testColumns = [
    { title: 'Mã đề', key: 'test_code' },
    { title: 'Tên bài thi', key: 'name' },
    { title: 'Thời gian', key: 'time', render: (row) => `${row.time} phút` },
    { 
        title: 'Số câu hỏi', 
        key: 'question_count',
        render: (row) => h(NTag, { type: (row.question_count > 0 ? 'info' : 'default'), size: 'small' }, { default: () => `${row.question_count || 0} câu` })
    },
    { 
        title: 'Sinh viên được thi', 
        key: 'list_students',
        render: (row) => {
            const list = row.list_students || row.list_student || []
            if (list.length === 0) return h(NTag, { type: 'success' }, { default: () => 'Tất cả sinh viên' })
            return h(NTag, { type: 'warning' }, { default: () => `${list.length} SV được chỉ định` })
        }
    },
    { title: 'Hành động', key: 'actions', render: (row) => {
        return h(NSpace, {}, {
            default: () => [
                h(NButton, { size: 'small', type: 'primary', ghost: true, onClick: () => navigateToQuestions(row._id) }, { default: () => '❓ Câu hỏi' }),
                h(NButton, { size: 'small', type: 'info', onClick: () => openEditTestModal(row) }, { default: () => 'Sửa' }),
                h(NPopconfirm, {
                    onPositiveClick: () => deleteTest(row._id),
                    positiveText: 'Xóa',
                    negativeText: 'Hủy'
                }, {
                    trigger: () => h(NButton, { size: 'small', type: 'error' }, { default: () => 'Xóa' }),
                    default: () => `Xóa mã đề ${row.test_code}? Thao tác này sẽ xóa cả các câu hỏi thuộc mã đề!`
                })
            ]
        })
    }}
]

const studentColumns = [
    { title: 'Mã Sinh Viên', key: 'student_code' },
    { title: 'Họ và Tên', key: 'student_name', render: (row) => row.student_name || row.name || 'N/A' },
    { 
        title: 'Lớp', 
        key: 'class_name',
        render: (row) => row.class_name ? h(NTag, { type: 'info', size: 'small' }, { default: () => row.class_name }) : h('span', { style: 'color: #94a3b8;' }, 'Chưa nhập')
    },
    { 
        title: 'Khoa', 
        key: 'faculty',
        render: (row) => row.faculty ? h(NTag, { type: 'success', size: 'small' }, { default: () => row.faculty }) : h('span', { style: 'color: #94a3b8;' }, 'Chưa nhập')
    },
    { title: 'Thao tác', key: 'actions', render: (row) => {
        return h(NSpace, {}, {
            default: () => [
                h(NButton, { size: 'small', type: 'info', onClick: () => openEditStudentModal(row) }, { default: () => 'Sửa' }),
                h(NPopconfirm, {
                    onPositiveClick: () => deleteStudent(row.student_code),
                    positiveText: 'Xóa',
                    negativeText: 'Hủy'
                }, {
                    trigger: () => h(NButton, { size: 'small', type: 'error' }, { default: () => 'Xóa' }),
                    default: () => `Xóa sinh viên MSV: ${row.student_code}?`
                }),
                h(NButton, { size: 'small', type: 'primary', ghost: true, onClick: () => viewStudentHistory(row.student_code) }, { default: () => 'Lịch sử thi' })
            ]
        })
    }}
]

const resultColumns = [
    {
        title: 'Sinh viên',
        key: 'student_code',
        render: (row) => h('div', {}, [
            h('div', { style: 'font-weight: 600; color: #1e293b; line-height: 1.4;' }, row.student_name || 'N/A'),
            h('div', { style: 'font-size: 12px; color: #94a3b8; margin-top: 1px;' }, row.student_code)
        ])
    },
    {
        title: 'Bài Thi',
        key: 'test_title',
        ellipsis: { tooltip: true },
        render: (row) => row.test_title || row.test_id
    },
    {
        title: 'Điểm số',
        key: 'score',
        width: 105,
        render: (row) => {
            const isPass = row.score >= 5
            return h(NTag, {
                type: isPass ? 'success' : 'error',
                round: true,
                style: 'font-weight: 700;'
            }, { default: () => `${row.score}/10` })
        }
    },
    {
        title: 'Số câu đúng',
        key: 'correct_answers',
        width: 115,
        render: (row) => `${row.correct_answers}/${row.total_questions}`
    },
    {
        title: 'Thời gian nộp',
        key: 'submitted_at',
        width: 165
    },
    {
        title: 'Thao tác',
        key: 'actions',
        width: 80,
        render: (row) => h(NButton, {
            size: 'small',
            type: 'info',
            ghost: true,
            circle: true,
            onClick: () => openSubmissionDetail(row)
        }, {
            default: () => h(Eye, { size: 16 })
        })
    }
]

const questionColumns = [
    { title: 'STT', key: 'index', width: 60, render: (_, index) => index + 1 },
    { title: 'Nội dung câu hỏi', key: 'text', ellipsis: { tooltip: true } },
    { 
        title: 'Các phương án & Đáp án đúng', 
        key: 'answers',
        render: (row) => {
            if (!row.answers || row.answers.length === 0) return 'N/A'
            return h('div', { style: 'display: flex; flex-direction: column; gap: 4px;' }, row.answers.map((a, idx) => {
                const label = `${String.fromCharCode(65 + idx)}. ${a.text}`
                if (a.is_correct) {
                    return h(NTag, { type: 'success', size: 'small', style: 'font-weight: bold;' }, { default: () => `✓ ${label} (Đúng)` })
                }
                return h('span', { style: 'font-size: 13px; color: #475569;' }, label)
            }))
        }
    },
    { title: 'Hành động', key: 'actions', width: 140, render: (row) => {
        return h(NSpace, {}, {
            default: () => [
                h(NButton, { size: 'small', type: 'info', onClick: () => openEditModal(row) }, { default: () => 'Sửa' }),
                h(NPopconfirm, {
                    onPositiveClick: () => deleteQuestion(row._id),
                    positiveText: 'Xóa',
                    negativeText: 'Hủy'
                }, {
                    trigger: () => h(NButton, { size: 'small', type: 'error' }, { default: () => 'Xóa' }),
                    default: () => 'Bạn có chắc muốn xóa câu hỏi này?'
                })
            ]
        })
    }}
]

function handleLogin() {
    if (username.value === 'admin' && password.value === 'admin') {
        isAuthenticated.value = true
        loginError.value = ''
        fetchData()
        fetchBgSettings()
    } else {
        loginError.value = 'Sai tài khoản hoặc mật khẩu! (Mặc định: admin / admin)'
    }
}

async function fetchData() {
    if (!isAuthenticated.value) return
    loading.value = true
    try {
        const [resTests, resStudents, resResults] = await Promise.all([
            axios.get(`${API_BASE}/task_service/admin/tests`).catch(() => ({ data: { status: 'failed' } })),
            axios.get(`${API_BASE}/task_service/admin/students`).catch(() => ({ data: { status: 'failed' } })),
            axios.get(`${API_BASE}/task_service/admin/results`).catch(() => ({ data: { status: 'failed' } }))
        ])

        if (resTests.data.status === 'success') {
            tests.value = resTests.data.data || []
            if (tests.value.length > 0) {
                const exists = tests.value.some(t => t._id === selectedTestId.value)
                if (!exists) {
                    selectedTestId.value = tests.value[0]._id
                }
            } else {
                selectedTestId.value = null
            }
        }
        if (resStudents.data.status === 'success') students.value = resStudents.data.data || []
        if (resResults.data.status === 'success') results.value = resResults.data.data || []

        // Luôn load câu hỏi nếu đang ở tab questions và có test được chọn
        if (activeTab.value === 'questions' && selectedTestId.value) {
            await fetchQuestions()
        }
    } catch (error) {
        console.error("Lỗi lấy dữ liệu Admin qua ApiGateway:", error)
    } finally {
        loading.value = false
    }
}

async function fetchQuestions() {
    if (!selectedTestId.value) {
        questions.value = []
        return
    }
    loading.value = true
    try {
        const resQ = await axios.post(`${API_BASE}/task_service/admin/questions`, { test_id: selectedTestId.value })
        if (resQ.data.status === 'success') {
            questions.value = resQ.data.data || []
            // Đồng bộ lại question_count trong danh sách tests
            const curTest = tests.value.find(t => t._id === selectedTestId.value)
            if (curTest) {
                curTest.question_count = questions.value.length
            }
        } else {
            questions.value = []
        }
    } catch (error) {
        console.error("Lỗi lấy câu hỏi:", error)
        questions.value = []
    } finally {
        loading.value = false
    }
}

async function viewStudentHistory(studentCode) {
    selectedStudentCode.value = studentCode
    try {
        const res = await axios.get(`${API_BASE}/task_service/student/history/${studentCode}`)
        if (res.data.status === 'success') {
            studentHistoryData.value = res.data.data || []
            showStudentHistoryModal.value = true
        }
    } catch (error) {
        console.error("Lỗi xem lịch sử sinh viên:", error)
    }
}

// ================= STUDENT CRUD =================
function openCreateStudentModal() {
    isEditingStudent.value = false
    originalStudentCode.value = ''
    studentForm.value = {
        student_code: '',
        student_name: '',
        class_name: '',
        faculty: ''
    }
    showStudentModal.value = true
}

function openEditStudentModal(s) {
    isEditingStudent.value = true
    originalStudentCode.value = s.student_code
    studentForm.value = {
        student_code: s.student_code,
        student_name: s.student_name || s.name || '',
        class_name: s.class_name || '',
        faculty: s.faculty || ''
    }
    showStudentModal.value = true
}

async function saveStudent() {
    if (!studentForm.value.student_code || !studentForm.value.student_name) {
        alert("Vui lòng nhập Mã sinh viên và Họ tên!")
        return
    }
    if (!/^\d{10}$/.test(studentForm.value.student_code)) {
        alert("Mã sinh viên (MSV) phải gồm đúng 10 chữ số!")
        return
    }
    loading.value = true
    try {
        const payload = {
            old_student_code: isEditingStudent.value ? originalStudentCode.value : studentForm.value.student_code,
            student_code: studentForm.value.student_code,
            student_name: studentForm.value.student_name,
            name: studentForm.value.student_name,
            class_name: studentForm.value.class_name,
            faculty: studentForm.value.faculty
        }
        let res
        if (isEditingStudent.value) {
            res = await axios.put(`${API_BASE}/task_service/admin/students/update`, payload)
        } else {
            res = await axios.post(`${API_BASE}/task_service/admin/students/create`, payload)
        }

        if (res.data && res.data.status === 'failed') {
            alert(res.data.message || "Lỗi lưu thông tin sinh viên!")
            return
        }

        showStudentModal.value = false
        fetchData()
    } catch (error) {
        console.error("Lỗi lưu thông tin sinh viên:", error)
        alert(error.response?.data?.message || "Lỗi lưu thông tin sinh viên!")
    } finally {
        loading.value = false
    }
}

async function deleteStudent(studentCode) {
    loading.value = true
    try {
        await axios.delete(`${API_BASE}/task_service/admin/students/delete`, { data: { student_code: studentCode } })
        fetchData()
    } catch (error) {
        console.error("Lỗi xóa sinh viên:", error)
    } finally {
        loading.value = false
    }
}

// ================= TEST CRUD & EXCEL IMPORT =================
function openCreateTestModal() {
    isEditingTest.value = false
    editingTestId.value = null
    testForm.value = { test_code: '', name: '', time: "45", list_students: '' }
    excelStatusMessage.value = ''
    showTestModal.value = true
}

function openEditTestModal(t) {
    isEditingTest.value = true
    editingTestId.value = t._id
    testForm.value = {
        test_code: t.test_code || '',
        name: t.name,
        time: String(t.time),
        list_students: (t.list_students || t.list_student || []).join(', ')
    }
    excelStatusMessage.value = ''
    showTestModal.value = true
}

async function saveTest() {
    if (!testForm.value.test_code || !testForm.value.test_code.trim()) {
        alert("Vui lòng nhập Mã đề thi (viết liền, ví dụ: SOA_01)!")
        return
    }
    if (!testForm.value.name || !testForm.value.name.trim()) {
        alert("Vui lòng nhập Tên bài thi!")
        return
    }

    loading.value = true
    try {
        const studentList = testForm.value.list_students
            ? testForm.value.list_students.split(/[\s,\n;\r]+/).map(s => s.trim()).filter(s => s)
            : []
            
        const payload = {
            test_code: testForm.value.test_code.trim(),
            name: testForm.value.name.trim(),
            time: parseInt(testForm.value.time) || 45,
            list_students: studentList
        }
        
        let res
        if (isEditingTest.value) {
            res = await axios.put(`${API_BASE}/task_service/admin/tests/update`, { ...payload, test_id: editingTestId.value })
        } else {
            res = await axios.post(`${API_BASE}/task_service/admin/tests/create`, payload)
        }

        if (res.data && res.data.status === 'failed') {
            alert(res.data.message || "Lỗi lưu mã đề!")
            return
        }

        // Tự động đồng bộ các MSV này vào DB Sinh viên (StudentService) nếu chưa có
        if (studentList.length > 0) {
            const syncPromises = studentList.map(code => {
                if (/^\d{10}$/.test(code)) {
                    return axios.post(`${API_BASE}/task_service/admin/students/create`, {
                        student_code: code,
                        student_name: `Sinh viên ${code}`,
                        name: `Sinh viên ${code}`,
                        class_name: 'Chưa xếp lớp',
                        faculty: 'CNTT'
                    }).catch(e => console.log('Sync student silent error:', e))
                }
                return Promise.resolve()
            })
            await Promise.all(syncPromises)
        }

        showTestModal.value = false
        if (res.data && res.data.data && res.data.data._id) {
            selectedTestId.value = res.data.data._id
        }
        await fetchData()
    } catch (error) {
        console.error("Lỗi lưu test:", error)
        alert(error.response?.data?.message || "Lỗi lưu mã đề thi!")
    } finally {
        loading.value = false
    }
}

async function deleteTest(id) {
    loading.value = true
    try {
        const res = await axios.delete(`${API_BASE}/task_service/admin/tests/delete`, { data: { test_id: id } })
        if (res.data && res.data.status === 'failed') {
            alert(res.data.message || "Lỗi xóa mã đề!")
            return
        }
        if (selectedTestId.value === id) {
            selectedTestId.value = null
        }
        await fetchData()
    } catch (error) {
        console.error("Lỗi xóa test:", error)
        alert(error.response?.data?.message || "Lỗi xóa bài thi!")
    } finally {
        loading.value = false
    }
}

function triggerExcelUpload() {
    if (excelFileInputRef.value) {
        excelFileInputRef.value.click()
    }
}

function downloadExcelTemplate() {
    try {
        const workbook = XLSX.utils.book_new()
        const sampleData = [
            ["STT", "MSV", "Họ và Tên", "Lớp", "Khoa"],
            [1, "2311060738", "Nguyễn Văn A", "ĐH CNTT K23A", "Công nghệ Thông tin"],
            [2, "2311060001", "Trần Thị B", "ĐH CNTT K23A", "Công nghệ Thông tin"],
            [3, "2311060002", "Lê Văn C", "ĐH CNTT K23B", "Công nghệ Thông tin"]
        ]
        const worksheet = XLSX.utils.aoa_to_sheet(sampleData)
        worksheet['!cols'] = [
            { wch: 6 },
            { wch: 15 },
            { wch: 25 },
            { wch: 18 },
            { wch: 25 }
        ]
        XLSX.utils.book_append_sheet(workbook, worksheet, "Danh_Sach_MSV")
        XLSX.writeFile(workbook, "Mau_Danh_Sach_MSV_Duoc_Phep_Thi.xlsx")
    } catch (err) {
        console.error("Lỗi tải file mẫu Excel:", err)
        alert("Lỗi tải file mẫu Excel!")
    }
}

function handleExcelUpload(event) {
    const file = event.target.files[0]
    if (!file) return

    excelFileName.value = file.name
    const reader = new FileReader()

    reader.onload = (e) => {
        try {
            const data = new Uint8Array(e.target.result)
            const workbook = XLSX.read(data, { type: 'array' })
            const firstSheetName = workbook.SheetNames[0]
            const worksheet = workbook.Sheets[firstSheetName]
            
            const rawRows = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
            if (!rawRows || rawRows.length === 0) {
                alert("File Excel trống hoặc không đúng định dạng!")
                return
            }

            let extractedMSVs = []
            let msvColIndex = -1

            if (rawRows.length > 0) {
                const headerRow = rawRows[0]
                if (Array.isArray(headerRow)) {
                    for (let i = 0; i < headerRow.length; i++) {
                        const cellVal = String(headerRow[i] || '').trim().toLowerCase()
                        if (/msv|mã sv|mã sinh viên|student_code|student code|student id/i.test(cellVal)) {
                            msvColIndex = i
                            break
                        }
                    }
                }
            }

            rawRows.forEach((row, rowIndex) => {
                if (!Array.isArray(row)) return
                
                if (msvColIndex !== -1 && rowIndex > 0) {
                    const val = String(row[msvColIndex] || '').trim()
                    if (val && !/msv|mã sv|mã sinh viên|student/i.test(val)) {
                        const cleaned = val.replace(/\s+/g, '')
                        if (cleaned) extractedMSVs.push(cleaned)
                    }
                } else {
                    row.forEach(cell => {
                        if (cell === null || cell === undefined) return
                        const cellStr = String(cell).trim()
                        const matches = cellStr.match(/\b\d{8,12}\b/g)
                        if (matches) {
                            matches.forEach(m => extractedMSVs.push(m))
                        }
                    })
                }
            })

            extractedMSVs = Array.from(new Set(extractedMSVs))

            if (extractedMSVs.length === 0) {
                alert("Không tìm thấy Mã sinh viên (MSV) nào trong file Excel! Vui lòng kiểm tra lại file hoặc dùng file mẫu.")
                return
            }

            pendingExtractedMSVs.value = extractedMSVs

            const currentContent = testForm.value.list_students ? testForm.value.list_students.trim() : ''
            if (currentContent.length > 0) {
                showExcelModeModal.value = true
            } else {
                applyExcelMSVs('replace')
            }
        } catch (err) {
            console.error("Lỗi đọc file Excel:", err)
            alert("Lỗi đọc file Excel. Vui lòng đảm bảo file hợp lệ (.xlsx, .xls, .csv).")
        } finally {
            if (event.target) event.target.value = ''
        }
    }

    reader.readAsArrayBuffer(file)
}

function applyExcelMSVs(mode) {
    if (mode === 'replace') {
        testForm.value.list_students = pendingExtractedMSVs.value.join(', ')
        excelStatusMessage.value = `Đã nạp ${pendingExtractedMSVs.value.length} MSV từ file "${excelFileName.value}" (Ghi đè)`
    } else if (mode === 'append') {
        const existingList = testForm.value.list_students
            ? testForm.value.list_students.split(',').map(s => s.trim()).filter(s => s)
            : []
        const merged = Array.from(new Set([...existingList, ...pendingExtractedMSVs.value]))
        testForm.value.list_students = merged.join(', ')
        excelStatusMessage.value = `Đã thêm ${pendingExtractedMSVs.value.length} MSV từ file "${excelFileName.value}" (Tổng: ${merged.length} MSV)`
    }
    showExcelModeModal.value = false
}

function triggerStudentExcelUpload() {
    if (studentExcelInputRef.value) {
        studentExcelInputRef.value.click()
    }
}

function handleStudentExcelUpload(event) {
    const file = event.target.files[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = async (e) => {
        try {
            loading.value = true
            const data = new Uint8Array(e.target.result)
            const workbook = XLSX.read(data, { type: 'array' })
            const worksheet = workbook.Sheets[workbook.SheetNames[0]]
            const rawRows = XLSX.utils.sheet_to_json(worksheet)

            if (!rawRows || rawRows.length === 0) {
                alert("File Excel sinh viên trống hoặc không đọc được dữ liệu!")
                return
            }

            let successCount = 0
            for (const row of rawRows) {
                let code = String(row['MSV'] || row['Mã SV'] || row['Mã sinh viên'] || row['student_code'] || row['Student ID'] || '').trim()
                if (!code) {
                    const val = Object.values(row).find(v => v && /^\d{10}$/.test(String(v).trim()))
                    if (val) code = String(val).trim()
                }

                const name = String(row['Họ và Tên'] || row['Họ tên'] || row['Tên'] || row['student_name'] || row['name'] || '').trim()
                const className = String(row['Lớp'] || row['class_name'] || '').trim()
                const faculty = String(row['Khoa'] || row['faculty'] || '').trim()

                if (code && /^\d{10}$/.test(code)) {
                    await axios.post(`${API_BASE}/task_service/admin/students/create`, {
                        student_code: code,
                        student_name: name || `Sinh viên ${code}`,
                        name: name || `Sinh viên ${code}`,
                        class_name: className || 'Chưa xếp lớp',
                        faculty: faculty || 'CNTT'
                    }).catch(e => console.log('Err create student:', e))
                    successCount++
                }
            }
            alert(`Đã nhập/cập nhật thành công ${successCount} sinh viên vào CSDL!`)
            fetchData()
        } catch (err) {
            console.error("Lỗi đọc file Excel Sinh viên:", err)
            alert("Lỗi import file Excel Sinh viên. Vui lòng kiểm tra định dạng file.")
        } finally {
            loading.value = false
            if (event.target) event.target.value = ''
        }
    }
    reader.readAsArrayBuffer(file)
}

// ================= QUESTION CRUD =================
function openCreateModal() {
    if (!selectedTestId.value) {
        alert("Vui lòng chọn một mã đề trước!")
        return
    }
    isEditing.value = false
    editingQuestionId.value = null
    questionForm.value = {
        text: '',
        answers: [
            { text: '', is_correct: true },
            { text: '', is_correct: false },
            { text: '', is_correct: false },
            { text: '', is_correct: false }
        ]
    }
    showQuestionModal.value = true
}

function openEditModal(question) {
    isEditing.value = true
    editingQuestionId.value = question._id
    
    let answers = []
    if (question.answers && Array.isArray(question.answers) && question.answers.length > 0) {
        answers = JSON.parse(JSON.stringify(question.answers))
    }
    // Đảm bảo tối thiểu 4 đáp án
    while (answers.length < 4) {
        answers.push({ text: '', is_correct: false })
    }
    // Đảm bảo có ít nhất 1 đáp án được đánh dấu đúng
    if (!answers.some(a => a.is_correct)) {
        answers[0].is_correct = true
    }

    questionForm.value = {
        text: question.text || '',
        answers: answers
    }
    showQuestionModal.value = true
}

function setCorrectAnswer(index) {
    questionForm.value.answers.forEach((ans, i) => {
        ans.is_correct = (i === index)
    })
}

async function saveQuestion() {
    if (!questionForm.value.text || !questionForm.value.text.trim()) {
        alert("Vui lòng nhập nội dung câu hỏi!")
        return
    }
    const emptyAns = questionForm.value.answers.some(a => !a.text || !a.text.trim())
    if (emptyAns) {
        alert("Vui lòng điền đầy đủ nội dung cho tất cả các đáp án A, B, C, D!")
        return
    }
    const hasCorrect = questionForm.value.answers.some(a => a.is_correct)
    if (!hasCorrect) {
        alert("Vui lòng chọn một đáp án đúng (tích vào nút tròn)!")
        return
    }

    loading.value = true
    try {
        let res
        const formattedAnswers = questionForm.value.answers.map(a => ({
            text: a.text.trim(),
            is_correct: !!a.is_correct
        }))

        if (isEditing.value) {
            res = await axios.put(`${API_BASE}/task_service/admin/questions/update`, {
                question_id: editingQuestionId.value,
                text: questionForm.value.text.trim(),
                answers: formattedAnswers
            })
        } else {
            res = await axios.post(`${API_BASE}/task_service/admin/questions/create`, {
                test_id: selectedTestId.value,
                text: questionForm.value.text.trim(),
                answers: formattedAnswers
            })
        }

        if (res.data && res.data.status === 'failed') {
            alert(res.data.message || "Lỗi lưu câu hỏi!")
            return
        }

        showQuestionModal.value = false
        await fetchQuestions()
        
        // Cập nhật lại số câu hỏi trong danh sách tests
        const curTest = tests.value.find(t => t._id === selectedTestId.value)
        if (curTest) {
            curTest.question_count = questions.value.length
        }
    } catch (error) {
        console.error("Lỗi lưu câu hỏi:", error)
        alert(error.response?.data?.message || "Lỗi kết nối khi lưu câu hỏi!")
    } finally {
        loading.value = false
    }
}

async function deleteQuestion(id) {
    loading.value = true
    try {
        const res = await axios.delete(`${API_BASE}/task_service/admin/questions/delete`, {
            data: { question_id: id }
        })
        if (res.data && res.data.status === 'failed') {
            alert(res.data.message || "Lỗi xóa câu hỏi!")
            return
        }
        await fetchQuestions()
        
        // Cập nhật lại số câu hỏi trong danh sách tests
        const curTest = tests.value.find(t => t._id === selectedTestId.value)
        if (curTest) {
            curTest.question_count = questions.value.length
        }
    } catch (error) {
        console.error("Lỗi xóa câu hỏi:", error)
        alert(error.response?.data?.message || "Lỗi xóa câu hỏi!")
    } finally {
        loading.value = false
    }
}

// ================= CÀI ĐẶT HÌNH NỀN ĐĂNG NHẬP =================
const currentBgImage = ref(localStorage.getItem("quiz_app_bg_image") || "")
const currentBgDim = ref(Number(localStorage.getItem("quiz_app_bg_dim")) || 45)
const currentBgBlur = ref(Number(localStorage.getItem("quiz_app_bg_blur")) || 0)

const tempBgImage = ref(localStorage.getItem("quiz_app_bg_image") || "")
const tempBgDim = ref(Number(localStorage.getItem("quiz_app_bg_dim")) || 45)
const tempBgBlur = ref(Number(localStorage.getItem("quiz_app_bg_blur")) || 0)
const bgTab = ref("upload") // 'upload' | 'url' | 'presets'
const inputBgUrl = ref("")
const bgFileInputRef = ref(null)
const uploadingBgFileName = ref("")
const isProcessingBgImage = ref(false)
const isSavingBg = ref(false)
const bgSuccessMsg = ref("")

const presetWallpapers = ref([
    {
        name: "Giảng đường & Campus",
        url: "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?q=80&w=1920&auto=format&fit=crop"
    },
    {
        name: "Thư viện Đại học Hiện đại",
        url: "https://images.unsplash.com/photo-1521587760476-6c12a4b040da?q=80&w=1920&auto=format&fit=crop"
    },
    {
        name: "Công nghệ Số & Không gian IT",
        url: "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1920&auto=format&fit=crop"
    },
    {
        name: "Bầu trời Đêm Tối giản",
        url: "https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=1920&auto=format&fit=crop"
    }
])

function compressAndReadImage(file, maxWidth = 1920, maxHeight = 1080, quality = 0.85) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = (e) => {
            const img = new Image()
            img.onload = () => {
                let width = img.width
                let height = img.height

                if (width > maxWidth) {
                    height = Math.round((height * maxWidth) / width)
                    width = maxWidth
                }
                if (height > maxHeight) {
                    width = Math.round((width * maxHeight) / height)
                    height = maxHeight
                }

                const canvas = document.createElement("canvas")
                canvas.width = width
                canvas.height = height
                const ctx = canvas.getContext("2d")
                ctx.drawImage(img, 0, 0, width, height)
                const dataUrl = canvas.toDataURL("image/jpeg", quality)
                resolve(dataUrl)
            }
            img.onerror = () => reject(new Error("Lỗi nạp hình ảnh"))
            img.src = e.target.result
        }
        reader.onerror = () => reject(new Error("Lỗi đọc file từ máy tính"))
        reader.readAsDataURL(file)
    })
}

function triggerBgFileInput() {
    if (bgFileInputRef.value) {
        bgFileInputRef.value.click()
    }
}

async function onBgFileSelected(event) {
    const file = event.target.files && event.target.files[0]
    if (!file) return
    await processBgImageFile(file)
}

async function onBgFileDrop(event) {
    event.preventDefault()
    const file = event.dataTransfer?.files?.[0]
    if (!file) return
    await processBgImageFile(file)
}

async function processBgImageFile(file) {
    if (!file.type.startsWith("image/")) {
        alert("Vui lòng chọn một file hình ảnh hợp lệ (PNG, JPG, JPEG, WEBP)!")
        return
    }

    isProcessingBgImage.value = true
    try {
        const compressedBase64 = await compressAndReadImage(file, 1920, 1080, 0.85)
        tempBgImage.value = compressedBase64
        uploadingBgFileName.value = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`
    } catch (err) {
        console.error("Lỗi đọc ảnh:", err)
        alert("Không thể đọc file ảnh này. Vui lòng thử ảnh khác!")
    } finally {
        isProcessingBgImage.value = false
        if (bgFileInputRef.value) bgFileInputRef.value.value = ""
    }
}

function applyBgUrlImage() {
    const url = inputBgUrl.value.trim()
    if (!url) {
        alert("Vui lòng nhập đường link ảnh!")
        return
    }
    tempBgImage.value = url
    uploadingBgFileName.value = "Ảnh từ URL"
}

function selectBgPreset(url, name) {
    tempBgImage.value = url
    uploadingBgFileName.value = name || "Ảnh mẫu có sẵn"
}

function resetBgDefault() {
    tempBgImage.value = ""
    tempBgDim.value = 45
    tempBgBlur.value = 0
    uploadingBgFileName.value = ""
    inputBgUrl.value = ""
}

async function saveBgSettings() {
    isSavingBg.value = true
    currentBgImage.value = tempBgImage.value
    currentBgDim.value = tempBgDim.value
    currentBgBlur.value = tempBgBlur.value

    if (currentBgImage.value) {
        localStorage.setItem("quiz_app_bg_image", currentBgImage.value)
        localStorage.setItem("quiz_app_bg_dim", String(currentBgDim.value))
        localStorage.setItem("quiz_app_bg_blur", String(currentBgBlur.value))
    } else {
        localStorage.removeItem("quiz_app_bg_image")
        localStorage.removeItem("quiz_app_bg_dim")
        localStorage.removeItem("quiz_app_bg_blur")
    }

    try {
        await axios.post(`${API_BASE}/task_service/settings/background`, {
            image: currentBgImage.value,
            dim: currentBgDim.value,
            blur: currentBgBlur.value
        })
    } catch (err) {
        console.log("Lỗi đồng bộ cấu hình lên backend:", err.message)
    } finally {
        isSavingBg.value = false
        bgSuccessMsg.value = "✅ Đã lưu và áp dụng hình nền thành công cho trang đăng nhập sinh viên!"
        setTimeout(() => {
            bgSuccessMsg.value = ""
        }, 5000)
    }
}

async function fetchBgSettings() {
    try {
        const res = await axios.get(`${API_BASE}/task_service/settings/background`)
        if (res.data?.status === 'success' && res.data?.data) {
            const data = res.data.data
            currentBgImage.value = data.image || ""
            currentBgDim.value = data.dim ?? 45
            currentBgBlur.value = data.blur ?? 0
            tempBgImage.value = currentBgImage.value
            tempBgDim.value = currentBgDim.value
            tempBgBlur.value = currentBgBlur.value
            if (currentBgImage.value) {
                localStorage.setItem("quiz_app_bg_image", currentBgImage.value)
                localStorage.setItem("quiz_app_bg_dim", String(currentBgDim.value))
                localStorage.setItem("quiz_app_bg_blur", String(currentBgBlur.value))
            }
        }
    } catch (e) {
        // Giữ nguyên giá trị từ localStorage
    }
}

onMounted(() => {
    fetchBgSettings()
    if (isAuthenticated.value) fetchData()
})

// ================= REPORT SERVICE =================
const reportStats = ref({})
const reportExporting = ref(false)
const reportExportingTestId = ref(null)

const reportByTestColumns = [
    { title: 'Mã đề', key: 'test_code' },
    { title: 'Tên bài thi', key: 'test_name', ellipsis: { tooltip: true } },
    { title: 'Tổng lượt nộp', key: 'submissions' },
    {
        title: 'Số lượt Đạt',
        key: 'pass',
        render: (row) => h(NTag, { type: 'success', size: 'small' }, { default: () => row.pass })
    },
    {
        title: 'Số lượt Chưa đạt',
        key: 'fail',
        render: (row) => h(NTag, { type: 'error', size: 'small' }, { default: () => row.fail })
    },
    {
        title: 'Tỉ lệ Đạt',
        key: 'pass_rate',
        render: (row) => `${row.pass_rate}%`
    },
    {
        title: 'Điểm TB',
        key: 'average_score',
        render: (row) => `${row.average_score}/10`
    },
    {
        title: 'Xuất Excel',
        key: 'export',
        render: (row) => h(NButton, {
            size: 'small',
            type: 'primary',
            ghost: true,
            loading: reportExportingTestId.value === row.test_id,
            onClick: () => exportByTest(row.test_id, row.test_code)
        }, { default: () => '📥 Xuất' })
    }
]

async function fetchReportStats() {
    try {
        const res = await axios.get(`${API_BASE}/task_service/report/stats`)
        if (res.data?.status === 'success') {
            reportStats.value = res.data.data || {}
        }
    } catch (e) {
        console.error('Lỗi lấy thống kê báo cáo:', e)
    }
}

async function exportAllResults() {
    reportExporting.value = true
    try {
        const response = await axios.get(`${API_BASE}/task_service/report/export/all`, {
            responseType: 'blob'
        })
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        const fileName = response.headers['content-disposition']
            ?.split('filename*=UTF-8\'\'')[1]
            || `BangDiem_TongHop_${new Date().toISOString().slice(0,10)}.xlsx`
        link.setAttribute('download', decodeURIComponent(fileName))
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
    } catch (e) {
        console.error('Lỗi xuất báo cáo:', e)
        alert('Lỗi xuất báo cáo! Kiểm tra Report-Service đang chạy trên port 8006.')
    } finally {
        reportExporting.value = false
    }
}

async function exportByTest(testId, testCode) {
    reportExportingTestId.value = testId
    try {
        const response = await axios.get(`${API_BASE}/task_service/report/export/by_test/${testId}`, {
            responseType: 'blob'
        })
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        const fileName = response.headers['content-disposition']
            ?.split('filename*=UTF-8\'\'')[1]
            || `BangDiem_${testCode}_${new Date().toISOString().slice(0,10)}.xlsx`
        link.setAttribute('download', decodeURIComponent(fileName))
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
    } catch (e) {
        console.error('Lỗi xuất báo cáo theo đề:', e)
        alert(`Lỗi xuất bảng điểm đề ${testCode}!`)
    } finally {
        reportExportingTestId.value = null
    }
}
</script>

<template>
    <div class="admin-wrapper">
        <transition name="fade" mode="out-in">
            <div v-if="!isAuthenticated" class="login-container" key="login">
                <div class="glass-card">
                    <h2 class="title">Đăng Nhập Quản Trị Admin</h2>
                    <p class="subtitle">Hệ thống Thi Trắc Nghiệm Microservices (SOA)</p>
                    
                    <n-alert v-if="loginError" type="error" style="margin-bottom: 20px;">
                        {{ loginError }}
                    </n-alert>

                    <div class="input-group">
                        <n-input v-model:value="username" size="large" placeholder="Tài khoản (admin)" @keyup.enter="handleLogin" />
                    </div>
                    <div class="input-group">
                        <n-input v-model:value="password" size="large" type="password" show-password-on="click" placeholder="Mật khẩu (admin)" @keyup.enter="handleLogin" />
                    </div>

                    <n-button @click="handleLogin" class="submit-btn" type="primary" size="large" block>
                        Đăng Nhập
                    </n-button>
                    
                    <div style="text-align: center; margin-top: 18px;">
                        <router-link to="/" style="color: rgba(255,255,255,0.85); text-decoration: none; font-size: 14px;">
                            &larr; Quay lại trang thi của sinh viên
                        </router-link>
                    </div>
                </div>
            </div>

            <div v-else class="admin-layout" key="dashboard">
                <n-layout has-sider style="height: 100vh; max-width: 100vw; overflow: hidden;">
                    <n-layout-sider bordered collapse-mode="width" :collapsed-width="64" :width="240"
                        :native-scrollbar="false" class="sidebar">
                        <div class="logo">
                            <h2>🛡️ Admin Panel</h2>
                        </div>
                        <n-menu :value="activeTab" @update:value="async (val) => { activeTab = val; if (val === 'questions') { await fetchData(); await fetchQuestions(); } else if (val === 'wallpaper') { await fetchBgSettings(); } else if (val === 'report') { await fetchReportStats(); } else { fetchData(); } }" :options="[
                            { label: '📊 Tổng quan Dashboard', key: 'dashboard' },
                            { label: '📝 Quản lý Đề thi', key: 'tests' },
                            { label: '❓ Ngân hàng câu hỏi', key: 'questions' },
                            { label: '🏆 Kết quả thi', key: 'results' },
                            { label: '🎓 Danh sách sinh viên', key: 'students' },
                            { label: '📈 Báo cáo & Xuất Excel', key: 'report' },
                            { label: '🖼️ Cài đặt hình nền', key: 'wallpaper' }
                        ]" />
                        <div style="padding: 20px; position: absolute; bottom: 0;">
                            <router-link to="/">
                                <n-button type="info" ghost size="small">Quay về cổng thi</n-button>
                            </router-link>
                        </div>
                    </n-layout-sider>

                    <n-layout style="height: 100vh; overflow: hidden;">
                        <n-layout-header bordered class="header">
                            <h2>
                                <span v-if="activeTab === 'dashboard'">📊 Tổng quan Thống kê Hệ thống</span>
                                <span v-else-if="activeTab === 'tests'">📝 Quản lý Mã Đề Thi</span>
                                <span v-else-if="activeTab === 'results'">🏆 Quản lý Kết quả thi</span>
                                <span v-else-if="activeTab === 'students'">🎓 Quản lý Sinh viên & Tài khoản</span>
                                <span v-else-if="activeTab === 'wallpaper'">🖼️ Cài Đặt Hình Nền Trang Đăng Nhập</span>
                                <span v-else-if="activeTab === 'report'">📈 Báo cáo & Xuất Bảng Điểm Excel</span>
                                <span v-else>❓ Ngân hàng Câu hỏi</span>
                            </h2>
                            <div>
                                <n-button v-if="activeTab === 'tests'" @click="openCreateTestModal" type="info" style="margin-right: 10px;">+ Thêm Mã Đề</n-button>
                                <n-button v-if="activeTab === 'students'" @click="openCreateStudentModal" type="info" style="margin-right: 10px;">+ Thêm Sinh Viên</n-button>
                                <n-button v-if="activeTab === 'questions'" @click="openCreateModal" type="info" style="margin-right: 10px;">+ Thêm Câu Hỏi</n-button>
                                <n-button v-if="activeTab === 'report'" @click="exportAllResults" type="success" style="margin-right: 10px;" :loading="reportExporting">📥 Xuất tất cả Excel</n-button>
                                <n-button @click="fetchData" :loading="loading" type="primary" style="margin-right: 10px;">Làm mới</n-button>
                                <n-button @click="isAuthenticated = false" type="error" ghost>Đăng xuất</n-button>
                            </div>
                        </n-layout-header>

                        <n-layout-content content-style="padding: 24px; background: #f8fafc; height: calc(100vh - 64px); overflow-y: auto; overflow-x: hidden; box-sizing: border-box;">
                            
                            <!-- TAB DASHBOARD THỐNG KÊ -->
                            <div v-if="activeTab === 'dashboard'" class="dashboard-tab">
                                <n-grid cols="4" item-responsive responsive="screen" x-gap="16" y-gap="16" style="margin-bottom: 24px;">
                                    <n-gi span="4 m:2 l:1">
                                        <n-card class="stat-card border-blue">
                                            <n-statistic label="🎓 Tổng số Sinh viên" :value="totalStudentsCount" />
                                        </n-card>
                                    </n-gi>
                                    <n-gi span="4 m:2 l:1">
                                        <n-card class="stat-card border-indigo">
                                            <n-statistic label="📝 Tổng số Đề thi" :value="totalTestsCount" />
                                        </n-card>
                                    </n-gi>
                                    <n-gi span="4 m:2 l:1">
                                        <n-card class="stat-card border-purple">
                                            <n-statistic label="📑 Tổng lượt nộp bài" :value="totalSubmissionsCount" />
                                        </n-card>
                                    </n-gi>
                                    <n-gi span="4 m:2 l:1">
                                        <n-card class="stat-card border-emerald">
                                            <n-statistic label="⭐ Điểm trung bình" :value="`${averageScore}/10`" />
                                        </n-card>
                                    </n-gi>
                                </n-grid>

                                <n-card title="📊 Phân bố phổ điểm sinh viên" style="margin-top: 24px;" v-if="results.length > 0">
                                    <div style="height: 280px; position: relative;">
                                        <Bar :data="scoreDistributionData" :options="scoreChartOptions" />
                                    </div>
                                </n-card>

                                <n-card title="🏆 Lượt bài nộp mới nhất" style="margin-top: 24px;">
                                    <template #header-extra>
                                        <n-select
                                            v-model:value="selectedTestFilter"
                                            :options="testFilterOptions"
                                            placeholder="Lọc theo bài thi"
                                            clearable
                                            style="width: 260px;"
                                            size="small"
                                        />
                                    </template>
                                    <n-data-table :columns="resultColumns" :data="filteredResults.slice(0, 10)" :bordered="false" />
                                </n-card>
                            </div>

                            <!-- TAB BÁO CÁO & XUẤT EXCEL -->
                            <div v-if="activeTab === 'report'">
                                <!-- Thống kê nhanh -->
                                <n-grid cols="4" item-responsive responsive="screen" x-gap="16" y-gap="16" style="margin-bottom: 24px;">
                                    <n-gi span="4 m:2 l:1">
                                        <n-card class="stat-card border-blue">
                                            <n-statistic label="📑 Tổng lượt nộp" :value="reportStats.total_submissions ?? '—'" />
                                        </n-card>
                                    </n-gi>
                                    <n-gi span="4 m:2 l:1">
                                        <n-card class="stat-card border-emerald">
                                            <n-statistic label="✅ Số lượt Đạt" :value="reportStats.pass_count ?? '—'" />
                                        </n-card>
                                    </n-gi>
                                    <n-gi span="4 m:2 l:1">
                                        <n-card class="stat-card border-red">
                                            <n-statistic label="❌ Số lượt Chưa đạt" :value="reportStats.fail_count ?? '—'" />
                                        </n-card>
                                    </n-gi>
                                    <n-gi span="4 m:2 l:1">
                                        <n-card class="stat-card border-purple">
                                            <n-statistic label="⭐ Điểm TB" :value="reportStats.average_score !== undefined ? `${reportStats.average_score}/10` : '—'" />
                                        </n-card>
                                    </n-gi>
                                </n-grid>

                                <!-- Xuất báo cáo tổng hợp -->
                                <n-card title="📥 Xuất Báo Cáo Excel" style="margin-bottom: 24px;">
                                    <div style="display: flex; flex-wrap: wrap; gap: 16px; align-items: center; padding: 8px 0;">
                                        <div style="flex: 1; min-width: 280px;">
                                            <div style="font-size: 15px; font-weight: 600; margin-bottom: 4px;">📊 Bảng điểm tổng hợp tất cả bài thi</div>
                                            <div style="font-size: 13px; color: #64748b;">Xuất toàn bộ kết quả thi của tất cả sinh viên, kèm thống kê pass/fail, điểm TB...</div>
                                        </div>
                                        <n-button type="success" :loading="reportExporting" @click="exportAllResults" size="large">
                                            📥 Xuất Excel Tổng hợp
                                        </n-button>
                                    </div>
                                </n-card>

                                <!-- Xuất theo từng bài thi -->
                                <n-card title="📝 Xuất Bảng Điểm Theo Đề Thi" style="margin-bottom: 24px;">
                                    <div v-if="tests.length === 0" style="color:#94a3b8; padding: 20px; text-align: center;">Chưa có đề thi nào.</div>
                                    <div v-else style="display: flex; flex-direction: column; gap: 12px;">
                                        <div v-for="t in tests" :key="t._id" class="report-row">
                                            <div style="flex: 1;">
                                                <n-tag type="info" size="small" style="margin-right: 8px;">{{ t.test_code }}</n-tag>
                                                <span style="font-weight: 500;">{{ t.name }}</span>
                                                <span style="color: #64748b; font-size: 13px; margin-left: 8px;">({{ t.question_count || 0 }} câu hỏi)</span>
                                            </div>
                                            <n-button size="small" type="primary" ghost :loading="reportExportingTestId === t._id" @click="exportByTest(t._id, t.test_code)">
                                                📥 Xuất Excel
                                            </n-button>
                                        </div>
                                    </div>
                                </n-card>

                                <!-- Thống kê từng đề -->
                                <n-card title="📈 Thống kê Chi tiết theo Đề Thi" v-if="reportStats.by_test && reportStats.by_test.length > 0">
                                    <n-data-table
                                        :columns="reportByTestColumns"
                                        :data="reportStats.by_test"
                                        :bordered="false"
                                    />
                                </n-card>
                            </div>

                            <!-- TAB MANAGE TESTS -->
                            <n-card v-if="activeTab === 'tests'">
                                <div style="margin-bottom: 16px; width: 300px;">
                                    <n-input v-model:value="testSearchQuery" placeholder="🔍 Tìm kiếm mã đề hoặc tên..." clearable />
                                </div>
                                <n-data-table :columns="testColumns" :data="filteredTests" :loading="loading" :bordered="false" />
                            </n-card>

                            <!-- TAB MANAGE RESULTS -->
                            <n-card v-if="activeTab === 'results'">
                                <div style="margin-bottom: 16px; display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
                                    <n-input v-model:value="resultSearchQuery" placeholder="🔍 Tìm kiếm MSV, Họ tên SV hoặc Tên bài thi..." clearable style="width: 340px;" />
                                    <n-select
                                        v-model:value="selectedTestFilter"
                                        :options="testFilterOptions"
                                        placeholder="Lọc theo bài thi"
                                        clearable
                                        style="width: 280px;"
                                    />
                                    <span style="color: #64748b; font-size: 13px; margin-left: auto;">Tổng: {{ filteredResults.length }} lượt nộp</span>
                                </div>
                                <n-data-table :columns="resultColumns" :data="filteredResults" :loading="loading" :bordered="false" />
                            </n-card>

                            <!-- TAB MANAGE STUDENTS -->
                            <n-card v-if="activeTab === 'students'">
                                <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
                                    <div style="width: 320px;">
                                        <n-input v-model:value="studentSearchQuery" placeholder="🔍 Tìm kiếm MSV, Tên, Lớp, Khoa..." clearable />
                                    </div>
                                    <div style="display: flex; gap: 10px;">
                                        <input type="file" ref="studentExcelInputRef" accept=".xlsx, .xls, .csv" style="display: none;" @change="handleStudentExcelUpload" />
                                        <n-button type="primary" ghost @click="triggerStudentExcelUpload">📁 Import Excel Sinh Viên</n-button>
                                        <n-button type="info" @click="openCreateStudentModal">+ Thêm Sinh Viên Mới</n-button>
                                    </div>
                                </div>
                                <n-data-table :columns="studentColumns" :data="filteredStudents" :loading="loading" :bordered="false" />
                            </n-card>

                            <!-- TAB MANAGE QUESTIONS -->
                            <n-card v-if="activeTab === 'questions'">
                                <div style="margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 15px;">
                                    <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                                        <strong>Chọn Mã Đề Thi:</strong>
                                        <select v-model="selectedTestId" @change="fetchQuestions" style="padding: 8px 14px; border-radius: 8px; border: 1px solid #cbd5e1; min-width: 320px; font-size: 14px; font-weight: 500;">
                                            <option value="" disabled>-- Chọn mã đề --</option>
                                            <option v-for="t in tests" :key="t._id" :value="t._id">
                                                [{{ t.test_code }}] {{ t.name }} ({{ t.question_count || 0 }} câu)
                                            </option>
                                        </select>
                                        <n-button size="small" type="primary" ghost @click="fetchQuestions" :loading="loading">🔄 Tải câu hỏi</n-button>
                                    </div>
                                    <div>
                                        <n-button type="info" :disabled="!selectedTestId" @click="openCreateModal">+ Thêm Câu Hỏi Mới</n-button>
                                    </div>
                                </div>

                                <div v-if="currentSelectedTest" style="background: #eef2ff; border: 1px solid #c7d2fe; border-radius: 8px; padding: 10px 16px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <span style="font-size: 14px; color: #3730a3;">
                                            📌 Đang quản lý câu hỏi của Mã đề: <strong>{{ currentSelectedTest.test_code }} - {{ currentSelectedTest.name }}</strong>
                                        </span>
                                    </div>
                                    <n-tag type="info" size="small">{{ questions.length }} câu hỏi</n-tag>
                                </div>

                                <div v-if="tests.length === 0" style="text-align:center; color:#94a3b8; padding: 40px;">
                                    ⚠️ Chưa có mã đề nào. Hãy tạo mã đề trước trong tab "Quản lý Đề thi".
                                </div>
                                <div v-else-if="!selectedTestId" style="text-align:center; color:#94a3b8; padding: 40px;">
                                    👉 Vui lòng chọn một mã đề từ danh sách bên trên để quản lý câu hỏi.
                                </div>
                                <div v-else-if="questions.length === 0 && !loading" style="text-align:center; color:#64748b; padding: 40px; background: #f8fafc; border-radius: 12px; border: 1px dashed #cbd5e1;">
                                    <p style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">Mã đề này chưa có câu hỏi nào!</p>
                                    <p style="font-size: 14px; color: #94a3b8; margin-bottom: 16px;">Hãy bấm nút bên dưới để thêm câu hỏi đầu tiên.</p>
                                    <n-button type="info" @click="openCreateModal">+ Thêm Câu Hỏi Ngay</n-button>
                                </div>
                                <n-data-table v-else :columns="questionColumns" :data="questions" :loading="loading" :bordered="false" />
                            </n-card>

                            <!-- TAB CÀI ĐẶT HÌNH NỀN ĐĂNG NHẬP -->
                            <div v-if="activeTab === 'wallpaper'" class="wallpaper-panel">
                                <!-- Hidden input để chọn file ảnh từ máy tính -->
                                <input 
                                    type="file" 
                                    ref="bgFileInputRef" 
                                    accept="image/png, image/jpeg, image/jpg, image/webp, image/gif" 
                                    style="display: none" 
                                    @change="onBgFileSelected" 
                                />

                                <n-alert v-if="bgSuccessMsg" type="success" closable @close="bgSuccessMsg = ''" style="margin-bottom: 20px;">
                                    {{ bgSuccessMsg }}
                                </n-alert>

                                <n-grid cols="12" item-responsive responsive="screen" x-gap="20" y-gap="20">
                                    <!-- Cột trái: Các công cụ nạp và tùy chỉnh ảnh -->
                                    <n-gi span="12 l:7">
                                        <n-card title="⚙️ Tùy Chỉnh Hình Nền Màn Hình Đăng Nhập" style="border-radius: 12px;">
                                            <p style="color: #64748b; font-size: 14px; margin-bottom: 16px;">
                                                Hình nền được cài đặt tại đây sẽ áp dụng cho toàn bộ sinh viên khi truy cập trang đăng nhập làm bài thi.
                                            </p>

                                            <!-- Trạng thái hiện tại -->
                                            <div style="background: #f1f5f9; border-radius: 8px; padding: 12px 16px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
                                                <div>
                                                    <span style="font-size: 13px; color: #475569;">Trạng thái nền đăng nhập hiện tại:</span>
                                                    <div style="font-weight: 600; margin-top: 2px;">
                                                        <span v-if="currentBgImage" style="color: #16a34a;">
                                                            🟢 Đang kích hoạt hình nền tùy chỉnh
                                                        </span>
                                                        <span v-else style="color: #6366f1;">
                                                            🟣 Đang dùng màu chuyển động gradient mặc định
                                                        </span>
                                                    </div>
                                                </div>
                                                <a href="/" target="_blank" style="text-decoration: none;">
                                                    <n-button size="small" type="info" ghost>
                                                        🔗 Xem trang sinh viên
                                                    </n-button>
                                                </a>
                                            </div>

                                            <n-tabs v-model:value="bgTab" type="line" animated>
                                                <!-- Tab 1: Tải ảnh từ máy tính -->
                                                <n-tab-pane name="upload" tab="📁 Tải ảnh từ máy tính">
                                                    <div 
                                                        class="admin-upload-dropzone" 
                                                        @click="triggerBgFileInput"
                                                        @dragover.prevent
                                                        @drop="onBgFileDrop"
                                                    >
                                                        <div v-if="isProcessingBgImage" style="padding: 24px; text-align: center;">
                                                            <n-spin size="large" stroke="#6366f1" />
                                                            <p style="margin-top: 12px; color: #64748b; font-weight: 500;">Đang xử lý và tối ưu hóa kích thước ảnh...</p>
                                                        </div>
                                                        <div v-else class="dropzone-body">
                                                            <div class="dropzone-icon-box">
                                                                <span style="font-size: 32px;">📷</span>
                                                            </div>
                                                            <h4 style="margin: 8px 0 4px 0; font-size: 16px; color: #1e293b;">
                                                                Nhấp vào đây để chọn ảnh từ máy tính của bạn
                                                            </h4>
                                                            <p style="color: #64748b; font-size: 13px; margin: 0 0 12px 0;">
                                                                Hoặc kéo và thả file ảnh vào khung này
                                                            </p>
                                                            <n-button type="primary" size="medium" style="border-radius: 8px;">
                                                                Chọn file ảnh
                                                            </n-button>
                                                            <p style="font-size: 12px; color: #94a3b8; margin-top: 12px;">
                                                                Hỗ trợ PNG, JPG, JPEG, WEBP. Ảnh sẽ được tự động tối ưu hóa chuẩn Full HD hiển thị mượt mà.
                                                            </p>
                                                            <div v-if="uploadingBgFileName" class="admin-badge-success">
                                                                ✅ Đã nạp file: <strong>{{ uploadingBgFileName }}</strong>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </n-tab-pane>

                                                <!-- Tab 2: Nhập liên kết ảnh URL -->
                                                <n-tab-pane name="url" tab="🔗 Dán link ảnh (URL)">
                                                    <div style="padding: 16px 0;">
                                                        <label style="font-size: 14px; font-weight: 600; color: #334155; display: block; margin-bottom: 8px;">
                                                            Đường dẫn hình ảnh trực tuyến:
                                                        </label>
                                                        <div style="display: flex; gap: 10px;">
                                                            <n-input 
                                                                v-model:value="inputBgUrl" 
                                                                placeholder="https://example.com/anh-truong-dai-hoc.jpg" 
                                                                size="large"
                                                                @keydown.enter="applyBgUrlImage"
                                                            />
                                                            <n-button type="primary" size="large" @click="applyBgUrlImage">
                                                                Nạp ảnh
                                                            </n-button>
                                                        </div>
                                                        <span style="display: block; font-size: 12px; color: #94a3b8; margin-top: 6px;">
                                                            Nhập liên kết trực tiếp tới file ảnh (.jpg, .png, .webp).
                                                        </span>
                                                    </div>
                                                </n-tab-pane>

                                                <!-- Tab 3: Bộ sưu tập mẫu có sẵn -->
                                                <n-tab-pane name="presets" tab="✨ Bộ sưu tập mẫu">
                                                    <div class="admin-presets-grid">
                                                        <div 
                                                            v-for="(preset, idx) in presetWallpapers" 
                                                            :key="idx" 
                                                            class="admin-preset-item"
                                                            :class="{ active: tempBgImage === preset.url }"
                                                            @click="selectBgPreset(preset.url, preset.name)"
                                                        >
                                                            <img :src="preset.url" :alt="preset.name" loading="lazy" />
                                                            <div class="admin-preset-name">{{ preset.name }}</div>
                                                        </div>
                                                    </div>
                                                </n-tab-pane>
                                            </n-tabs>

                                            <!-- Thanh trượt điều chỉnh độ sáng tối và độ mờ -->
                                            <div v-if="tempBgImage" style="margin-top: 20px; background: #f8fafc; border-radius: 10px; padding: 16px; border: 1px solid #e2e8f0;">
                                                <div style="margin-bottom: 16px;">
                                                    <div style="display: flex; justify-content: space-between; font-size: 14px; font-weight: 600; color: #1e293b; margin-bottom: 4px;">
                                                        <span>🌑 Độ tối lớp phủ (Overlay Dim):</span>
                                                        <span style="color: #6366f1;">{{ tempBgDim }}%</span>
                                                    </div>
                                                    <n-slider v-model:value="tempBgDim" :min="0" :max="90" :step="5" />
                                                    <span style="font-size: 12px; color: #64748b;">
                                                        Tăng độ tối nếu ảnh nền có nhiều chi tiết sáng giúp khung đăng nhập và chữ luôn rõ nét.
                                                    </span>
                                                </div>

                                                <div>
                                                    <div style="display: flex; justify-content: space-between; font-size: 14px; font-weight: 600; color: #1e293b; margin-bottom: 4px;">
                                                        <span>🌫️ Độ mờ hậu cảnh (Blur Effect):</span>
                                                        <span style="color: #6366f1;">{{ tempBgBlur }}px</span>
                                                    </div>
                                                    <n-slider v-model:value="tempBgBlur" :min="0" :max="20" :step="1" />
                                                    <span style="font-size: 12px; color: #64748b;">
                                                        Làm mờ hậu cảnh tạo hiệu ứng kính mờ (Glassmorphism) chuyên nghiệp.
                                                    </span>
                                                </div>
                                            </div>

                                            <!-- Các nút hành động lưu / khôi phục -->
                                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e2e8f0;">
                                                <n-button secondary type="warning" @click="resetBgDefault">
                                                    🔄 Đặt lại mặc định (Gradient)
                                                </n-button>
                                                <div style="display: flex; gap: 12px;">
                                                    <n-button type="primary" size="large" :loading="isSavingBg" @click="saveBgSettings">
                                                        💾 Áp Dụng & Lưu Cấu Hình
                                                    </n-button>
                                                </div>
                                            </div>
                                        </n-card>
                                    </n-gi>

                                    <!-- Cột phải: Live Preview màn hình đăng nhập -->
                                    <n-gi span="12 l:5">
                                        <n-card title="👁️ Xem Trước Màn Hình Đăng Nhập Sinh Viên" style="border-radius: 12px;">
                                            <p style="color: #64748b; font-size: 13px; margin-bottom: 12px;">
                                                Mô phỏng trực tiếp giao diện sinh viên sẽ nhìn thấy:
                                            </p>

                                            <div class="admin-preview-monitor">
                                                <!-- Ảnh nền mô phỏng -->
                                                <div 
                                                    v-if="tempBgImage" 
                                                    class="monitor-bg" 
                                                    :style="{
                                                        backgroundImage: `url(${tempBgImage})`,
                                                        filter: `blur(${tempBgBlur}px)`
                                                    }"
                                                ></div>
                                                <div 
                                                    v-else 
                                                    class="monitor-bg-gradient"
                                                ></div>

                                                <!-- Lớp phủ tối -->
                                                <div 
                                                    v-if="tempBgImage" 
                                                    class="monitor-overlay"
                                                    :style="{ backgroundColor: `rgba(15, 23, 42, ${tempBgDim / 100})` }"
                                                ></div>

                                                <!-- Thẻ đăng nhập mô phỏng -->
                                                <div class="monitor-login-card">
                                                    <div class="monitor-card-title">Đăng Nhập Thi Trắc Nghiệm</div>
                                                    <div class="monitor-card-sub">HUNRE Microservices (SOA)</div>
                                                    <div class="monitor-input-mock">Mã đề thi (VD: SOA_01)</div>
                                                    <div class="monitor-input-mock">Email sinh viên</div>
                                                    <div class="monitor-input-mock">Mật khẩu (MSV)</div>
                                                    <div class="monitor-btn-mock">Bắt đầu làm bài</div>
                                                </div>
                                            </div>

                                            <div style="margin-top: 16px; font-size: 13px; color: #64748b; text-align: center;">
                                                💡 Khi ấn <strong>"Áp Dụng & Lưu Cấu Hình"</strong>, hình nền sẽ được đồng bộ ngay tức thì đến máy chủ và trang đăng nhập.
                                            </div>
                                        </n-card>
                                    </n-gi>
                                </n-grid>
                            </div>
                        </n-layout-content>
                    </n-layout>
                </n-layout>

                <!-- Modal Thêm/Sửa Sinh Viên -->
                <n-modal v-model:show="showStudentModal" preset="card" style="width: 520px; border-radius: 16px;" :title="isEditingStudent ? 'Sửa Thông Tin Sinh Viên' : 'Thêm Sinh Viên Mới'">
                    <n-space vertical size="large">
                        <div>
                            <label style="font-weight: bold;">Mã Sinh Viên (MSV - 10 chữ số):</label>
                            <n-input v-model:value="studentForm.student_code" placeholder="Ví dụ: 2311060738" />
                        </div>
                        <div>
                            <label style="font-weight: bold;">Họ và Tên:</label>
                            <n-input v-model:value="studentForm.student_name" placeholder="Ví dụ: An Công Chuẩn" />
                        </div>
                        <div>
                            <label style="font-weight: bold;">Lớp:</label>
                            <n-input v-model:value="studentForm.class_name" placeholder="Ví dụ: ĐH CNTT K23A" />
                        </div>
                        <div>
                            <label style="font-weight: bold;">Khoa:</label>
                            <n-input v-model:value="studentForm.faculty" placeholder="Ví dụ: Công nghệ Thông tin" />
                        </div>
                        <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px;">
                            <n-button @click="showStudentModal = false">Hủy</n-button>
                            <n-button type="primary" @click="saveStudent" :loading="loading">Lưu</n-button>
                        </div>
                    </n-space>
                </n-modal>

                <!-- Modal Thêm/Sửa Mã Đề -->
                <n-modal v-model:show="showTestModal" preset="card" style="width: 580px; border-radius: 16px;" :title="isEditingTest ? 'Sửa Mã Đề' : 'Thêm Mã Đề Mới'">
                    <n-space vertical size="large">
                        <div>
                            <label style="font-weight: bold;">Mã đề (VD: SOA_01):</label>
                            <n-input v-model:value="testForm.test_code" placeholder="Mã đề viết liền không dấu" />
                        </div>
                        <div>
                            <label style="font-weight: bold;">Tên bài thi:</label>
                            <n-input v-model:value="testForm.name" placeholder="Tên bài kiểm tra" />
                        </div>
                        <div>
                            <label style="font-weight: bold;">Thời gian (phút):</label>
                            <n-input v-model:value="testForm.time" type="text" placeholder="Ví dụ: 45" />
                        </div>
                        <div>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <label style="font-weight: bold;">Danh sách MSV được phép thi:</label>
                                <div style="display: flex; gap: 8px;">
                                    <n-button size="tiny" type="info" ghost @click="downloadExcelTemplate">
                                        📥 File mẫu Excel
                                    </n-button>
                                    <n-button size="tiny" type="primary" @click="triggerExcelUpload">
                                        📁 Upload Excel
                                    </n-button>
                                </div>
                            </div>
                            
                            <input type="file" ref="excelFileInputRef" accept=".xlsx, .xls, .csv" style="display: none;" @change="handleExcelUpload" />

                            <n-input v-model:value="testForm.list_students" type="textarea" :rows="4" placeholder="Ví dụ: 2311060738, 2311060001 (Cách nhau dấu phẩy, để trống nếu cho phép tất cả SV)" />
                            
                            <div v-if="excelStatusMessage" style="font-size: 13px; color: #10b981; margin-top: 6px; font-weight: 600; display: flex; align-items: center; gap: 4px;">
                                ✨ {{ excelStatusMessage }}
                            </div>
                        </div>
                        <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px;">
                            <n-button @click="showTestModal = false">Hủy</n-button>
                            <n-button type="primary" @click="saveTest" :loading="loading">Lưu</n-button>
                        </div>
                    </n-space>
                </n-modal>

                <!-- Modal Chọn Phương Thức Nhập MSV Excel -->
                <n-modal v-model:show="showExcelModeModal" preset="card" style="width: 480px; border-radius: 16px;" title="💡 Lựa chọn phương thức nhập dữ liệu Excel">
                    <div style="font-size: 14px; line-height: 1.6; color: #334155; margin-bottom: 20px;">
                        Phát hiện <strong>{{ pendingExtractedMSVs.length }} MSV</strong> từ file Excel <code>{{ excelFileName }}</code>.<br/>
                        Danh sách MSV hiện tại đang có dữ liệu. Bạn muốn xử lý như thế nào?
                    </div>
                    <div style="display: flex; justify-content: flex-end; gap: 10px;">
                        <n-button @click="showExcelModeModal = false">Hủy bỏ</n-button>
                        <n-button type="warning" @click="applyExcelMSVs('append')">➕ Thêm nối tiếp (Append)</n-button>
                        <n-button type="primary" @click="applyExcelMSVs('replace')">🔄 Ghi đè (Replace)</n-button>
                    </div>
                </n-modal>

                <!-- Modal Thêm/Sửa Câu Hỏi -->
                <n-modal v-model:show="showQuestionModal" preset="card" style="width: 650px; border-radius: 16px;" :title="isEditing ? 'Sửa Câu Hỏi' : 'Thêm Câu Hỏi Mới'">
                    <div v-if="currentSelectedTest" style="margin-bottom: 14px; padding: 8px 12px; background: #eff6ff; border-radius: 8px; border: 1px solid #bfdbfe; font-size: 13.5px; color: #1e40af;">
                        Mã đề: <strong>{{ currentSelectedTest.test_code }}</strong> ({{ currentSelectedTest.name }})
                    </div>
                    <n-space vertical size="large">
                        <div>
                            <label style="font-weight: bold;">Nội dung câu hỏi: <span style="color: #ef4444;">*</span></label>
                            <n-input v-model:value="questionForm.text" type="textarea" :rows="3" placeholder="Nhập nội dung câu hỏi..." />
                        </div>
                        <div>
                            <label style="font-weight: bold; display: flex; justify-content: space-between;">
                                <span>Các đáp án lựa chọn (Tích chọn 1 đáp án đúng): <span style="color: #ef4444;">*</span></span>
                            </label>
                            <div v-for="(ans, index) in questionForm.answers" :key="index" style="display: flex; align-items: center; gap: 10px; margin-top: 10px;">
                                <input 
                                    type="radio" 
                                    name="correct_answer_radio" 
                                    :checked="ans.is_correct" 
                                    @change="setCorrectAnswer(index)" 
                                    style="width: 20px; height: 20px; cursor: pointer; accent-color: #10b981;" 
                                    title="Chọn làm đáp án đúng"
                                />
                                <span style="font-weight: bold; width: 22px;">{{ String.fromCharCode(65 + index) }}.</span>
                                <n-input v-model:value="ans.text" :placeholder="`Nhập nội dung đáp án ${String.fromCharCode(65 + index)}...`" style="flex: 1;" />
                                <n-tag v-if="ans.is_correct" type="success" size="small" style="font-weight: bold;">Đúng</n-tag>
                            </div>
                        </div>
                        <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px;">
                            <n-button @click="showQuestionModal = false">Hủy</n-button>
                            <n-button type="primary" @click="saveQuestion" :loading="loading">Lưu Câu Hỏi</n-button>
                        </div>
                    </n-space>
                </n-modal>

                <!-- Modal xem lịch sử thi sinh viên -->
                <n-modal v-model:show="showStudentHistoryModal" preset="card" style="width: 600px; border-radius: 16px;" :title="`📜 Lịch sử thi của MSV: ${selectedStudentCode}`">
                    <div v-if="studentHistoryData.length === 0" style="padding: 20px; text-align: center; color: #64748b;">
                        Sinh viên này chưa có lượt nộp bài thi nào.
                    </div>
                    <div v-else style="display: flex; flex-direction: column; gap: 12px;">
                        <div v-for="(h, idx) in studentHistoryData" :key="idx" style="padding: 12px 16px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;">
                            <div style="display: flex; justify-content: space-between; font-weight: bold;">
                                <span>Bài thi ID: {{ h.test_id }}</span>
                                <n-tag :type="h.score >= 5 ? 'success' : 'error'">Điểm: {{ h.score }}/10</n-tag>
                            </div>
                            <div style="font-size: 13px; color: #64748b; margin-top: 4px;">
                                <span>Đúng: {{ h.correct_count }}/{{ h.total_questions }} câu</span> • <span>Nộp lúc: {{ new Date(h.submitted_at).toLocaleString() }}</span>
                            </div>
                        </div>
                    </div>
                </n-modal>

                <!-- Modal xem chi tiết bài nộp -->
                <n-modal v-model:show="showSubmissionDetailModal" preset="card" style="width: 520px; border-radius: 16px;" title="📋 Chi tiết Bài nộp">
                    <div v-if="selectedSubmission" style="display: flex; flex-direction: column; gap: 16px;">
                        <div style="display: flex; align-items: center; gap: 14px; padding: 16px; background: linear-gradient(135deg, #eef2ff 0%, #f0f9ff 100%); border-radius: 12px; border: 1px solid #c7d2fe;">
                            <div style="width: 48px; height: 48px; border-radius: 50%; background: linear-gradient(135deg, #6366f1, #a855f7); display: flex; align-items: center; justify-content: center; color: white; font-size: 20px; font-weight: 800; flex-shrink: 0;">
                                {{ (selectedSubmission.student_name || 'N')[0] }}
                            </div>
                            <div>
                                <div style="font-size: 17px; font-weight: 700; color: #1e293b;">{{ selectedSubmission.student_name || 'N/A' }}</div>
                                <div style="font-size: 13px; color: #64748b; margin-top: 2px;">MSV: {{ selectedSubmission.student_code }}</div>
                            </div>
                        </div>

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                            <div class="detail-info-card">
                                <div class="detail-label">📝 Bài thi</div>
                                <div class="detail-value">{{ selectedSubmission.test_title || selectedSubmission.test_id }}</div>
                            </div>
                            <div class="detail-info-card">
                                <div class="detail-label">⭐ Điểm số</div>
                                <div class="detail-value">
                                    <n-tag :type="selectedSubmission.score >= 5 ? 'success' : 'error'" round style="font-weight: 700; font-size: 15px;">
                                        {{ selectedSubmission.score }}/10
                                    </n-tag>
                                </div>
                            </div>
                            <div class="detail-info-card">
                                <div class="detail-label">✅ Số câu đúng</div>
                                <div class="detail-value" style="font-weight: 700; font-size: 16px; color: #0f172a;">
                                    {{ selectedSubmission.correct_answers }}/{{ selectedSubmission.total_questions }}
                                </div>
                            </div>
                            <div class="detail-info-card">
                                <div class="detail-label">🕐 Thời gian nộp</div>
                                <div class="detail-value">{{ selectedSubmission.submitted_at }}</div>
                            </div>
                        </div>

                        <div style="text-align: center; padding: 12px 0 4px 0;">
                            <n-tag :type="selectedSubmission.score >= 5 ? 'success' : 'error'" size="large" round style="font-size: 15px; font-weight: 700; padding: 6px 24px;">
                                {{ selectedSubmission.score >= 5 ? '✓ ĐẠT' : '✗ CHƯA ĐẠT' }}
                            </n-tag>
                        </div>
                    </div>
                </n-modal>
            </div>
        </transition>
    </div>
</template>

<style scoped>
*, *::before, *::after {
    box-sizing: border-box;
}

.admin-wrapper {
    height: 100vh;
    width: 100%;
    max-width: 100vw;
    overflow: hidden;
}

.login-container {
    height: 100vh;
    width: 100vw;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(-45deg, #0f172a, #1e1b4b, #312e81, #1e293b);
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
}

@keyframes gradientBG {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
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
    max-width: 420px;
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

.admin-layout {
    height: 100vh;
    width: 100%;
    max-width: 100vw;
    overflow: hidden;
}

.sidebar {
    background: #ffffff;
}

.logo {
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid #f1f5f9;
    color: #0f172a;
}

.logo h2 {
    margin: 0;
    font-size: 19px;
    font-weight: 800;
    background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.header {
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;
    background: #fff;
    width: 100%;
    box-sizing: border-box;
}

.header h2 {
    margin: 0;
    font-size: 19px;
    font-weight: 700;
    color: #0f172a;
}

:deep(.n-card) {
    border-radius: 14px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
    max-width: 100%;
    box-sizing: border-box;
}

.stat-card {
    border-left: 5px solid #cbd5e1;
    border-radius: 12px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.03);
}

.stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.06);
}

:deep(.stat-card .n-card__content) {
    padding: 16px 18px !important;
}

:deep(.stat-card .n-statistic .n-statistic-main__label) {
    font-size: 13.5px !important;
    font-weight: 600 !important;
    color: #475569 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}

:deep(.stat-card .n-statistic .n-statistic-value__content) {
    font-size: 26px !important;
    font-weight: 800 !important;
    color: #0f172a !important;
    margin-top: 6px !important;
}

.border-blue { border-left-color: #3b82f6; }
.border-indigo { border-left-color: #6366f1; }
.border-purple { border-left-color: #a855f7; }
.border-emerald { border-left-color: #10b981; }


.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.4s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}

/* Wallpaper Panel Styles */
.admin-upload-dropzone {
    border: 2px dashed #818cf8;
    background: #f8fafc;
    border-radius: 12px;
    padding: 32px 20px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
    margin: 10px 0;
}

.admin-upload-dropzone:hover {
    border-color: #4f46e5;
    background: #eef2ff;
    transform: translateY(-2px);
}

.dropzone-icon-box {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: #e0e7ff;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 8px;
}

.admin-badge-success {
    margin-top: 14px;
    display: inline-block;
    background: #dcfce7;
    color: #15803d;
    border: 1px solid #86efac;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 13px;
}

.admin-presets-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin: 12px 0;
}

.admin-preset-item {
    position: relative;
    height: 110px;
    border-radius: 10px;
    overflow: hidden;
    cursor: pointer;
    border: 2px solid transparent;
    transition: all 0.25s ease;
}

.admin-preset-item img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s ease;
}

.admin-preset-item:hover img {
    transform: scale(1.08);
}

.admin-preset-item.active {
    border-color: #6366f1;
    box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);
}

.admin-preset-name {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(to top, rgba(0,0,0,0.85), transparent);
    color: #fff;
    font-size: 12px;
    font-weight: 600;
    padding: 8px 10px;
}

/* Monitor Preview */
.admin-preview-monitor {
    position: relative;
    height: 380px;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #cbd5e1;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}

.monitor-bg {
    position: absolute;
    inset: -6px;
    background-size: cover;
    background-position: center;
    z-index: 1;
}

.monitor-bg-gradient {
    position: absolute;
    inset: 0;
    background: linear-gradient(-45deg, #1e1b4b, #312e81, #0f172a, #1e293b);
    background-size: 400% 400%;
    z-index: 1;
}

.monitor-overlay {
    position: absolute;
    inset: 0;
    z-index: 2;
}

.monitor-login-card {
    position: relative;
    z-index: 3;
    background: rgba(255, 255, 255, 0.14);
    backdrop-filter: blur(12px);
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.25);
    padding: 20px 24px;
    width: 250px;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.37);
}

.monitor-card-title {
    color: #fff;
    font-size: 13px;
    font-weight: 800;
}

.monitor-card-sub {
    color: rgba(255, 255, 255, 0.85);
    font-size: 10px;
    margin-bottom: 12px;
}

.monitor-input-mock {
    background: rgba(255, 255, 255, 0.92);
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 9px;
    color: #94a3b8;
    margin-bottom: 8px;
    text-align: left;
}

.monitor-btn-mock {
    background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
    color: #fff;
    font-size: 11px;
    font-weight: bold;
    padding: 7px 0;
    border-radius: 6px;
    margin-top: 6px;
}

/* Report tab */
.border-red {
    border-left: 4px solid #ef4444 !important;
}

.report-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    transition: box-shadow 0.2s;
}

.report-row:hover {
    box-shadow: 0 2px 10px rgba(99, 102, 241, 0.12);
    border-color: #a5b4fc;
}

/* Submission Detail Modal */
.detail-info-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 16px;
    transition: box-shadow 0.2s ease;
}

.detail-info-card:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.detail-label {
    font-size: 12px;
    color: #64748b;
    font-weight: 600;
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

.detail-value {
    font-size: 14px;
    color: #1e293b;
    font-weight: 500;
    word-break: break-word;
}
</style>
