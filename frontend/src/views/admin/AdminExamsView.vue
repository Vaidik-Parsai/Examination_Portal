<template>
  <div class="admin-exams app-container">
    <div class="page-header">
      <div>
        <h1 class="page-title">Examinations & Rubrics</h1>
        <p class="page-subtitle">Define examinations, assessment windows, and evaluation scoring rubrics</p>
      </div>
      <button @click="openCreateExamModal" class="btn btn-primary btn-sm">+ Create Examination</button>
    </div>

    <!-- Alert / Message -->
    <div v-if="feedback.text" :class="['alert', feedback.isError ? 'alert-error' : 'alert-success']">
      {{ feedback.text }}
    </div>

    <!-- Exams Table -->
    <div class="table-container glass-card">
      <div v-if="loading" class="table-empty">Loading examinations...</div>
      <div v-else-if="exams.length === 0" class="table-empty">No examinations scheduled yet. Click "+ Create Examination" to begin.</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Course</th>
            <th>Exam Name</th>
            <th>Type</th>
            <th>Duration</th>
            <th>Max Marks</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in exams" :key="e.id">
            <td>#{{ e.id }}</td>
            <td><strong>{{ e.course_name }}</strong></td>
            <td>{{ e.name }}</td>
            <td><span class="badge badge-student">{{ e.exam_type }}</span></td>
            <td>{{ e.duration }} min</td>
            <td>{{ e.max_marks }} pts</td>
            <td>
              <span :class="['badge', e.status === 'published' ? 'badge-success' : 'badge-warning']">
                {{ e.status }}
              </span>
            </td>
            <td>
              <div class="action-buttons">
                <button @click="openRubricsModal(e)" class="btn btn-secondary btn-sm">Rubrics</button>
                <button @click="openEditExamModal(e)" class="btn btn-secondary btn-sm">Edit</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create/Edit Exam Modal -->
    <div v-if="showExamModal" class="modal-overlay" @click.self="closeExamModal">
      <div class="modal-content">
        <h3>{{ isEditingExam ? 'Edit Examination' : 'Create New Examination' }}</h3>
        <form @submit.prevent="saveExam" class="modal-form">
          <div class="form-group" v-if="!isEditingExam">
            <label class="form-label" for="exam-course">Course</label>
            <select id="exam-course" v-model="examForm.course_id" class="form-select" required>
              <option value="" disabled>Select a course</option>
              <option v-for="c in courses" :key="c.id" :value="c.id">
                {{ c.code }} - {{ c.name }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label" for="exam-name">Exam Name</label>
            <input
              id="exam-name"
              v-model="examForm.name"
              type="text"
              class="form-input"
              placeholder="e.g. End Term Viva Assessment"
              required
            />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="exam-type">Exam Type</label>
              <select id="exam-type" v-model="examForm.exam_type" class="form-select">
                <option value="viva">Oral Viva</option>
                <option value="written">Written</option>
                <option value="practical">Practical</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label" for="exam-duration">Duration (Minutes)</label>
              <input
                id="exam-duration"
                v-model="examForm.duration"
                type="number"
                min="5"
                class="form-input"
                placeholder="20"
                required
              />
            </div>

            <div class="form-group">
              <label class="form-label" for="exam-max-marks">Max Marks</label>
              <input
                id="exam-max-marks"
                v-model="examForm.max_marks"
                type="number"
                min="1"
                class="form-input"
                placeholder="100"
                required
              />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="exam-status">Status</label>
            <select id="exam-status" v-model="examForm.status" class="form-select">
              <option value="draft">Draft</option>
              <option value="published">Published</option>
              <option value="completed">Completed</option>
            </select>
          </div>

          <div class="modal-actions">
            <button type="button" @click="closeExamModal" class="btn btn-secondary">Cancel</button>
            <button type="submit" class="btn btn-primary" :disabled="submitting">
              {{ submitting ? 'Saving...' : (isEditingExam ? 'Update Exam' : 'Create Exam') }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Rubrics Modal -->
    <div v-if="showRubricsModal" class="modal-overlay" @click.self="closeRubricsModal">
      <div class="modal-content modal-wide">
        <div class="modal-header">
          <div>
            <h3>Scoring Rubrics</h3>
            <p class="subtitle">For: {{ activeExam?.name }} ({{ activeExam?.course_name }})</p>
          </div>
          <button @click="closeRubricsModal" class="btn btn-secondary btn-sm">Close</button>
        </div>

        <!-- Add Rubric Form -->
        <form @submit.prevent="addRubric" class="rubric-form glass-card">
          <h4>+ Add Rubric Criterion</h4>
          <div class="form-row">
            <div class="form-group flex-2">
              <label class="form-label">Criterion Name</label>
              <input v-model="rubricForm.criterion_name" type="text" class="form-input" placeholder="e.g. Conceptual Understanding" required />
            </div>
            <div class="form-group">
              <label class="form-label">Max Marks</label>
              <input v-model="rubricForm.max_marks" type="number" class="form-input" placeholder="25" required />
            </div>
            <div class="form-group">
              <label class="form-label">Weight (%)</label>
              <input v-model="rubricForm.weightage" type="number" step="0.1" class="form-input" placeholder="25.0" />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Description / Guidelines</label>
            <input v-model="rubricForm.description" type="text" class="form-input" placeholder="Evaluation criteria instructions for examiners..." />
          </div>
          <button type="submit" class="btn btn-primary btn-sm align-self-start" :disabled="rubricSubmitting">
            {{ rubricSubmitting ? 'Adding...' : 'Add Criterion' }}
          </button>
        </form>

        <!-- Current Rubrics Table -->
        <div class="table-container">
          <div v-if="rubrics.length === 0" class="table-empty">No criteria defined yet. Add criteria above.</div>
          <table v-else class="data-table">
            <thead>
              <tr>
                <th>Criterion</th>
                <th>Max Marks</th>
                <th>Weightage</th>
                <th>Description</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in rubrics" :key="r.id">
                <td><strong>{{ r.criterion_name }}</strong></td>
                <td>{{ r.max_marks }} pts</td>
                <td>{{ r.weightage ? `${r.weightage}%` : '—' }}</td>
                <td>{{ r.description || '—' }}</td>
                <td>
                  <button @click="deleteRubric(r.id)" class="btn btn-danger btn-sm">Remove</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { api } from '../../services/api';

const exams = ref([]);
const courses = ref([]);
const rubrics = ref([]);
const activeExam = ref(null);

const loading = ref(true);
const submitting = ref(false);
const rubricSubmitting = ref(false);

const showExamModal = ref(false);
const isEditingExam = ref(false);
const editingExamId = ref(null);
const showRubricsModal = ref(false);

const examForm = reactive({
  course_id: '',
  name: '',
  exam_type: 'viva',
  duration: 20,
  max_marks: 100,
  status: 'published'
});

const rubricForm = reactive({
  criterion_name: '',
  max_marks: 25,
  weightage: 25.0,
  description: ''
});

const feedback = reactive({ text: '', isError: false });
const showFeedback = (text, isError = false) => {
  feedback.text = text;
  feedback.isError = isError;
  setTimeout(() => { feedback.text = ''; }, 4000);
};

const loadExams = async () => {
  loading.value = true;
  try {
    const [examData, courseData] = await Promise.all([
      api.get('/api/admin/exams'),
      api.get('/api/admin/courses')
    ]);
    exams.value = examData.exams || [];
    courses.value = courseData.courses || [];
  } catch (err) {
    showFeedback(err.message || 'Error loading examination data.', true);
  } finally {
    loading.value = false;
  }
};

const openCreateExamModal = () => {
  isEditingExam.value = false;
  editingExamId.value = null;
  examForm.course_id = courses.value.length ? courses.value[0].id : '';
  examForm.name = '';
  examForm.exam_type = 'viva';
  examForm.duration = 20;
  examForm.max_marks = 100;
  examForm.status = 'published';
  showExamModal.value = true;
};

const openEditExamModal = (e) => {
  isEditingExam.value = true;
  editingExamId.value = e.id;
  examForm.course_id = e.course_id;
  examForm.name = e.name;
  examForm.exam_type = e.exam_type || 'viva';
  examForm.duration = e.duration || 20;
  examForm.max_marks = e.max_marks || 100;
  examForm.status = e.status || 'published';
  showExamModal.value = true;
};

const closeExamModal = () => {
  showExamModal.value = false;
};

const saveExam = async () => {
  submitting.value = true;
  try {
    if (isEditingExam.value) {
      await api.put(`/api/admin/exams/${editingExamId.value}`, {
        name: examForm.name,
        exam_type: examForm.exam_type,
        duration: parseInt(examForm.duration),
        max_marks: parseInt(examForm.max_marks),
        status: examForm.status
      });
      showFeedback('Examination updated successfully.');
    } else {
      await api.post('/api/admin/exams', {
        course_id: parseInt(examForm.course_id),
        name: examForm.name,
        exam_type: examForm.exam_type,
        duration: parseInt(examForm.duration),
        max_marks: parseInt(examForm.max_marks),
        status: examForm.status
      });
      showFeedback('Examination created successfully.');
    }
    closeExamModal();
    loadExams();
  } catch (err) {
    showFeedback(err.message || 'Failed to save examination.', true);
  } finally {
    submitting.value = false;
  }
};

// Rubrics
const openRubricsModal = async (exam) => {
  activeExam.value = exam;
  showRubricsModal.value = true;
  await loadRubrics(exam.id);
};

const closeRubricsModal = () => {
  showRubricsModal.value = false;
  activeExam.value = null;
};

const loadRubrics = async (examId) => {
  try {
    const data = await api.get(`/api/admin/exams/${examId}/rubrics`);
    rubrics.value = data.rubrics || [];
  } catch (err) {
    showFeedback('Failed to load rubrics.', true);
  }
};

const addRubric = async () => {
  rubricSubmitting.value = true;
  try {
    await api.post(`/api/admin/exams/${activeExam.value.id}/rubrics`, {
      criterion_name: rubricForm.criterion_name,
      max_marks: parseInt(rubricForm.max_marks),
      weightage: parseFloat(rubricForm.weightage || 0),
      description: rubricForm.description
    });
    rubricForm.criterion_name = '';
    rubricForm.description = '';
    await loadRubrics(activeExam.value.id);
  } catch (err) {
    showFeedback(err.message || 'Failed to add rubric.', true);
  } finally {
    rubricSubmitting.value = false;
  }
};

const deleteRubric = async (rubricId) => {
  if (!confirm('Remove this criterion?')) return;
  try {
    await api.delete(`/api/admin/rubrics/${rubricId}`);
    await loadRubrics(activeExam.value.id);
  } catch (err) {
    showFeedback('Failed to delete rubric.', true);
  }
};

onMounted(() => {
  loadExams();
});
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.table-empty {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

.form-row {
  display: flex;
  gap: 1rem;
}

.flex-2 {
  flex: 2;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

.modal-wide {
  max-width: 720px;
}

.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.subtitle {
  color: var(--text-muted);
  font-size: 0.9rem;
}

.rubric-form {
  padding: 1.25rem;
  margin-bottom: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.alert {
  padding: 0.75rem 1rem;
  border-radius: var(--radius-md);
  margin-bottom: 1.5rem;
}

.alert-success {
  background: var(--success-bg);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: #a7f3d0;
}

.alert-error {
  background: var(--danger-bg);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #fca5a5;
}
</style>
