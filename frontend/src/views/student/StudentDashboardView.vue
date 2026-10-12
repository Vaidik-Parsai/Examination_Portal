<template>
  <div class="student-dashboard app-container">
    <div class="page-header">
      <div>
        <h1 class="page-title">Student Candidate Portal</h1>
        <p class="page-subtitle">Track your examination schedule, book open viva slots, and access grading feedback</p>
      </div>
      <router-link to="/student/slots" class="btn btn-primary btn-sm">+ Book New Slot</router-link>
    </div>

    <!-- Alert / Message -->
    <div v-if="error" class="alert-error">
      {{ error }}
    </div>

    <!-- Stats Grid -->
    <div class="stats-grid">
      <div class="stat-card">
        <span class="stat-label">Total Reservations</span>
        <span class="stat-value">{{ stats.total_bookings || 0 }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Upcoming Vivas</span>
        <span class="stat-value">{{ stats.upcoming_exams || 0 }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Completed Assessments</span>
        <span class="stat-value">{{ stats.completed_exams || 0 }}</span>
      </div>
    </div>

    <!-- Quick Navigation Shortcuts -->
    <div class="glass-card nav-card">
      <h3>Quick Actions</h3>
      <p class="subtitle">Select an action to manage your examination journey</p>
      <div class="student-shortcuts">
        <router-link to="/student/slots" class="shortcut-box">
          <span class="shortcut-icon">🕒</span>
          <div>
            <strong>Browse & Book Slots</strong>
            <small>View open examination time slots and reserve a seat</small>
          </div>
        </router-link>

        <router-link to="/student/bookings" class="shortcut-box">
          <span class="shortcut-icon">📅</span>
          <div>
            <strong>My Reserved Bookings</strong>
            <small>Check your scheduled times and online video conference links</small>
          </div>
        </router-link>

        <router-link to="/student/evaluations" class="shortcut-box">
          <span class="shortcut-icon">🏆</span>
          <div>
            <strong>Evaluation Results</strong>
            <small>Review marks awarded and feedback remarks from examiners</small>
          </div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { api } from '../../services/api';

const stats = ref({});
const error = ref('');

const loadDashboard = async () => {
  try {
    const data = await api.get('/api/student/dashboard');
    stats.value = data.stats || {};
  } catch (err) {
    error.value = err.message || 'Error loading student dashboard.';
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

.subtitle {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
}

.student-shortcuts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.25rem;
}

.shortcut-box {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-subtle);
  transition: var(--transition);
}

.shortcut-box:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--border-glow);
  transform: translateY(-2px);
}

.shortcut-icon {
  font-size: 2rem;
}

.shortcut-box strong {
  display: block;
  color: var(--text-main);
  font-size: 1.05rem;
}

.shortcut-box small {
  color: var(--text-muted);
}

.alert-error {
  background: var(--danger-bg);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #fca5a5;
  padding: 1rem;
  border-radius: var(--radius-md);
  margin-bottom: 1.5rem;
}
</style>
