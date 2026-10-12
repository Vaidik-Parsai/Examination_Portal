<template>
  <div class="admin-dashboard app-container">
    <div class="page-header">
      <div>
        <h1 class="page-title">Admin Dashboard</h1>
        <p class="page-subtitle">Central oversight of courses, examinations, examiners, and system jobs</p>
      </div>
      <div class="header-actions">
        <router-link to="/admin/courses" class="btn btn-secondary btn-sm">+ Course</router-link>
        <router-link to="/admin/exams" class="btn btn-secondary btn-sm">+ Exam</router-link>
        <router-link to="/admin/slots" class="btn btn-primary btn-sm">+ Slot</router-link>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state glass-card">
      <p>Loading dashboard metrics...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="alert-error">
      {{ error }}
    </div>

    <!-- Metrics Grid -->
    <div v-else class="stats-grid">
      <div class="stat-card">
        <span class="stat-label">Total Courses</span>
        <span class="stat-value">{{ stats.total_courses || 0 }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Examinations</span>
        <span class="stat-value">{{ stats.total_exams || 0 }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Active Examiners</span>
        <span class="stat-value">{{ stats.total_examiners || 0 }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Registered Students</span>
        <span class="stat-value">{{ stats.total_students || 0 }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Total Bookings</span>
        <span class="stat-value">{{ stats.total_bookings || 0 }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Pending Evaluations</span>
        <span class="stat-value">{{ stats.pending_evaluations || 0 }}</span>
      </div>
    </div>

    <!-- Quick Navigation Panels -->
    <div class="dashboard-panels">
      <div class="glass-card panel-card">
        <h3>Administrative Modules</h3>
        <p>Direct access to manage portal entities and configuration.</p>
        <div class="module-links">
          <router-link to="/admin/courses" class="module-link">
            <span class="module-icon">📚</span>
            <div>
              <strong>Courses</strong>
              <small>Create and edit academic course codes</small>
            </div>
          </router-link>
          <router-link to="/admin/exams" class="module-link">
            <span class="module-icon">📝</span>
            <div>
              <strong>Examinations & Rubrics</strong>
              <small>Configure duration, windows, and scoring rubrics</small>
            </div>
          </router-link>
          <router-link to="/admin/slots" class="module-link">
            <span class="module-icon">🕒</span>
            <div>
              <strong>Slot Allocations</strong>
              <small>Generate and monitor viva exam slots</small>
            </div>
          </router-link>
          <router-link to="/admin/examiners" class="module-link">
            <span class="module-icon">👨‍🏫</span>
            <div>
              <strong>Examiners</strong>
              <small>Provision examiner accounts and departments</small>
            </div>
          </router-link>
          <router-link to="/admin/tasks" class="module-link">
            <span class="module-icon">⚡</span>
            <div>
              <strong>Celery Tasks & Reports</strong>
              <small>Trigger reminders, daily report, and async CSV exports</small>
            </div>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { api } from '../../services/api';

const stats = ref({});
const loading = ref(true);
const error = ref('');

const loadDashboard = async () => {
  loading.value = true;
  error.value = '';
  try {
    const data = await api.get('/api/admin/dashboard');
    stats.value = data.stats || {};
  } catch (err) {
    error.value = err.message || 'Failed to load dashboard metrics.';
  } finally {
    loading.value = false;
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

.page-title {
  font-size: 2.2rem;
}

.page-subtitle {
  color: var(--text-muted);
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.loading-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
}

.alert-error {
  background: var(--danger-bg);
  border: 1px solid rgba(239, 68, 68, 0.35);
  color: #fca5a5;
  padding: 1rem;
  border-radius: var(--radius-md);
  margin-bottom: 1.5rem;
}

.module-links {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1rem;
  margin-top: 1.5rem;
}

.module-link {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-subtle);
  transition: var(--transition);
}

.module-link:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--border-glow);
  transform: translateY(-2px);
}

.module-icon {
  font-size: 1.8rem;
}

.module-link strong {
  display: block;
  color: var(--text-main);
}

.module-link small {
  color: var(--text-muted);
}
</style>
