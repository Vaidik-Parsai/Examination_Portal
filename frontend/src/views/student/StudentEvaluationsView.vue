<template>
  <div class="student-evaluations app-container">
    <div class="page-header">
      <div>
        <h1 class="page-title">Assessment Results & Grading</h1>
        <p class="page-subtitle">View finalized scores, rubric grades, and feedback remarks from examiners</p>
      </div>
      <router-link to="/student/dashboard" class="btn btn-secondary btn-sm">← Dashboard</router-link>
    </div>

    <!-- Alert / Message -->
    <div v-if="feedback.text" :class="['alert', feedback.isError ? 'alert-error' : 'alert-success']">
      {{ feedback.text }}
    </div>

    <!-- Evaluations Table -->
    <div class="table-container glass-card">
      <div v-if="loading" class="table-empty">Loading examination results...</div>
      <div v-else-if="evaluations.length === 0" class="table-empty">
        No evaluation results published yet. Check back once your scheduled viva is completed.
      </div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Assessment</th>
            <th>Examiner</th>
            <th>Marks Scored</th>
            <th>Examiner Feedback & Remarks</th>
            <th>Date Evaluated</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in evaluations" :key="e.id">
            <td><strong>{{ e.exam_name || `Booking #${e.booking_id}` }}</strong></td>
            <td>{{ e.examiner_name ? `Prof. ${e.examiner_name}` : `Examiner #${e.examiner_id}` }}</td>
            <td>
              <span class="marks-pill">{{ e.total_marks }} pts</span>
            </td>
            <td>
              <div class="remarks-cell">
                {{ e.remarks || 'No detailed remarks recorded.' }}
              </div>
            </td>
            <td>{{ e.evaluation_date ? e.evaluation_date.split('T')[0] : '—' }}</td>
            <td>
              <span class="badge badge-success">{{ e.status }}</span>
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

const evaluations = ref([]);
const loading = ref(true);

const feedback = reactive({ text: '', isError: false });
const showFeedback = (text, isError = false) => {
  feedback.text = text;
  feedback.isError = isError;
  setTimeout(() => { feedback.text = ''; }, 4000);
};

const loadEvaluations = async () => {
  loading.value = true;
  try {
    const data = await api.get('/api/student/evaluations');
    evaluations.value = data.evaluations || [];
  } catch (err) {
    showFeedback(err.message || 'Failed to fetch examination results.', true);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadEvaluations();
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

.marks-pill {
  display: inline-block;
  padding: 0.35rem 0.85rem;
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.35);
  color: #6ee7b7;
  font-weight: 700;
  border-radius: var(--radius-full);
  font-size: 0.95rem;
}

.remarks-cell {
  max-width: 320px;
  color: var(--text-muted);
  line-height: 1.4;
  font-size: 0.9rem;
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
