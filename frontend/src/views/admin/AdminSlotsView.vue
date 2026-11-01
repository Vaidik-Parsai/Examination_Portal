<template>
  <div class="admin-slots app-container">
    <div class="page-header d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
      <div>
        <h1 class="page-title h2 mb-1">Slot Allocations & Management</h1>
        <p class="page-subtitle text-muted mb-0">Generate time slots, reassign examiners, reschedule sessions, and toggle booking access</p>
      </div>
      <button @click="openCreateSlotModal" class="btn btn-primary btn-sm">+ Create Slot</button>
    </div>

    <!-- Alert / Message -->
    <div v-if="feedback.text" :class="['alert', feedback.isError ? 'alert-danger' : 'alert-success']" role="alert">
      {{ feedback.text }}
    </div>

    <!-- Filter by Exam -->
    <div class="card shadow-sm border-0 mb-4 p-3">
      <div class="row align-items-center g-2">
        <div class="col-md-3">
          <label class="form-label fw-bold mb-0" for="exam-filter">Select Examination:</label>
        </div>
        <div class="col-md-9">
          <select id="exam-filter" v-model="selectedExamId" @change="onExamSelected" class="form-select">
            <option value="" disabled>Select Examination to view slots</option>
            <option v-for="e in exams" :key="e.id" :value="e.id">
              {{ e.name }} ({{ e.course_name }}) - {{ e.status }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Slots Table -->
    <div class="card shadow-sm border-0 mb-4 p-3">
      <div v-if="loading" class="text-center py-4 text-muted">Loading scheduled slots...</div>
      <div v-else-if="!selectedExamId" class="text-center py-4 text-muted">Please select an examination above to view scheduled slots.</div>
      <div v-else-if="slots.length === 0" class="text-center py-4 text-muted">No slots scheduled for this exam yet. Click "+ Create Slot" to allocate one.</div>
      <div v-else class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead class="table-light">
            <tr>
              <th>Slot ID</th>
              <th>Date</th>
              <th>Timing</th>
              <th>Assigned Examiner</th>
              <th>Capacity</th>
              <th>Status</th>
              <th>Meeting Link</th>
              <th class="text-end">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in slots" :key="s.id">
              <td>#{{ s.id }}</td>
              <td><strong>{{ s.date }}</strong></td>
              <td>{{ s.start_time }} – {{ s.end_time }}</td>
              <td>
                <strong>{{ s.examiner_name || `Examiner #${s.examiner_id}` }}</strong>
                <div v-if="s.examiner_department" class="small text-muted">{{ s.examiner_department }}</div>
              </td>
              <td>
                <span class="badge bg-light text-dark border">{{ s.available_seats }} / {{ s.max_capacity }} seats left</span>
                <span v-if="s.bookings_count" class="ms-1 badge bg-info text-dark">{{ s.bookings_count }} booked</span>
              </td>
              <td>
                <span :class="['badge', s.status === 'available' ? 'bg-success' : (s.status === 'closed' ? 'bg-danger' : 'bg-secondary')]">
                  {{ s.status }}
                </span>
              </td>
              <td>
                <a v-if="s.meeting_link" :href="s.meeting_link" target="_blank" rel="noopener" class="btn btn-outline-info btn-sm">
                  Meeting ↗
                </a>
                <span v-else class="text-muted">—</span>
              </td>
              <td class="text-end">
                <div class="btn-group btn-group-sm">
                  <!-- Toggle Slot Booking -->
                  <button
                    @click="toggleSlotBooking(s)"
                    :class="['btn', s.status === 'available' ? 'btn-outline-warning' : 'btn-outline-success']"
                    :title="s.status === 'available' ? 'Close booking for this slot' : 'Open booking for this slot'"
                  >
                    {{ s.status === 'available' ? 'Close Booking' : 'Open Booking' }}
                  </button>
                  <!-- Edit / Reschedule Slot -->
                  <button @click="openEditSlotModal(s)" class="btn btn-outline-primary" title="Reschedule date/time or reassign examiner">
                    Edit / Reschedule
                  </button>
                  <!-- Delete Slot -->
                  <button @click="deleteSlot(s.id)" class="btn btn-outline-danger" title="Delete slot">
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create Slot Modal -->
    <div v-if="showModal" class="modal-backdrop fade show"></div>
    <div v-if="showModal" class="modal d-block" tabindex="-1" role="dialog">
      <div class="modal-dialog modal-dialog-centered" role="document">
        <div class="modal-content shadow border-0">
          <div class="modal-header">
            <h5 class="modal-title fw-bold">Create Examination Slot</h5>
            <button type="button" class="btn-close" @click="closeModal" aria-label="Close"></button>
          </div>
          <form @submit.prevent="createSlot">
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label" for="slot-exam">Examination</label>
                <select id="slot-exam" v-model="form.exam_id" class="form-select" required>
                  <option value="" disabled>Select Examination</option>
                  <option v-for="e in exams" :key="e.id" :value="e.id">
                    {{ e.name }} ({{ e.course_name }})
                  </option>
                </select>
              </div>

              <div class="mb-3">
                <label class="form-label" for="slot-examiner">Assign Examiner</label>
                <select id="slot-examiner" v-model="form.examiner_id" class="form-select" required>
                  <option value="" disabled>Select Examiner</option>
                  <option v-for="ex in examiners" :key="ex.id" :value="ex.id">
                    {{ ex.name }} ({{ ex.department || 'Department' }})
                  </option>
                </select>
              </div>

              <div class="row g-2 mb-3">
                <div class="col-6">
                  <label class="form-label" for="slot-date">Slot Date</label>
                  <input id="slot-date" v-model="form.date" type="date" class="form-control" required />
                </div>
                <div class="col-6">
                  <label class="form-label" for="slot-capacity">Capacity (Seats)</label>
                  <input id="slot-capacity" v-model="form.max_capacity" type="number" min="1" class="form-control" required />
                </div>
              </div>

              <div class="row g-2 mb-3">
                <div class="col-6">
                  <label class="form-label" for="slot-start">Start Time</label>
                  <input id="slot-start" v-model="form.start_time" type="time" step="1" class="form-control" required />
                </div>
                <div class="col-6">
                  <label class="form-label" for="slot-end">End Time</label>
                  <input id="slot-end" v-model="form.end_time" type="time" step="1" class="form-control" required />
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label" for="slot-link">Meeting Link (e.g., Google Meet / Zoom)</label>
                <input id="slot-link" v-model="form.meeting_link" type="url" class="form-control" placeholder="https://meet.google.com/..." />
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" @click="closeModal" class="btn btn-secondary">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="submitting">
                {{ submitting ? 'Creating...' : 'Create Slot' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Edit / Reschedule Slot Modal -->
    <div v-if="showEditModal" class="modal-backdrop fade show"></div>
    <div v-if="showEditModal" class="modal d-block" tabindex="-1" role="dialog">
      <div class="modal-dialog modal-dialog-centered" role="document">
        <div class="modal-content shadow border-0">
          <div class="modal-header">
            <h5 class="modal-title fw-bold">Edit / Reschedule Slot #{{ editForm.id }}</h5>
            <button type="button" class="btn-close" @click="closeEditModal" aria-label="Close"></button>
          </div>
          <form @submit.prevent="saveSlotEdit">
            <div class="modal-body">
              <div class="alert alert-info py-2 small mb-3">
                <strong>Rescheduling note:</strong> Modifying the date or time will keep existing student bookings and flag them with an updated reschedule notice. Overlapping examiner schedules will be rejected.
              </div>

              <div class="mb-3">
                <label class="form-label" for="edit-slot-examiner">Change Assigned Examiner</label>
                <select id="edit-slot-examiner" v-model="editForm.examiner_id" class="form-select" required>
                  <option v-for="ex in examiners" :key="ex.id" :value="ex.id">
                    {{ ex.name }} ({{ ex.department || 'Department' }})
                  </option>
                </select>
              </div>

              <div class="row g-2 mb-3">
                <div class="col-6">
                  <label class="form-label" for="edit-slot-date">Slot Date</label>
                  <input id="edit-slot-date" v-model="editForm.date" type="date" class="form-control" required />
                </div>
                <div class="col-6">
                  <label class="form-label" for="edit-slot-capacity">Capacity (Seats)</label>
                  <input id="edit-slot-capacity" v-model="editForm.max_capacity" type="number" min="1" class="form-control" required />
                </div>
              </div>

              <div class="row g-2 mb-3">
                <div class="col-6">
                  <label class="form-label" for="edit-slot-start">Start Time</label>
                  <input id="edit-slot-start" v-model="editForm.start_time" type="time" step="1" class="form-control" required />
                </div>
                <div class="col-6">
                  <label class="form-label" for="edit-slot-end">End Time</label>
                  <input id="edit-slot-end" v-model="editForm.end_time" type="time" step="1" class="form-control" required />
                </div>
              </div>

              <div class="row g-2 mb-3">
                <div class="col-6">
                  <label class="form-label" for="edit-slot-status">Slot Status</label>
                  <select id="edit-slot-status" v-model="editForm.status" class="form-select">
                    <option value="available">Available (Open)</option>
                    <option value="closed">Closed</option>
                    <option value="completed">Completed</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>
                <div class="col-6">
                  <label class="form-label" for="edit-slot-link">Meeting Link</label>
                  <input id="edit-slot-link" v-model="editForm.meeting_link" type="url" class="form-control" placeholder="https://..." />
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" @click="closeEditModal" class="btn btn-secondary">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="submitting">
                {{ submitting ? 'Saving Changes...' : 'Save & Reschedule' }}
              </button>
            </div>
          </form>
        </div>
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
const showEditModal = ref(false);

const form = reactive({
  exam_id: '',
  examiner_id: '',
  date: '',
  start_time: '10:00:00',
  end_time: '11:00:00',
  max_capacity: 5,
  meeting_link: ''
});

const editForm = reactive({
  id: null,
  examiner_id: '',
  date: '',
  start_time: '',
  end_time: '',
  max_capacity: 5,
  meeting_link: '',
  status: 'available'
});

const feedback = reactive({ text: '', isError: false });
const showFeedback = (text, isError = false) => {
  feedback.text = text;
  feedback.isError = isError;
  setTimeout(() => { feedback.text = ''; }, 5000);
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

const openEditSlotModal = (slot) => {
  editForm.id = slot.id;
  editForm.examiner_id = slot.examiner_id;
  editForm.date = slot.date;
  editForm.start_time = slot.start_time;
  editForm.end_time = slot.end_time;
  editForm.max_capacity = slot.max_capacity;
  editForm.meeting_link = slot.meeting_link || '';
  editForm.status = slot.status || 'available';
  showEditModal.value = true;
};

const closeEditModal = () => {
  showEditModal.value = false;
};

const createSlot = async () => {
  submitting.value = true;
  try {
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

const saveSlotEdit = async () => {
  submitting.value = true;
  try {
    let st = editForm.start_time;
    if (st.split(':').length === 2) st += ':00';
    let et = editForm.end_time;
    if (et.split(':').length === 2) et += ':00';

    const res = await api.put(`/api/admin/slots/${editForm.id}`, {
      examiner_id: parseInt(editForm.examiner_id),
      date: editForm.date,
      start_time: st,
      end_time: et,
      max_capacity: parseInt(editForm.max_capacity),
      meeting_link: editForm.meeting_link,
      status: editForm.status
    });

    showFeedback(res.message || 'Slot updated successfully.');
    closeEditModal();
    loadSlots(selectedExamId.value);
  } catch (err) {
    showFeedback(err.message || 'Failed to update slot.', true);
  } finally {
    submitting.value = false;
  }
};

const toggleSlotBooking = async (slot) => {
  try {
    const res = await api.post(`/api/admin/slots/${slot.id}/toggle-booking`, {});
    slot.status = res.status;
    showFeedback(res.message || 'Slot booking status toggled.');
  } catch (err) {
    showFeedback(err.message || 'Failed to toggle slot booking.', true);
  }
};

const deleteSlot = async (slotId) => {
  if (!confirm('Are you sure you want to delete this slot?')) return;
  try {
    await api.delete(`/api/admin/slots/${slotId}`);
    showFeedback('Slot deleted.');
    loadSlots(selectedExamId.value);
  } catch (err) {
    showFeedback(err.message || 'Error deleting slot.', true);
  }
};

onMounted(() => {
  loadInitial();
});
</script>

<style scoped>
.modal-backdrop {
  z-index: 1040;
}
.modal {
  z-index: 1050;
  background: rgba(0, 0, 0, 0.4);
}
</style>
