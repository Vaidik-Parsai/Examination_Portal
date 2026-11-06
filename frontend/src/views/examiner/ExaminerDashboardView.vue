<template>
  <div class="examiner-dashboard app-container">
    <div class="page-header">
      <div>
        <h1 class="page-title">Examiner Assessment Hub</h1>
        <p class="page-subtitle">Schedule viva slots, manage assigned candidates, and record evaluation grades</p>
      </div>
      <button @click="openCreateSlotModal" class="btn btn-primary btn-sm">+ Schedule Slot</button>
    </div>

    <!-- Alert / Message -->
    <div v-if="feedback.text" :class="['alert', feedback.isError ? 'alert-error' : 'alert-success']">
      {{ feedback.text }}
    </div>

    <!-- Stats Grid -->
    <div class="stats-grid">
      <div class="stat-card">
        <span class="stat-label">Total Slots</span>
        <span class="stat-value">{{ stats.total_slots || 0 }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Active Slots</span>
        <span class="stat-value">{{ stats.active_slots || 0 }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Completed Evaluations</span>
        <span class="stat-value">{{ stats.total_evaluations || 0 }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Pending Evaluations</span>
        <span class="stat-value">{{ stats.pending_evaluations || 0 }}</span>
      </div>
    </div>

    <!-- My Slots Table -->
    <div class="simple-card">
      <h3 style="margin-bottom:1rem;">My Scheduled Examination Slots</h3>
      <div v-if="loading" class="table-empty">Loading your slots...</div>
      <div v-else-if="slots.length === 0" class="table-empty">No slots scheduled yet. Click "+ Schedule Slot" to create your assessment window.</div>
      <div v-else class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Exam / Course</th>
              <th>Date</th>
              <th>Time</th>
              <th>Seats</th>
              <th>Status</th>
              <th>Rubrics</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in slots" :key="s.id">
              <td>#{{ s.id }}</td>
              <td>
                <strong>{{ s.exam_name || `Exam #${s.examination_id}` }}</strong>
                <div class="text-muted small">{{ s.course_name }}</div>
              </td>
              <td>{{ s.date }}</td>
              <td>{{ s.start_time }} – {{ s.end_time }}</td>
              <td>{{ s.available_seats }} / {{ s.max_capacity }}</td>
              <td>
                <span :class="['badge', s.status === 'completed' ? 'badge-student' : (s.status === 'available' ? 'badge-success' : 'badge-warning')]">
                  {{ s.status }}
                </span>
              </td>
              <td>
                <span v-if="s.rubrics && s.rubrics.length" class="badge badge-examiner">{{ s.rubrics.length }} rubric{{ s.rubrics.length > 1 ? 's' : '' }}</span>
                <span v-else class="text-muted small">None</span>
              </td>
              <td>
                <div class="action-buttons">
                  <router-link :to="`/examiner/slots/${s.id}/bookings`" class="btn btn-primary btn-sm">
                    Candidates
                  </router-link>
                  <button
                    v-if="s.booked_count === 0 && s.status !== 'completed'"
                    @click="openEditModal(s)"
                    class="btn btn-secondary btn-sm"
                    title="Edit slot (only before any student books)"
                  >Edit</button>
                  <button v-if="s.status !== 'completed'" @click="completeSlot(s.id)" class="btn btn-secondary btn-sm">
                    Complete
                  </button>
                  <button @click="deleteSlot(s.id)" class="btn btn-danger btn-sm">Delete</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create Slot Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <h3>Schedule Viva Assessment Slot</h3>
        <p class="text-muted" style="font-size:13px; margin-bottom:12px;">Open a booking window for students within the examination schedule.</p>
        <form @submit.prevent="createSlot">
          <div class="form-group">
            <label class="form-label" for="ex-slot-exam">Select Examination</label>
            <select id="ex-slot-exam" v-model="form.examination_id" class="form-select" required>
              <option value="" disabled>Choose an exam</option>
              <option v-for="e in exams" :key="e.id" :value="e.id">
                {{ e.name }} ({{ e.course_name }})
                <template v-if="e.rubrics && e.rubrics.length"> — {{ e.rubrics.length }} rubric(s)</template>
              </option>
            </select>
          </div>

          <!-- Show rubrics for selected exam -->
          <div v-if="selectedExamRubrics.length" class="rubric-ref">
            <strong>Rubrics for this exam:</strong>
            <ul>
              <li v-for="r in selectedExamRubrics" :key="r.id">{{ r.criterion_name }} ({{ r.max_marks ?? '?' }} pts)</li>
            </ul>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="ex-slot-date">Date</label>
              <input id="ex-slot-date" v-model="form.date" type="date" class="form-input" required />
            </div>
            <div class="form-group">
              <label class="form-label" for="ex-slot-cap">Max Capacity</label>
              <input id="ex-slot-cap" v-model="form.max_capacity" type="number" min="1" class="form-input" placeholder="5" required />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="ex-slot-start">Start Time</label>
              <input id="ex-slot-start" v-model="form.start_time" type="time" step="1" class="form-input" required />
            </div>
            <div class="form-group">
              <label class="form-label" for="ex-slot-end">End Time</label>
              <input id="ex-slot-end" v-model="form.end_time" type="time" step="1" class="form-input" required />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="ex-slot-link">Video Meeting Link (optional)</label>
            <input id="ex-slot-link" v-model="form.meeting_link" type="url" class="form-input" placeholder="https://meet.google.com/xyz-abc" />
          </div>

          <div class="modal-actions">
            <button type="button" @click="closeModal" class="btn btn-secondary">Cancel</button>
            <button type="submit" class="btn btn-primary" :disabled="submitting">
              {{ submitting ? 'Scheduling...' : 'Open Slot' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Edit Slot Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal-content">
        <h3>Edit Slot #{{ editForm.id }}</h3>
        <p class="text-muted" style="font-size:13px; margin-bottom:12px;">
          You can only edit a slot before any student books it.
        </p>
        <form @submit.prevent="saveEditSlot">
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Date</label>
              <input v-model="editForm.date" type="date" class="form-input" required />
            </div>
            <div class="form-group">
              <label class="form-label">Max Capacity</label>
              <input v-model="editForm.max_capacity" type="number" min="1" class="form-input" required />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Start Time</label>
              <input v-model="editForm.start_time" type="time" step="1" class="form-input" required />
            </div>
            <div class="form-group">
              <label class="form-label">End Time</label>
              <input v-model="editForm.end_time" type="time" step="1" class="form-input" required />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Meeting Link (optional)</label>
            <input v-model="editForm.meeting_link" type="url" class="form-input" />
          </div>
          <div class="modal-actions">
            <button type="button" @click="closeEditModal" class="btn btn-secondary">Cancel</button>
            <button type="submit" class="btn btn-primary" :disabled="submitting">
              {{ submitting ? 'Saving...' : 'Save Changes' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { api } from '../../services/api';

const stats = ref({});
const slots = ref([]);
const exams = ref([]);

const loading = ref(true);
const submitting = ref(false);
const showModal = ref(false);
const showEditModal = ref(false);

const form = reactive({
  examination_id: '',
  date: '',
  start_time: '10:00:00',
  end_time: '11:00:00',
  max_capacity: 5,
  meeting_link: ''
});

const editForm = reactive({
  id: null,
  date: '',
  start_time: '',
  end_time: '',
  max_capacity: 5,
  meeting_link: ''
});

const feedback = reactive({ text: '', isError: false });
const showFeedback = (text, isError = false) => {
  feedback.text = text;
  feedback.isError = isError;
  setTimeout(() => { feedback.text = ''; }, 5000);
};

const selectedExamRubrics = computed(() => {
  if (!form.examination_id) return [];
  const exam = exams.value.find(e => e.id === parseInt(form.examination_id));
  return exam?.rubrics || [];
});

const loadDashboard = async () => {
  loading.value = true;
  try {
    const [dashData, slotData, examData] = await Promise.all([
      api.get('/api/examiner/dashboard'),
      api.get('/api/examiner/slots'),
      api.get('/api/examiner/exams').catch(() => ({ exams: [] }))
    ]);
    stats.value = dashData.stats || {};
    slots.value = slotData.slots || [];
    exams.value = examData.exams || [];
  } catch (err) {
    showFeedback(err.message || 'Error loading examiner portal.', true);
  } finally {
    loading.value = false;
  }
};

const openCreateSlotModal = () => {
  form.examination_id = exams.value.length ? exams.value[0].id : '';
  form.date = new Date().toISOString().split('T')[0];
  form.start_time = '10:00:00';
  form.end_time = '11:00:00';
  form.max_capacity = 5;
  form.meeting_link = '';
  showModal.value = true;
};

const closeModal = () => { showModal.value = false; };

const createSlot = async () => {
  submitting.value = true;
  try {
    let st = form.start_time;
    if (st.split(':').length === 2) st += ':00';
    let et = form.end_time;
    if (et.split(':').length === 2) et += ':00';

    await api.post('/api/examiner/slots', {
      examination_id: parseInt(form.examination_id),
      date: form.date,
      start_time: st,
      end_time: et,
      max_capacity: parseInt(form.max_capacity),
      meeting_link: form.meeting_link || null
    });

    showFeedback('Examination slot scheduled successfully.');
    closeModal();
    loadDashboard();
  } catch (err) {
    showFeedback(err.message || 'Failed to schedule slot.', true);
  } finally {
    submitting.value = false;
  }
};

const openEditModal = (slot) => {
  editForm.id = slot.id;
  editForm.date = slot.date;
  editForm.start_time = slot.start_time;
  editForm.end_time = slot.end_time;
  editForm.max_capacity = slot.max_capacity;
  editForm.meeting_link = slot.meeting_link || '';
  showEditModal.value = true;
};

const closeEditModal = () => { showEditModal.value = false; };

const saveEditSlot = async () => {
  submitting.value = true;
  try {
    let st = editForm.start_time;
    if (st.split(':').length === 2) st += ':00';
    let et = editForm.end_time;
    if (et.split(':').length === 2) et += ':00';

    await api.put(`/api/examiner/slots/${editForm.id}`, {
      date: editForm.date,
      start_time: st,
      end_time: et,
      max_capacity: parseInt(editForm.max_capacity),
      meeting_link: editForm.meeting_link || null
    });

    showFeedback('Slot updated successfully.');
    closeEditModal();
    loadDashboard();
  } catch (err) {
    showFeedback(err.message || 'Failed to update slot.', true);
  } finally {
    submitting.value = false;
  }
};

const completeSlot = async (slotId) => {
  if (!confirm('Mark this slot as completed? All candidates must already be graded.')) return;
  try {
    const res = await api.post(`/api/examiner/slots/${slotId}/complete`, {});
    showFeedback(res.message || 'Slot finalized.');
    loadDashboard();
  } catch (err) {
    showFeedback(err.message || 'Cannot complete slot: ensure all candidates are graded.', true);
  }
};

const deleteSlot = async (slotId) => {
  if (!confirm('Delete this slot? This cannot be undone.')) return;
  try {
    await api.delete(`/api/examiner/slots/${slotId}`);
    showFeedback('Slot deleted.');
    loadDashboard();
  } catch (err) {
    showFeedback(err.message || 'Cannot delete slot with existing student bookings.', true);
  }
};

onMounted(() => { loadDashboard(); });
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.text-muted { color: #6c757d; }
.small { font-size: 12px; }

.action-buttons { display: flex; gap: 6px; flex-wrap: wrap; }

.table-empty { text-align: center; padding: 3rem; color: #6c757d; }

.rubric-ref {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 10px 14px;
  margin-bottom: 12px;
  font-size: 13px;
}
.rubric-ref ul { margin: 6px 0 0 16px; }
.rubric-ref li { margin-bottom: 3px; }
</style>
