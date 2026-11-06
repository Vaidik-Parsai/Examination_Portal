<template>
  <div class="slot-bookings app-container">
    <div class="page-header">
      <div>
        <router-link to="/examiner/dashboard" class="back-link">← Back to Examiner Hub</router-link>
        <h1 class="page-title">Candidate Evaluation: Slot #{{ slotId }}</h1>
        <p class="page-subtitle">Review enrolled students, record viva marks and remarks</p>
      </div>
    </div>

    <!-- Alert / Message -->
    <div v-if="feedback.text" :class="['alert', feedback.isError ? 'alert-error' : 'alert-success']">
      {{ feedback.text }}
    </div>

    <!-- Slot & Exam Info -->
    <div v-if="slotInfo" class="simple-card mb-3">
      <h3>{{ slotInfo.exam_name }} &nbsp;<small class="text-muted">{{ slotInfo.course_name }}</small></h3>
      <p class="text-muted">
        Date: <strong>{{ slotInfo.date }}</strong> &nbsp;|&nbsp;
        Time: <strong>{{ slotInfo.start_time }} – {{ slotInfo.end_time }}</strong> &nbsp;|&nbsp;
        Max Marks: <strong>{{ slotInfo.max_marks }}</strong>
        <span v-if="slotInfo.meeting_link">
          &nbsp;|&nbsp; <a :href="slotInfo.meeting_link" target="_blank" rel="noopener">Join Meeting ↗</a>
        </span>
      </p>
    </div>

    <!-- Rubrics Panel -->
    <div v-if="rubrics.length" class="simple-card rubrics-panel mb-3">
      <h4>Evaluation Rubrics</h4>
      <table class="data-table">
        <thead>
          <tr>
            <th>Criterion</th>
            <th>Max Marks</th>
            <th>Weightage (%)</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rubrics" :key="r.id">
            <td><strong>{{ r.criterion_name }}</strong></td>
            <td>{{ r.max_marks ?? '—' }}</td>
            <td>{{ r.weightage != null ? r.weightage + '%' : '—' }}</td>
            <td>{{ r.description || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else-if="!loading" class="alert alert-warning mb-3">
      No rubrics defined for this examination. Contact the admin to add evaluation criteria.
    </div>

    <!-- Bookings Table -->
    <div class="table-container simple-card">
      <div v-if="loading" class="table-empty">Loading candidate bookings...</div>
      <div v-else-if="bookings.length === 0" class="table-empty">No students have booked this examination slot yet.</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Booking ID</th>
            <th>Candidate</th>
            <th>Email</th>
            <th>Booked On</th>
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
                {{ b.evaluation ? 'Evaluated' : 'Pending' }}
              </span>
            </td>
            <td>
              <strong v-if="b.evaluation">{{ b.evaluation.total_marks }} / {{ slotInfo?.max_marks || '?' }}</strong>
              <span v-else class="text-muted">—</span>
            </td>
            <td>
              <span v-if="b.evaluation">{{ b.evaluation.remarks || 'No remarks' }}</span>
              <span v-else class="text-muted">—</span>
            </td>
            <td>
              <button @click="openGradingModal(b)" class="btn btn-primary btn-sm">
                {{ b.evaluation ? 'Update Grade' : 'Grade' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Grade Modal -->
    <div v-if="showGradeModal" class="modal-overlay" @click.self="closeGradeModal">
      <div class="modal-content">
        <h3>Evaluate: {{ activeBooking?.student_name }}</h3>
        <p class="text-muted" style="margin-bottom:12px; font-size:13px;">
          Max marks: <strong>{{ slotInfo?.max_marks || '?' }}</strong>
        </p>

        <!-- Rubrics quick-reference in modal -->
        <div v-if="rubrics.length" class="rubric-ref">
          <strong>Rubrics reference:</strong>
          <ul>
            <li v-for="r in rubrics" :key="r.id">
              <span>{{ r.criterion_name }}</span>
              <span v-if="r.max_marks"> — {{ r.max_marks }} pts</span>
              <span v-if="r.weightage"> ({{ r.weightage }}%)</span>
            </li>
          </ul>
        </div>

        <form @submit.prevent="submitGrade">
          <div class="form-group">
            <label class="form-label" for="grade-marks">Total Marks Awarded</label>
            <input
              id="grade-marks"
              v-model="gradeForm.total_marks"
              type="number"
              min="0"
              :max="slotInfo?.max_marks || undefined"
              class="form-input"
              placeholder="e.g. 85"
              required
            />
          </div>

          <div class="form-group">
            <label class="form-label" for="grade-remarks">Examiner Remarks</label>
            <textarea
              id="grade-remarks"
              v-model="gradeForm.remarks"
              rows="3"
              class="form-textarea"
              placeholder="Strong conceptual clarity, well structured..."
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
const rubrics = ref([]);
const slotInfo = ref(null);
const loading = ref(true);
const submitting = ref(false);

const showGradeModal = ref(false);
const activeBooking = ref(null);
const gradeForm = reactive({ total_marks: '', remarks: '' });

const feedback = reactive({ text: '', isError: false });
const showFeedback = (text, isError = false) => {
  feedback.text = text;
  feedback.isError = isError;
  setTimeout(() => { feedback.text = ''; }, 5000);
};

const loadBookings = async () => {
  loading.value = true;
  try {
    const data = await api.get(`/api/examiner/slots/${slotId}/bookings`);
    bookings.value = data.bookings || [];
    rubrics.value = data.rubrics || [];
    slotInfo.value = data.slot || null;
  } catch (err) {
    showFeedback(err.message || 'Error loading slot data.', true);
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
    showFeedback(err.message || 'Failed to submit evaluation.', true);
  } finally {
    submitting.value = false;
  }
};

onMounted(() => {
  loadBookings();
});
</script>

<style scoped>
.page-header { margin-bottom: 1.5rem; }
.back-link { display: inline-block; margin-bottom: 0.5rem; font-size: 13px; color: #6c757d; }
.back-link:hover { color: #0d6efd; }
.mb-3 { margin-bottom: 1rem; }
.text-muted { color: #6c757d; }

.rubrics-panel h4 { margin-bottom: 0.75rem; font-size: 15px; }

.table-empty { text-align: center; padding: 3rem; color: #6c757d; }

.rubric-ref {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 10px 14px;
  margin-bottom: 14px;
  font-size: 13px;
}
.rubric-ref ul { margin: 6px 0 0 16px; }
.rubric-ref li { margin-bottom: 3px; }

.alert-warning {
  background-color: #fff3cd;
  border: 1px solid #ffc107;
  color: #664d03;
  padding: 10px 14px;
  border-radius: 4px;
}
</style>
