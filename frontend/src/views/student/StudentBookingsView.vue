<template>
  <div class="student-bookings app-container">
    <div class="page-header">
      <div>
        <h1 class="page-title">My Reserved Examination Slots</h1>
        <p class="page-subtitle">Track your upcoming viva sessions and access online meeting links</p>
      </div>
      <router-link to="/student/slots" class="btn btn-primary btn-sm">+ Book Another Slot</router-link>
    </div>

    <!-- Alert / Message -->
    <div v-if="feedback.text" :class="['alert', feedback.isError ? 'alert-error' : 'alert-success']">
      {{ feedback.text }}
    </div>

    <!-- Bookings Table -->
    <div class="table-container glass-card">
      <div v-if="loading" class="table-empty">Loading your bookings...</div>
      <div v-else-if="bookings.length === 0" class="table-empty">
        You haven't booked any examination slots yet.
        <router-link to="/student/slots" class="booking-cta">Browse available slots →</router-link>
      </div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Booking ID</th>
            <th>Course</th>
            <th>Examination</th>
            <th>Exam Date</th>
            <th>Timing</th>
            <th>Meeting Link</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="b in bookings" :key="b.id">
            <td>#{{ b.id }}</td>
            <td><strong>{{ b.course_name || '—' }}</strong></td>
            <td>{{ b.exam_name || 'Assessment' }}</td>
            <td>{{ b.date }}</td>
            <td>{{ b.start_time }} – {{ b.end_time }}</td>
            <td>
              <a v-if="b.meeting_link" :href="b.meeting_link" target="_blank" rel="noopener" class="meeting-btn">
                🎥 Join Meeting ↗
              </a>
              <span v-else class="text-faint">Will be provided</span>
            </td>
            <td>
              <span :class="['badge', b.status === 'completed' ? 'badge-success' : 'badge-student']">
                {{ b.status }}
              </span>
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
  setTimeout(() => { feedback.text = ''; }, 4000);
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

onMounted(() => {
  loadBookings();
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

.booking-cta {
  display: block;
  margin-top: 0.5rem;
  font-weight: 600;
}

.meeting-btn {
  display: inline-flex;
  align-items: center;
  padding: 0.35rem 0.75rem;
  background: rgba(56, 189, 248, 0.15);
  border: 1px solid rgba(56, 189, 248, 0.3);
  border-radius: var(--radius-sm);
  color: var(--info);
  font-weight: 500;
  font-size: 0.85rem;
}

.meeting-btn:hover {
  background: rgba(56, 189, 248, 0.25);
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
