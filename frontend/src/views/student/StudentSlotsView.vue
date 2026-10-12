<template>
  <div class="student-slots app-container">
    <div class="page-header">
      <div>
        <h1 class="page-title">Available Examination Slots</h1>
        <p class="page-subtitle">Browse open assessment time slots and reserve your examination seat</p>
      </div>
      <router-link to="/student/bookings" class="btn btn-secondary btn-sm">View My Bookings →</router-link>
    </div>

    <!-- Alert / Message -->
    <div v-if="feedback.text" :class="['alert', feedback.isError ? 'alert-error' : 'alert-success']">
      {{ feedback.text }}
    </div>

    <!-- Slots Table -->
    <div class="table-container glass-card">
      <div v-if="loading" class="table-empty">Finding available slots...</div>
      <div v-else-if="slots.length === 0" class="table-empty">
        No open examination slots available at the moment. Please check back later.
      </div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Course</th>
            <th>Examination</th>
            <th>Examiner</th>
            <th>Date</th>
            <th>Time Window</th>
            <th>Seats Left</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in slots" :key="s.id">
            <td><strong>{{ s.course_name || '—' }}</strong></td>
            <td>{{ s.exam_name }}</td>
            <td>{{ s.examiner_name ? `Prof. ${s.examiner_name}` : 'Faculty Examiner' }}</td>
            <td>{{ s.date }}</td>
            <td>{{ s.start_time }} – {{ s.end_time }}</td>
            <td>
              <span class="badge badge-success">{{ s.available_seats }} / {{ s.max_capacity }} seats</span>
            </td>
            <td>
              <button
                @click="bookSlot(s.id)"
                class="btn btn-primary btn-sm"
                :disabled="bookingSlotId === s.id"
              >
                {{ bookingSlotId === s.id ? 'Reserving...' : 'Book This Slot' }}
              </button>
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

const slots = ref([]);
const loading = ref(true);
const bookingSlotId = ref(null);

const feedback = reactive({ text: '', isError: false });
const showFeedback = (text, isError = false) => {
  feedback.text = text;
  feedback.isError = isError;
  setTimeout(() => { feedback.text = ''; }, 4000);
};

const loadSlots = async () => {
  loading.value = true;
  try {
    const data = await api.get('/api/student/slots');
    slots.value = data.slots || [];
  } catch (err) {
    showFeedback(err.message || 'Failed to load available slots.', true);
  } finally {
    loading.value = false;
  }
};

const bookSlot = async (slotId) => {
  if (!confirm('Confirm reservation for this examination slot?')) return;
  bookingSlotId.value = slotId;
  try {
    const res = await api.post('/api/student/slots', { slot_id: slotId });
    showFeedback(res.message || 'Slot successfully booked!');
    await loadSlots();
  } catch (err) {
    showFeedback(err.message || 'Unable to book this slot.', true);
  } finally {
    bookingSlotId.value = null;
  }
};

onMounted(() => {
  loadSlots();
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
