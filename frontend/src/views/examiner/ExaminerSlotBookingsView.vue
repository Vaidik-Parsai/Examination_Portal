<template>
  <div class="slot-bookings app-container">
    <div class="page-header">
      <div>
        <router-link to="/examiner/dashboard" class="back-link">← Back to Examiner Hub</router-link>
        <h1 class="page-title">Candidate Evaluation: Slot #{{ slotId }}</h1>
        <p class="page-subtitle">Review enrolled students, conduct assessments, and submit viva marks & remarks</p>
      </div>
    </div>

    <!-- Alert / Message -->
    <div v-if="feedback.text" :class="['alert', feedback.isError ? 'alert-error' : 'alert-success']">
      {{ feedback.text }}
    </div>

    <!-- Bookings Table -->
    <div class="table-container glass-card">
      <div v-if="loading" class="table-empty">Loading candidate bookings...</div>
      <div v-else-if="bookings.length === 0" class="table-empty">No students have booked this examination slot yet.</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Booking ID</th>
            <th>Candidate Name</th>
            <th>Email</th>
            <th>Booked At</th>
            <th>Status</th>
            <th>Total Marks</th>
            <th>Remarks</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="b in bookings" :key="b.booking_id">
            <td>#{{ b.booking_id }}</td>
            <td><strong>{{ b.student_name }}</strong></td>
            <td>{{ b.student_email || '—' }}</td>
            <td>{{ b.booking_date ? b.booking_date.split('T')[0] : '—' }}</td>
            <td>
              <span :class="['badge', b.evaluation ? 'badge-success' : 'badge-warning']">
                {{ b.evaluation ? 'Evaluated' : 'Pending Grading' }}
              </span>
            </td>
            <td>
              <strong v-if="b.evaluation">{{ b.evaluation.total_marks }} pts</strong>
              <span v-else class="text-faint">—</span>
            </td>
            <td>
              <span v-if="b.evaluation">{{ b.evaluation.remarks || 'No remarks' }}</span>
              <span v-else class="text-faint">—</span>
            </td>
            <td>
              <button @click="openGradingModal(b)" class="btn btn-primary btn-sm">
                {{ b.evaluation ? 'Update Grade' : 'Grade Candidate' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Grade Modal -->
    <div v-if="showGradeModal" class="modal-overlay" @click.self="closeGradeModal">
      <div class="modal-content">
        <h3>Evaluate Candidate</h3>
        <p class="subtitle">Assign viva marks and assessment feedback for <strong>{{ activeBooking?.student_name }}</strong></p>
        <form @submit.prevent="submitGrade" class="modal-form">
          <div class="form-group">
            <label class="form-label" for="grade-marks">Total Marks Awarded</label>
            <input
              id="grade-marks"
              v-model="gradeForm.total_marks"
              type="number"
              min="0"
              class="form-input"
              placeholder="e.g. 85"
              required
            />
          </div>

          <div class="form-group">
            <label class="form-label" for="grade-remarks">Examiner Remarks & Feedback</label>
            <textarea
              id="grade-remarks"
              v-model="gradeForm.remarks"
              rows="3"
              class="form-textarea"
              placeholder="Strong conceptual clarity, well structured answer on algorithms..."
            ></textarea>
          </div>

          <div class="modal-actions">
            <button type="button" @click="closeGradeModal" class="btn btn-secondary">Cancel</button>
            <button type="submit" class="btn btn-primary" :disabled="submitting">
              {{ submitting ? 'Saving...' : 'Submit Evaluation' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { api } from '../../services/api';

const route = useRoute();
const slotId = route.params.slotId;

const bookings = ref([]);
const loading = ref(true);
const submitting = ref(false);

const showGradeModal = ref(false);
const activeBooking = ref(null);

const gradeForm = reactive({
  total_marks: '',
  remarks: ''
});

const feedback = reactive({ text: '', isError: false });
const showFeedback = (text, isError = false) => {
  feedback.text = text;
  feedback.isError = isError;
  setTimeout(() => { feedback.text = ''; }, 4000);
};

const loadBookings = async () => {
  loading.value = true;
  try {
    const data = await api.get(`/api/examiner/slots/${slotId}/bookings`);
    bookings.value = data.bookings || [];
  } catch (err) {
    showFeedback(err.message || 'Error loading slot candidate bookings.', true);
  } finally {
    loading.value = false;
  }
};

const openGradingModal = (booking) => {
  activeBooking.value = booking;
  gradeForm.total_marks = booking.evaluation ? booking.evaluation.total_marks : '';
  gradeForm.remarks = booking.evaluation ? booking.evaluation.remarks : '';
  showGradeModal.value = true;
};

const closeGradeModal = () => {
  showGradeModal.value = false;
  activeBooking.value = null;
};

const submitGrade = async () => {
  submitting.value = true;
  try {
    await api.post('/api/examiner/evaluations', {
      booking_id: activeBooking.value.booking_id,
      total_marks: parseInt(gradeForm.total_marks),
      remarks: gradeForm.remarks
    });

    showFeedback(`Evaluation saved for ${activeBooking.value.student_name}.`);
    closeGradeModal();
    loadBookings();
  } catch (err) {
    showFeedback(err.message || 'Failed to submit evaluation grade.', true);
  } finally {
    submitting.value = false;
  }
};

onMounted(() => {
  loadBookings();
});
</script>

<style scoped>
.page-header {
  margin-bottom: 2rem;
}

.back-link {
  display: inline-block;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: var(--text-muted);
}

.back-link:hover {
  color: var(--primary);
}

.subtitle {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-bottom: 1.25rem;
}

.table-empty {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
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
