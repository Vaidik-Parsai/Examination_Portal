<template>
  <div class="admin-examiners app-container">
    <div class="page-header">
      <div>
        <h1 class="page-title">Examiner Directory & Provisioning</h1>
        <p class="page-subtitle">Manage faculty and authorized evaluators conducting viva assessments</p>
      </div>
      <button @click="openCreateModal" class="btn btn-primary btn-sm">+ Provision Examiner</button>
    </div>

    <!-- Alert / Message -->
    <div v-if="feedback.text" :class="['alert', feedback.isError ? 'alert-error' : 'alert-success']">
      {{ feedback.text }}
    </div>

    <!-- Examiners Table -->
    <div class="table-container glass-card">
      <div v-if="loading" class="table-empty">Loading examiners...</div>
      <div v-else-if="examiners.length === 0" class="table-empty">No examiners provisioned yet. Click "+ Provision Examiner" to add one.</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Profile ID</th>
            <th>Name</th>
            <th>Email</th>
            <th>Department</th>
            <th>Contact</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ex in examiners" :key="ex.id">
            <td>#{{ ex.id }}</td>
            <td><strong>{{ ex.name }}</strong></td>
            <td>{{ ex.email }}</td>
            <td>{{ ex.department || 'General' }}</td>
            <td>{{ ex.contact || '—' }}</td>
            <td>
              <span class="badge badge-examiner">{{ ex.status || 'active' }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Examiner Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <h3>Provision New Examiner</h3>
        <p class="subtitle">Creates an authorized user account with the examiner role.</p>
        <form @submit.prevent="createExaminer" class="modal-form">
          <div class="form-group">
            <label class="form-label" for="ex-name">Full Name</label>
            <input id="ex-name" v-model="form.name" type="text" class="form-input" placeholder="Dr. Alice Smith" required />
          </div>

          <div class="form-group">
            <label class="form-label" for="ex-email">Email Address</label>
            <input id="ex-email" v-model="form.email" type="email" class="form-input" placeholder="alice@university.edu" required />
          </div>

          <div class="form-group">
            <label class="form-label" for="ex-password">Password</label>
            <input id="ex-password" v-model="form.password" type="password" class="form-input" placeholder="••••••••" required />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="ex-dept">Department</label>
              <input id="ex-dept" v-model="form.department" type="text" class="form-input" placeholder="Computer Science" />
            </div>

            <div class="form-group">
              <label class="form-label" for="ex-contact">Contact Phone</label>
              <input id="ex-contact" v-model="form.contact" type="text" class="form-input" placeholder="+91 9876543210" />
            </div>
          </div>

          <div class="modal-actions">
            <button type="button" @click="closeModal" class="btn btn-secondary">Cancel</button>
            <button type="submit" class="btn btn-primary" :disabled="submitting">
              {{ submitting ? 'Provisioning...' : 'Create Account' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { api } from '../../services/api';

const examiners = ref([]);
const loading = ref(true);
const submitting = ref(false);
const showModal = ref(false);

const form = reactive({
  name: '',
  email: '',
  password: '',
  department: '',
  contact: ''
});

const feedback = reactive({ text: '', isError: false });
const showFeedback = (text, isError = false) => {
  feedback.text = text;
  feedback.isError = isError;
  setTimeout(() => { feedback.text = ''; }, 4000);
};

const loadExaminers = async () => {
  loading.value = true;
  try {
    const data = await api.get('/api/admin/examiners');
    examiners.value = data.examiners || [];
  } catch (err) {
    showFeedback(err.message || 'Error loading examiners.', true);
  } finally {
    loading.value = false;
  }
};

const openCreateModal = () => {
  form.name = '';
  form.email = '';
  form.password = '';
  form.department = '';
  form.contact = '';
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
};

const createExaminer = async () => {
  submitting.value = true;
  try {
    await api.post('/api/admin/examiners', form);
    showFeedback('Examiner account provisioned successfully.');
    closeModal();
    loadExaminers();
  } catch (err) {
    showFeedback(err.message || 'Failed to provision examiner.', true);
  } finally {
    submitting.value = false;
  }
};

onMounted(() => {
  loadExaminers();
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
  margin-bottom: 1.25rem;
}

.table-empty {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
}

.form-row {
  display: flex;
  gap: 1rem;
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
