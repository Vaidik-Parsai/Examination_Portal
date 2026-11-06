<template>
  <div class="admin-tasks app-container">
    <div class="page-header">
      <div>
        <h1 class="page-title">Celery Tasks & Asynchronous Exports</h1>
        <p class="page-subtitle">Trigger automated reminders, compile daily activity reports, and export exam score sheets</p>
      </div>
    </div>

    <!-- Alert / Message -->
    <div v-if="feedback.text" :class="['alert', feedback.isError ? 'alert-error' : 'alert-success']">
      {{ feedback.text }}
    </div>

    <div class="tasks-grid">
      <!-- Background Tasks Panel -->
      <div class="glass-card task-card">
        <div class="card-icon">⚡</div>
        <h3>Celery Background Tasks</h3>
        <p>Trigger automated scheduled operations on demand via worker queues.</p>

        <div class="task-action-box">
          <div>
            <strong>1. Automated Slot Reminders</strong>
            <p class="text-muted">Scans for viva slots occurring within the next 24 hours and dispatches reminders to booked students and examiners.</p>
          </div>
          <button @click="triggerTask('reminders')" class="btn btn-primary btn-sm" :disabled="triggeringReminders">
            {{ triggeringReminders ? 'Dispatching...' : 'Dispatch Reminders Now' }}
          </button>
        </div>

        <div class="task-action-box">
          <div>
            <strong>2. Daily Activity Summary Report</strong>
            <p class="text-muted">Calculates total bookings, exams taken, and pending evaluations today, storing structured JSON metrics.</p>
          </div>
          <button @click="triggerTask('daily-report')" class="btn btn-secondary btn-sm" :disabled="triggeringReport">
            {{ triggeringReport ? 'Generating...' : 'Compile Daily Report' }}
          </button>
        </div>

        <div class="task-action-box">
          <div>
            <strong>3. Monthly Examination Report</strong>
            <p class="text-muted">Compiles the previous month's statistics (exams conducted, students evaluated, top examiners) and emails the report to the admin. Use year/month fields to test a specific month.</p>
            <div style="display:flex; gap:8px; margin-top:8px; flex-wrap:wrap;">
              <div class="form-group" style="margin:0;">
                <label class="form-label">Year (optional)</label>
                <input v-model="monthlyYear" type="number" min="2020" max="2100" class="form-input" style="width:100px;" placeholder="e.g. 2026" />
              </div>
              <div class="form-group" style="margin:0;">
                <label class="form-label">Month (optional)</label>
                <input v-model="monthlyMonth" type="number" min="1" max="12" class="form-input" style="width:80px;" placeholder="1–12" />
              </div>
            </div>
          </div>
          <button @click="triggerMonthlyReport" class="btn btn-primary btn-sm" :disabled="triggeringMonthly">
            {{ triggeringMonthly ? 'Generating...' : 'Generate Monthly Report' }}
          </button>
        </div>

        <!-- Task Log Output -->
        <div v-if="lastTaskResult" class="alert alert-info py-2 px-3 mt-3">
          <div class="fw-bold mb-1">Execution Status: {{ lastTaskResult.status || 'Completed' }}</div>
          <div v-if="lastTaskResult.message" class="small">{{ lastTaskResult.message }}</div>
          <div v-if="lastTaskResult.reminders_sent !== undefined" class="small">
            Checked {{ lastTaskResult.slots_checked || 0 }} slots, sent {{ lastTaskResult.reminders_sent }} reminders.
          </div>
          <div v-if="lastTaskResult.slots_scheduled_today !== undefined" class="small">
            Report date: {{ lastTaskResult.date }} | Scheduled slots: {{ lastTaskResult.slots_scheduled_today }} | Evaluations: {{ lastTaskResult.evaluations_completed_today }}
          </div>
        </div>
      </div>

      <!-- CSV Export Panel -->
      <div class="glass-card task-card">
        <div class="card-icon">📊</div>
        <h3>Examination CSV Data Export</h3>
        <p>Generate downloadable spreadsheet records for student evaluations, scores, and rubrics.</p>

        <div class="form-group">
          <label class="form-label" for="export-exam-select">Select Examination to Export:</label>
          <select id="export-exam-select" v-model="selectedExamId" @change="loadExports" class="form-select">
            <option value="" disabled>Select Examination</option>
            <option v-for="e in exams" :key="e.id" :value="e.id">
              {{ e.name }} ({{ e.course_name }})
            </option>
          </select>
        </div>

        <button @click="triggerExport" class="btn btn-primary" :disabled="exporting || !selectedExamId">
          {{ exporting ? 'Generating Export...' : 'Generate Results CSV' }}
        </button>

        <!-- Existing Exports List -->
        <div class="exports-list-section">
          <h4>Generated Export Files:</h4>
          <div v-if="loadingExports" class="text-muted">Checking export archive...</div>
          <div v-else-if="exportFiles.length === 0" class="text-muted">No exports generated for this examination yet.</div>
          <ul v-else class="exports-list">
            <li v-for="file in exportFiles" :key="file" class="export-item">
              <span class="file-name">📄 {{ file }}</span>
              <a :href="`/api/admin/exams/${selectedExamId}/export?download=true`" target="_blank" class="btn btn-secondary btn-sm">
                Download CSV ↓
              </a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { api } from '../../services/api';

const exams = ref([]);
const selectedExamId = ref('');
const exportFiles = ref([]);
const lastTaskResult = ref(null);

const triggeringReminders = ref(false);
const triggeringReport = ref(false);
const triggeringMonthly = ref(false);
const exporting = ref(false);
const loadingExports = ref(false);
const monthlyYear = ref('');
const monthlyMonth = ref('');

const feedback = reactive({ text: '', isError: false });
const showFeedback = (text, isError = false) => {
  feedback.text = text;
  feedback.isError = isError;
  setTimeout(() => { feedback.text = ''; }, 4000);
};

const loadInitial = async () => {
  try {
    const data = await api.get('/api/admin/exams');
    exams.value = data.exams || [];
    if (exams.value.length > 0) {
      selectedExamId.value = exams.value[0].id;
      loadExports();
    }
  } catch (err) {
    showFeedback('Error loading exams.', true);
  }
};

const triggerTask = async (taskName) => {
  if (taskName === 'reminders') triggeringReminders.value = true;
  if (taskName === 'daily-report') triggeringReport.value = true;

  try {
    const res = await api.post(`/api/admin/tasks/${taskName}`, {});
    lastTaskResult.value = res.result || res;
    showFeedback(res.message || 'Task initiated successfully.');
  } catch (err) {
    showFeedback(err.message || 'Task execution failed.', true);
  } finally {
    triggeringReminders.value = false;
    triggeringReport.value = false;
  }
};

const loadExports = async () => {
  if (!selectedExamId.value) return;
  loadingExports.value = true;
  try {
    const data = await api.get(`/api/admin/exams/${selectedExamId.value}/export`);
    exportFiles.value = data.exports || [];
  } catch (err) {
    console.error('Failed to load exports list', err);
  } finally {
    loadingExports.value = false;
  }
};

const triggerExport = async () => {
  if (!selectedExamId.value) return;
  exporting.value = true;
  try {
    const res = await api.post(`/api/admin/exams/${selectedExamId.value}/export`, {});
    showFeedback(res.message || 'CSV Export job completed.');
    await loadExports();
  } catch (err) {
    showFeedback(err.message || 'Export failed.', true);
  } finally {
    exporting.value = false;
  }
};

const triggerMonthlyReport = async () => {
  triggeringMonthly.value = true;
  try {
    let url = '/api/admin/tasks/monthly-report';
    const params = [];
    if (monthlyYear.value) params.push(`year=${monthlyYear.value}`);
    if (monthlyMonth.value) params.push(`month=${monthlyMonth.value}`);
    if (params.length) url += '?' + params.join('&');
    const res = await api.post(url, {});
    lastTaskResult.value = res.result || res;
    showFeedback(res.message || 'Monthly report generated successfully.');
  } catch (err) {
    showFeedback(err.message || 'Monthly report task failed.', true);
  } finally {
    triggeringMonthly.value = false;
  }
};

onMounted(() => {
  loadInitial();
});
</script>

<style scoped>
.page-header {
  margin-bottom: 2rem;
}

.tasks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
  gap: 1.75rem;
}

.task-card {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.card-icon {
  font-size: 2.2rem;
}

.task-action-box {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.task-log-box {
  background: #080c14;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 1rem;
  font-size: 0.825rem;
  overflow-x: auto;
}

.task-log-box pre {
  margin-top: 0.5rem;
  color: #38bdf8;
}

.exports-list-section {
  border-top: 1px solid var(--border-subtle);
  padding-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.exports-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.export-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.65rem 0.85rem;
  background: rgba(255, 255, 255, 0.03);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
}

.file-name {
  font-size: 0.85rem;
  color: var(--text-main);
  word-break: break-all;
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
