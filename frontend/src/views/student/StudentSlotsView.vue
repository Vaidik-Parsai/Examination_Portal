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

    <!-- Search / Filter Bar -->
    <div class="simple-card filter-bar">
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Search by Examiner Name</label>
          <input v-model="filterExaminer" type="text" class="form-input" placeholder="e.g. Dr. Sharma" />
        </div>
        <div class="form-group">
          <label class="form-label">Search by Subject / Exam</label>
          <input v-model="filterSubject" type="text" class="form-input" placeholder="e.g. Data Structures" />
        </div>
        <div class="form-group filter-action">
          <button @click="applyFilter" class="btn btn-primary">Search</button>
          <button @click="clearFilter" class="btn btn-secondary">Clear</button>
        </div>
      </div>
    </div>

    <!-- Slots Table -->
    <div class="simple-card table-container">
      <div v-if="loading" class="table-empty">Finding available slots...</div>
      <div v-else-if="filteredSlots.length === 0" class="table-empty">
        No open examination slots found. Try different filters or check back later.
      </div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Course</th>
            <th>Examination</th>
            <th>Examiner</th>
            <th>Department</th>
            <th>Date</th>
            <th>Time</th>
            <th>Seats Left</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in filteredSlots" :key="s.id">
            <td><strong>{{ s.course_name || '—' }}</strong></td>
            <td>{{ s.exam_name }}</td>
            <td>{{ s.examiner_name ? `Prof. ${s.examiner_name}` : 'Faculty Examiner' }}</td>
            <td>{{ s.examiner_department || '—' }}</td>
            <td>{{ s.date }}</td>
            <td>{{ s.start_time }} – {{ s.end_time }}</td>
            <td>
              <span class="badge badge-success">{{ s.available_seats }} / {{ s.max_capacity }}</span>
            </td>
            <td>
              <button
                @click="bookSlot(s.id)"
                class="btn btn-primary btn-sm"
                :disabled="bookingSlotId === s.id"
              >
                {{ bookingSlotId === s.id ? 'Reserving...' : 'Book Slot' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { api } from '../../services/api';

const slots = ref([]);
const loading = ref(true);
const bookingSlotId = ref(null);
const filterExaminer = ref('');
const filterSubject = ref('');
const activeExaminer = ref('');
const activeSubject = ref('');

const feedback = reactive({ text: '', isError: false });
const showFeedback = (text, isError = false) => {
  feedback.text = text;
  feedback.isError = isError;
  setTimeout(() => { feedback.text = ''; }, 5000);
};

const filteredSlots = computed(() => {
  if (!activeExaminer.value && !activeSubject.value) return slots.value;
  const eq = activeExaminer.value.toLowerCase();
  const sq = activeSubject.value.toLowerCase();
  return slots.value.filter(s => {
    const matchEx = !eq || (s.examiner_name || '').toLowerCase().includes(eq);
    const matchSub = !sq ||
      (s.exam_name || '').toLowerCase().includes(sq) ||
      (s.course_name || '').toLowerCase().includes(sq);
    return matchEx && matchSub;
  });
});

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

const applyFilter = () => {
  activeExaminer.value = filterExaminer.value.trim();
  activeSubject.value = filterSubject.value.trim();
};

const clearFilter = () => {
  filterExaminer.value = '';
  filterSubject.value = '';
  activeExaminer.value = '';
  activeSubject.value = '';
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

onMounted(() => { loadSlots(); });
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

.filter-bar { margin-bottom: 1rem; }

.filter-action {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.table-empty { text-align: center; padding: 3rem; color: #6c757d; }
</style>
