<template>
  <div class="admin-slots app-container">
    <div class="page-header">
      <div>
        <h1 class="page-title">Slot Allocations & Management</h1>
        <p class="page-subtitle">Generate examination time slots, allocate examiners, and set capacity</p>
      </div>
      <button @click="openCreateSlotModal" class="btn btn-primary btn-sm">+ Create Slot</button>
    </div>

    <!-- Alert / Message -->
    <div v-if="feedback.text" :class="['alert', feedback.isError ? 'alert-error' : 'alert-success']">
      {{ feedback.text }}
    </div>

    <!-- Filter by Exam -->
    <div class="filter-bar glass-card">
      <div class="filter-item">
        <label class="form-label" for="exam-filter">Filter by Examination:</label>
        <select id="exam-filter" v-model="selectedExamId" @change="onExamSelected" class="form-select">
          <option value="" disabled>Select Examination</option>
          <option v-for="e in exams" :key="e.id" :value="e.id">
            {{ e.name }} ({{ e.course_name }})
          </option>
        </select>
      </div>
    </div>

    <!-- Slots Table -->
    <div class="table-container glass-card">
      <div v-if="loading" class="table-empty">Loading slots...</div>
      <div v-else-if="!selectedExamId" class="table-empty">Please select an examination above to view scheduled slots.</div>
      <div v-else-if="slots.length === 0" class="table-empty">No slots scheduled for this exam yet. Click "+ Create Slot" to allocate one.</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Slot ID</th>
            <th>Date</th>
            <th>Timing</th>
            <th>Examiner ID</th>
            <th>Seats</th>
            <th>Status</th>
            <th>Meeting Link</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in slots" :key="s.id">
            <td>#{{ s.id }}</td>
            <td><strong>{{ s.date }}</strong></td>
            <td>{{ s.start_time }} – {{ s.end_time }}</td>
            <td>Examiner #{{ s.examiner_id }}</td>
            <td>
              <span>{{ s.available_seats }} / {{ s.max_capacity }} available</span>
            </td>
            <td>
              <span :class="['badge', s.status === 'available' ? 'badge-success' : 'badge-warning']">
                {{ s.status }}
              </span>
            </td>
            <td>
              <a v-if="s.meeting_link" :href="s.meeting_link" target="_blank" rel="noopener" class="meeting-tag">Join Call ↗</a>
              <span v-else class="text-faint">—</span>
            </td>
            <td>
              <button @click="deleteSlot(s.id)" class="btn btn-danger btn-sm">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Slot Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <h3>Create Examination Slot</h3>
        <form @submit.prevent="createSlot" class="modal-form">
          <div class="form-group">
            <label class="form-label" for="slot-exam">Examination</label>
            <select id="slot-exam" v-model="form.exam_id" class="form-select" required>
              <option value="" disabled>Select Examination</option>
              <option v-for="e in exams" :key="e.id" :value="e.id">
                {{ e.name }} ({{ e.course_name }})
              </option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label" for="slot-examiner">Assign Examiner</label>
            <select id="slot-examiner" v-model="form.examiner_id" class="form-select" required>
              <option value="" disabled>Select Examiner</option>
              <option v-for="ex in examiners" :key="ex.id" :value="ex.id">
                {{ ex.name }} ({{ ex.department || 'Department' }})
              </option>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="slot-date">Slot Date</label>
              <input id="slot-date" v-model="form.date" type="date" class="form-input" required />
            </div>

            <div class="form-group">
              <label class="form-label" for="slot-capacity">Capacity (Seats)</label>
              <input id="slot-capacity" v-model="form.max_capacity" type="number" min="1" class="form-input" placeholder="10" required />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="slot-start">Start Time</label>
              <input id="slot-start" v-model="form.start_time" type="time" step="1" class="form-input" required />
            </div>

            <div class="form-group">
              <label class="form-label" for="slot-end">End Time</label>
              <input id="slot-end" v-model="form.end_time" type="time" step="1" class="form-input" required />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="slot-link">Meeting Link (Google Meet / Zoom)</label>
            <input id="slot-link" v-model="form.meeting_link" type="url" class="form-input" placeholder="https://meet.google.com/xyz-abc" />
          </div>

          <div class="modal-actions">
            <button type="button" @click="closeModal" class="btn btn-secondary">Cancel</button>
            <button type="submit" class="btn btn-primary" :disabled="submitting">
              {{ submitting ? 'Allocating...' : 'Create Slot' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { api } from '../../services/api';

const exams = ref([]);
const examiners = ref([]);
const slots = ref([]);
const selectedExamId = ref('');

const loading = ref(false);
const submitting = ref(false);
const showModal = ref(false);

const form = reactive({
  exam_id: '',
  examiner_id: '',
  date: '',
  start_time: '10:00:00',
  end_time: '11:00:00',
  max_capacity: 5,
  meeting_link: ''
});

const feedback = reactive({ text: '', isError: false });
const showFeedback = (text, isError = false) => {
  feedback.text = text;
  feedback.isError = isError;
  setTimeout(() => { feedback.text = ''; }, 4000);
};

const loadInitial = async () => {
  try {
    const [examData, examinerData] = await Promise.all([
      api.get('/api/admin/exams'),
      api.get('/api/admin/examiners')
    ]);
    exams.value = examData.exams || [];
    examiners.value = examinerData.examiners || [];
    if (exams.value.length > 0) {
      selectedExamId.value = exams.value[0].id;
      loadSlots(selectedExamId.value);
    }
  } catch (err) {
    showFeedback('Failed to load exams or examiners.', true);
  }
};

const loadSlots = async (examId) => {
  if (!examId) return;
  loading.value = true;
  try {
    const data = await api.get(`/api/admin/exams/${examId}/slots`);
    slots.value = data.slots || [];
  } catch (err) {
    showFeedback(err.message || 'Error fetching exam slots.', true);
  } finally {
    loading.value = false;
  }
};

const onExamSelected = () => {
  loadSlots(selectedExamId.value);
};

const openCreateSlotModal = () => {
  form.exam_id = selectedExamId.value || (exams.value.length ? exams.value[0].id : '');
  form.examiner_id = examiners.value.length ? examiners.value[0].id : '';
  const today = new Date().toISOString().split('T')[0];
  form.date = today;
  form.start_time = '10:00:00';
  form.end_time = '11:00:00';
  form.max_capacity = 5;
  form.meeting_link = '';
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
};

const createSlot = async () => {
  submitting.value = true;
  try {
    // Format start/end time if lacking seconds
    let st = form.start_time;
    if (st.split(':').length === 2) st += ':00';
    let et = form.end_time;
    if (et.split(':').length === 2) et += ':00';

    await api.post(`/api/admin/exams/${form.exam_id}/slots`, {
      examiner_id: parseInt(form.examiner_id),
      date: form.date,
      start_time: st,
      end_time: et,
      max_capacity: parseInt(form.max_capacity),
      meeting_link: form.meeting_link
    });

    showFeedback('Slot created successfully.');
    closeModal();
    selectedExamId.value = form.exam_id;
    loadSlots(form.exam_id);
  } catch (err) {
    showFeedback(err.message || 'Failed to create slot.', true);
  } finally {
    submitting.value = false;
  }
};

const deleteSlot = async (slotId) => {
  if (!confirm('Are you sure you want to delete this slot?')) return;
  try {
    await api.delete(`/api/admin/slots/${slotId}`);
    showFeedback('Slot deleted successfully.');
    loadSlots(selectedExamId.value);
  } catch (err) {
    showFeedback(err.message || 'Cannot delete slot with bookings.', true);
  }
};

onMounted(() => {
  loadInitial();
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

.filter-bar {
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  max-width: 480px;
}

.table-empty {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
}

.meeting-tag {
  color: var(--info);
  font-weight: 500;
}

.form-row {
  display: flex;
  gap: 1rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
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
