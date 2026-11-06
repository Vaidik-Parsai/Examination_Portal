<template>
  <div class="student-bookings app-container">
    <div class="page-header">
      <div>
        <h1 class="page-title">My Reserved Examination Slots</h1>
        <p class="page-subtitle">Track your upcoming viva sessions and access meeting links</p>
      </div>
      <router-link to="/student/slots" class="btn btn-primary btn-sm">+ Book Another Slot</router-link>
    </div>

    <!-- Alert / Message -->
    <div v-if="feedback.text" :class="['alert', feedback.isError ? 'alert-error' : 'alert-success']">
      {{ feedback.text }}
    </div>

    <!-- Bookings Table -->
    <div class="simple-card table-container">
      <div v-if="loading" class="table-empty">Loading your bookings...</div>
      <div v-else-if="bookings.length === 0" class="table-empty">
        You haven't booked any examination slots yet.
        <router-link to="/student/slots" style="display:block; margin-top:8px; font-weight:600;">Browse available slots →</router-link>
      </div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Course</th>
            <th>Examination</th>
            <th>Exam Date</th>
            <th>Time</th>
            <th>Meeting Link</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="b in bookings" :key="b.id">
            <td>#{{ b.id }}</td>
            <td><strong>{{ b.course_name || '—' }}</strong></td>
            <td>{{ b.exam_name || 'Assessment' }}</td>
            <td>{{ b.date || '—' }}</td>
            <td>{{ b.start_time }} – {{ b.end_time }}</td>
            <td>
              <a v-if="b.meeting_link" :href="b.meeting_link" target="_blank" rel="noopener" class="btn btn-secondary btn-sm">
                🎥 Join
              </a>
              <span v-else class="text-muted">TBD</span>
            </td>
            <td>
              <span :class="['badge', statusBadge(b.status)]">{{ b.status }}</span>
              <div v-if="b.reschedule_notice" class="reschedule-notice">
                📌 {{ b.reschedule_notice }}
              </div>
            </td>
            <td>
              <router-link v-if="b.status === 'completed'" to="/student/evaluations" class="btn btn-secondary btn-sm">
                View Result
              </router-link>
              <div v-else-if="b.status === 'booked'">
                <button
                  v-if="b.can_cancel"
                  @click="cancelBooking(b.id)"
                  class="btn btn-danger btn-sm"
                  title="Cancel this booking"
                >Cancel</button>
                <span v-else class="text-muted small" :title="b.cancel_deadline_msg">⏱ Deadline passed</span>
              </div>
              <span v-else class="text-muted">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { api } from '../../services/api';

const bookings = ref([]);
const loading = ref(true);

const feedback = reactive({ text: '', isError: false });
const showFeedback = (text, isError = false) => {
  feedback.text = text;
  feedback.isError = isError;
  setTimeout(() => { feedback.text = ''; }, 5000);
};

const statusBadge = (status) => {
  if (status === 'completed') return 'badge-success';
  if (status === 'cancelled') return 'badge-danger';
  if (status === 'rescheduled') return 'badge-warning';
  return 'badge-student';
};

const loadBookings = async () => {
  loading.value = true;
  try {
    const data = await api.get('/api/student/bookings');
    bookings.value = data.bookings || [];
  } catch (err) {
    showFeedback(err.message || 'Failed to load bookings.', true);
  } finally {
    loading.value = false;
  }
};

const cancelBooking = async (bookingId) => {
  if (!confirm('Are you sure you want to cancel this booking? The seat will be released back.')) return;
  try {
    const res = await api.delete(`/api/student/bookings/${bookingId}/cancel`);
    showFeedback(res.message || 'Booking cancelled.');
    loadBookings();
  } catch (err) {
    showFeedback(err.message || 'Failed to cancel booking.', true);
  }
};

onMounted(() => { loadBookings(); });
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
.table-empty { text-align: center; padding: 3rem; color: #6c757d; }

.reschedule-notice {
  margin-top: 4px;
  font-size: 11px;
  color: #664d03;
  background: #fff3cd;
  padding: 2px 6px;
  border-radius: 3px;
}

.badge-danger { background-color: #f8d7da; color: #842029; }
</style>
