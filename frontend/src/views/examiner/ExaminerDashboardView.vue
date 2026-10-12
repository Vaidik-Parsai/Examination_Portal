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
        <span class="stat-label">Pending Candidate Evaluations</span>
        <span class="stat-value">{{ stats.pending_evaluations || 0 }}</span>
      </div>
    </div>

    <!-- My Slots Table -->
    <div class="table-container glass-card">
      <div class="table-header-row">
        <h3>My Scheduled Examination Slots</h3>
      </div>
      <div v-if="loading" class="table-empty">Loading your slots...</div>
      <div v-else-if="slots.length === 0" class="table-empty">No slots scheduled yet. Click "+ Schedule Slot" to create your assessment window.</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Slot ID</th>
            <th>Exam Name</th>
            <th>Date</th>
            <th>Timing</th>
            <th>Capacity</th>
            <th>Status</th>
            <th>Meeting Link</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in slots" :key="s.id">
            <td>#{{ s.id }}</td>
            <td><strong>{{ s.exam_name || `Exam #${s.examination_id}` }}</strong></td>
            <td>{{ s.date }}</td>
            <td>{{ s.start_time }} – {{ s.end_time }}</td>
            <td>{{ s.available_seats }} / {{ s.max_capacity }} available</td>
            <td>
              <span :class="['badge', s.status === 'completed' ? 'badge-student' : (s.status === 'available' ? 'badge-success' : 'badge-warning')]">
                {{ s.status }}
              </span>
            </td>
            <td>
              <a v-if="s.meeting_link" :href="s.meeting_link" target="_blank" rel="noopener" class="meeting-tag">Join Call ↗</a>
              <span v-else class="text-faint">—</span>
            </td>
            <td>
              <div class="action-buttons">
                <router-link :to="`/examiner/slots/${s.id}/bookings`" class="btn btn-primary btn-sm">
                  Candidates & Grading
                </router-link>
                <button v-if="s.status !== 'completed'" @click="completeSlot(s.id)" class="btn btn-secondary btn-sm" title="Mark complete once all candidates are graded">
                  Complete
                </button>
                <button @click="deleteSlot(s.id)" class="btn btn-danger btn-sm">
                  Delete
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Slot Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <h3>Schedule Viva Assessment Slot</h3>
        <p class="subtitle">Open a booking window for students within the examination schedule.</p>
        <form @submit.prevent="createSlot" class="modal-form">
          <div class="form-group">
            <label class="form-label" for="ex-slot-exam">Select Examination</label>
            <select id="ex-slot-exam" v-model="form.examination_id" class="form-select" required>
              <option value="" disabled>Choose an exam</option>
              <option v-for="e in exams" :key="e.id" :value="e.id">
                {{ e.name }} ({{ e.course_name }})
              </option>
            </select>
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
            <label class="form-label" for="ex-slot-link">Video Meeting Link</label>
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { api } from '../../services/api';

const stats = ref({});
const slots = ref([]);
const exams = ref([]);

const loading = ref(true);
const submitting = ref(false);
const showModal = ref(false);

const form = reactive({
  examination_id: '',
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

const loadDashboard = async () => {
  loading.value = true;
  try {
    const [dashData, slotData, examData] = await Promise.all([
      api.get('/api/examiner/dashboard'),
      api.get('/api/examiner/slots'),
      api.get('/api/admin/exams').catch(() => ({ exams: [] }))
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
      meeting_link: form.meeting_link
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

const completeSlot = async (slotId) => {
  try {
    const res = await api.post(`/api/examiner/slots/${slotId}/complete`, {});
    showFeedback(res.message || 'Slot finalized and completed.');
    loadDashboard();
  } catch (err) {
    showFeedback(err.message || 'Cannot complete slot: ensure all candidates are graded.', true);
  }
};

const deleteSlot = async (slotId) => {
  if (!confirm('Are you sure you want to delete this slot?')) return;
  try {
    await api.delete(`/api/examiner/slots/${slotId}`);
    showFeedback('Slot deleted successfully.');
    loadDashboard();
  } catch (err) {
    showFeedback(err.message || 'Cannot delete slot with existing student bookings.', true);
  }
};

onMounted(() => {
  loadDashboard();
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

.table-header-row {
  margin-bottom: 1rem;
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

.subtitle {
  color: var(--text-muted);
  font-size: 0.9rem;
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
