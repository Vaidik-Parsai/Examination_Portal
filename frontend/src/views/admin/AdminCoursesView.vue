<template>
  <div class="admin-courses app-container">
    <div class="page-header">
      <div>
        <h1 class="page-title">Course Management</h1>
        <p class="page-subtitle">Configure courses and academic subjects offered for examination</p>
      </div>
      <button @click="openCreateModal" class="btn btn-primary btn-sm">+ Create Course</button>
    </div>

    <!-- Alert / Message -->
    <div v-if="feedback.text" :class="['alert', feedback.isError ? 'alert-error' : 'alert-success']">
      {{ feedback.text }}
    </div>

    <!-- Courses Table -->
    <div class="table-container glass-card">
      <div v-if="loading" class="table-empty">Loading courses...</div>
      <div v-else-if="courses.length === 0" class="table-empty">No courses created yet. Click "+ Create Course" to add one.</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Code</th>
            <th>Course Name</th>
            <th>Description</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in courses" :key="c.id">
            <td>#{{ c.id }}</td>
            <td><strong>{{ c.code }}</strong></td>
            <td>{{ c.name }}</td>
            <td>{{ c.description || '—' }}</td>
            <td>
              <span :class="['badge', c.status === 'active' ? 'badge-success' : 'badge-warning']">
                {{ c.status }}
              </span>
            </td>
            <td>
              <div class="action-buttons">
                <button @click="openEditModal(c)" class="btn btn-secondary btn-sm">Edit</button>
                <button @click="deleteCourse(c.id)" class="btn btn-danger btn-sm">Delete</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <h3>{{ isEditing ? 'Edit Course' : 'Create New Course' }}</h3>
        <form @submit.prevent="saveCourse" class="modal-form">
          <div class="form-group">
            <label class="form-label" for="course-code">Course Code</label>
            <input
              id="course-code"
              v-model="form.code"
              type="text"
              class="form-input"
              placeholder="e.g. CS2001"
              :disabled="isEditing"
              required
            />
          </div>

          <div class="form-group">
            <label class="form-label" for="course-name">Course Name</label>
            <input
              id="course-name"
              v-model="form.name"
              type="text"
              class="form-input"
              placeholder="e.g. Modern Application Development"
              required
            />
          </div>

          <div class="form-group">
            <label class="form-label" for="course-desc">Description</label>
            <textarea
              id="course-desc"
              v-model="form.description"
              class="form-textarea"
              rows="3"
              placeholder="Course syllabus and assessment summary..."
            ></textarea>
          </div>

          <div class="form-group">
            <label class="form-label" for="course-status">Status</label>
            <select id="course-status" v-model="form.status" class="form-select">
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>

          <div class="modal-actions">
            <button type="button" @click="closeModal" class="btn btn-secondary">Cancel</button>
            <button type="submit" class="btn btn-primary" :disabled="submitting">
              {{ submitting ? 'Saving...' : (isEditing ? 'Update Course' : 'Create Course') }}
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

const courses = ref([]);
const loading = ref(true);
const submitting = ref(false);
const showModal = ref(false);
const isEditing = ref(false);
const editingId = ref(null);

const form = reactive({
  code: '',
  name: '',
  description: '',
  status: 'active'
});

const feedback = reactive({
  text: '',
  isError: false
});

const showFeedback = (text, isError = false) => {
  feedback.text = text;
  feedback.isError = isError;
  setTimeout(() => { feedback.text = ''; }, 4000);
};

const loadCourses = async () => {
  loading.value = true;
  try {
    const data = await api.get('/api/admin/courses');
    courses.value = data.courses || [];
  } catch (err) {
    showFeedback(err.message || 'Failed to fetch courses.', true);
  } finally {
    loading.value = false;
  }
};

const openCreateModal = () => {
  isEditing.value = false;
  editingId.value = null;
  form.code = '';
  form.name = '';
  form.description = '';
  form.status = 'active';
  showModal.value = true;
};

const openEditModal = (c) => {
  isEditing.value = true;
  editingId.value = c.id;
  form.code = c.code;
  form.name = c.name;
  form.description = c.description;
  form.status = c.status;
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
};

const saveCourse = async () => {
  submitting.value = true;
  try {
    if (isEditing.value) {
      await api.put(`/api/admin/courses/${editingId.value}`, {
        name: form.name,
        description: form.description,
        status: form.status
      });
      showFeedback('Course updated successfully.');
    } else {
      await api.post('/api/admin/courses', form);
      showFeedback('Course created successfully.');
    }
    closeModal();
    loadCourses();
  } catch (err) {
    showFeedback(err.message || 'Error saving course.', true);
  } finally {
    submitting.value = false;
  }
};

const deleteCourse = async (id) => {
  if (!confirm('Are you sure you want to delete this course?')) return;
  try {
    await api.delete(`/api/admin/courses/${id}`);
    showFeedback('Course deleted successfully.');
    loadCourses();
  } catch (err) {
    showFeedback(err.message || 'Failed to delete course.', true);
  }
};

onMounted(() => {
  loadCourses();
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

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

.modal-form {
  margin-top: 1.5rem;
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
