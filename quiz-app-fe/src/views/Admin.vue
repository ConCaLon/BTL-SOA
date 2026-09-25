<script setup>
import { ref, onMounted, computed, h } from 'vue'
import { NButton, NPopconfirm, NSpace, NTag, NCard, NGrid, NGi, NStatistic, NInput } from 'naive-ui'
import axios from 'axios'
import * as XLSX from 'xlsx'

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

// Search filters
const testSearchQuery = ref('')
const resultSearchQuery = ref('')
const studentSearchQuery = ref('')

// Student History Modal
const showStudentHistoryModal = ref(false)
const selectedStudentCode = ref('')
const studentHistoryData = ref([])

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
    if (!resultSearchQuery.value) return results.value
    const q = resultSearchQuery.value.toLowerCase()
    return results.value.filter(r => 
        (r.student_code && r.student_code.toLowerCase().includes(q)) ||
        (r.test_id && r.test_id.toLowerCase().includes(q))
    )
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
                h(NButton, { size: 'small', type: 'info', onClick: () => openEditTestModal(row) }, { default: () => 'Sửa' }),
                h(NPopconfirm, {
                    onPositiveClick: () => deleteTest(row._id),
                    positiveText: 'Xóa',
                    negativeText: 'Hủy'
                }, {
                    trigger: () => h(NButton, { size: 'small', type: 'error' }, { default: () => 'Xóa' }),
                    default: () => 'Xóa mã đề sẽ mồ côi các câu hỏi thuộc mã đề này. Xác nhận xóa?'
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
    { title: 'Mã SV', key: 'student_code' },
    { title: 'Bài Thi (ID)', key: 'test_id' },
    { 
        title: 'Điểm số', 
        key: 'score', 
        render: (row) => {
            const isPass = row.score >= 5
            return h(NTag, { type: isPass ? 'success' : 'error' }, { default: () => `${row.score}/10` })
        }
    },
    { title: 'Số câu đúng', key: 'correct_count', render: (row) => `${row.correct_count}/${row.total_questions}` },
    { title: 'Thời gian nộp', key: 'submitted_at', render: (row) => new Date(row.submitted_at).toLocaleString() }
]

const questionColumns = [
    { title: 'Câu hỏi', key: 'text' },
    { title: 'Đáp án đúng', key: 'correct', render: (row) => {
        const correctAns = row.answers ? row.answers.find(a => a.is_correct) : null
        return correctAns ? h(NTag, { type: 'success' }, { default: () => correctAns.text }) : 'N/A'
    }},
    { title: 'Hành động', key: 'actions', render: (row) => {
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
            tests.value = resTests.data.data
            if (!selectedTestId.value && tests.value.length > 0) {
                selectedTestId.value = tests.value[0]._id
            }
        }
        if (resStudents.data.status === 'success') students.value = resStudents.data.data
        if (resResults.data.status === 'success') results.value = resResults.data.data

        if (activeTab.value === 'questions' && selectedTestId.value) {
            const resQ = await axios.post(`${API_BASE}/task_service/admin/questions`, { test_id: selectedTestId.value })
            if (resQ.data.status === 'success') questions.value = resQ.data.data
        }
    } catch (error) {
        console.error("Lỗi lấy dữ liệu Admin qua ApiGateway:", error)
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
    loading.value = true
    try {
        const studentList = testForm.value.list_students
            ? testForm.value.list_students.split(/[\s,\n;\r]+/).map(s => s.trim()).filter(s => s)
            : []
            
        const payload = {
            test_code: testForm.value.test_code,
            name: testForm.value.name,
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
        fetchData()
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
        await axios.delete(`${API_BASE}/task_service/admin/tests/delete`, { data: { test_id: id } })
        fetchData()
    } catch (error) {
        console.error("Lỗi xóa test:", error)
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
    questionForm.value = {
        text: question.text,
        answers: JSON.parse(JSON.stringify(question.answers))
    }
    showQuestionModal.value = true
}

function setCorrectAnswer(index) {
    questionForm.value.answers.forEach((ans, i) => {
        ans.is_correct = (i === index)
    })
}

async function saveQuestion() {
    loading.value = true
    try {
        if (isEditing.value) {
            await axios.put(`${API_BASE}/task_service/admin/questions/update`, {
                question_id: editingQuestionId.value,
                text: questionForm.value.text,
                answers: questionForm.value.answers
            })
        } else {
            await axios.post(`${API_BASE}/task_service/admin/questions/create`, {
                test_id: selectedTestId.value,
                text: questionForm.value.text,
                answers: questionForm.value.answers
            })
        }
        showQuestionModal.value = false
        fetchData()
    } catch (error) {
        console.error("Lỗi lưu câu hỏi:", error)
    } finally {
        loading.value = false
    }
}

async function deleteQuestion(id) {
    loading.value = true
    try {
        await axios.delete(`${API_BASE}/task_service/admin/questions/delete`, {
            data: { question_id: id }
        })
        fetchData()
    } catch (error) {
        console.error("Lỗi xóa câu hỏi:", error)
    } finally {
        loading.value = false
    }
}

onMounted(() => {
    if (isAuthenticated.value) fetchData()
})
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
                        <n-menu :value="activeTab" @update:value="val => { activeTab = val; fetchData(); }" :options="[
                            { label: '📊 Tổng quan Dashboard', key: 'dashboard' },
                            { label: '📝 Quản lý Đề thi', key: 'tests' },
                            { label: '❓ Ngân hàng câu hỏi', key: 'questions' },
                            { label: '🏆 Kết quả thi', key: 'results' },
                            { label: '🎓 Danh sách sinh viên', key: 'students' }
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
                                <span v-else>❓ Ngân hàng Câu hỏi</span>
                            </h2>
                            <div>
                                <n-button v-if="activeTab === 'tests'" @click="openCreateTestModal" type="info" style="margin-right: 10px;">+ Thêm Mã Đề</n-button>
                                <n-button v-if="activeTab === 'students'" @click="openCreateStudentModal" type="info" style="margin-right: 10px;">+ Thêm Sinh Viên</n-button>
                                <n-button v-if="activeTab === 'questions'" @click="openCreateModal" type="info" style="margin-right: 10px;">+ Thêm Câu Hỏi</n-button>
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

                                <n-card title="🏆 Lượt bài nộp mới nhất" style="margin-top: 24px;">
                                    <n-data-table :columns="resultColumns" :data="results.slice(0, 5)" :bordered="false" />
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
                                <div style="margin-bottom: 16px; width: 300px;">
                                    <n-input v-model:value="resultSearchQuery" placeholder="🔍 Tìm kiếm MSV hoặc Mã đề..." clearable />
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
                                <div style="margin-bottom: 20px; display: flex; align-items: center; gap: 15px;">
                                    <strong>Chọn Mã Đề Thi:</strong>
                                    <select v-model="selectedTestId" @change="fetchData" style="padding: 8px 12px; border-radius: 8px; border: 1px solid #cbd5e1; width: 320px;">
                                        <option v-for="t in tests" :key="t._id" :value="t._id">{{ t.test_code }} - {{ t.name }}</option>
                                    </select>
                                </div>
                                <n-data-table :columns="questionColumns" :data="questions" :loading="loading" :bordered="false" />
                            </n-card>
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
                    <n-space vertical size="large">
                        <div>
                            <label style="font-weight: bold;">Nội dung câu hỏi:</label>
                            <n-input v-model:value="questionForm.text" type="textarea" placeholder="Nhập nội dung câu hỏi..." />
                        </div>
                        <div>
                            <label style="font-weight: bold;">Các đáp án (Chọn 1 đáp án đúng):</label>
                            <div v-for="(ans, index) in questionForm.answers" :key="index" style="display: flex; align-items: center; gap: 10px; margin-top: 10px;">
                                <input type="radio" :name="'correct_answer'" :checked="ans.is_correct" @change="setCorrectAnswer(index)" style="width: 20px; height: 20px; cursor: pointer;" />
                                <n-input v-model:value="ans.text" :placeholder="`Đáp án ${String.fromCharCode(65 + index)}`" style="flex: 1;" />
                            </div>
                        </div>
                        <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px;">
                            <n-button @click="showQuestionModal = false">Hủy</n-button>
                            <n-button type="primary" @click="saveQuestion" :loading="loading">Lưu</n-button>
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
</style>
