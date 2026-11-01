<template>
  <div class="admin-dashboard app-container">
    <div class="page-header d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
      <div>
        <h1 class="page-title h2 mb-1">Admin Dashboard & Reports</h1>
        <p class="page-subtitle text-muted mb-0">Examination statistics, student evaluations, examiner activity, and portal search</p>
      </div>
      <div class="header-actions d-flex gap-2">
        <router-link to="/admin/courses" class="btn btn-outline-secondary btn-sm">+ Course</router-link>
        <router-link to="/admin/exams" class="btn btn-outline-secondary btn-sm">+ Exam</router-link>
        <router-link to="/admin/slots" class="btn btn-primary btn-sm">+ Create Slot</router-link>
      </div>
    </div>

    <!-- Alert / Message -->
    <div v-if="error" class="alert alert-danger" role="alert">
      {{ error }}
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="text-muted mt-2">Loading examination portal metrics...</p>
    </div>

    <div v-else>
      <!-- Key Performance Indicators (Cards) -->
      <div class="row g-3 mb-4">
        <div class="col-6 col-md-4 col-xl-2">
          <div class="card shadow-sm border-0 h-100 p-3 stat-card">
            <span class="text-muted small">Total Courses</span>
            <h3 class="fw-bold mt-1 mb-0">{{ stats.total_courses || 0 }}</h3>
          </div>
        </div>
        <div class="col-6 col-md-4 col-xl-2">
          <div class="card shadow-sm border-0 h-100 p-3 stat-card">
            <span class="text-muted small">Total Exams</span>
            <h3 class="fw-bold mt-1 mb-0">{{ stats.total_exams || 0 }}</h3>
            <small class="text-success">{{ stats.examinations_conducted || 0 }} conducted</small>
          </div>
        </div>
        <div class="col-6 col-md-4 col-xl-2">
          <div class="card shadow-sm border-0 h-100 p-3 stat-card">
            <span class="text-muted small">Registered Students</span>
            <h3 class="fw-bold mt-1 mb-0">{{ stats.total_students || 0 }}</h3>
            <small class="text-primary">{{ stats.students_evaluated || 0 }} evaluated</small>
          </div>
        </div>
        <div class="col-6 col-md-4 col-xl-2">
          <div class="card shadow-sm border-0 h-100 p-3 stat-card">
            <span class="text-muted small">Total Bookings</span>
            <h3 class="fw-bold mt-1 mb-0">{{ stats.total_bookings || 0 }}</h3>
            <small class="text-info">{{ stats.bookings_by_status?.completed || 0 }} completed</small>
          </div>
        </div>
        <div class="col-6 col-md-4 col-xl-2">
          <div class="card shadow-sm border-0 h-100 p-3 stat-card">
            <span class="text-muted small">Pending Grading</span>
            <h3 class="fw-bold text-warning mt-1 mb-0">{{ stats.pending_evaluations || 0 }}</h3>
            <small class="text-muted">Awaiting evaluation</small>
          </div>
        </div>
        <div class="col-6 col-md-4 col-xl-2">
          <div class="card shadow-sm border-0 h-100 p-3 stat-card">
            <span class="text-muted small">Active Examiners</span>
            <h3 class="fw-bold mt-1 mb-0">{{ stats.total_examiners || 0 }}</h3>
            <small class="text-muted">Faculty evaluators</small>
          </div>
        </div>
      </div>

      <!-- Bookings by Status Breakdown -->
      <div class="card shadow-sm border-0 mb-4 p-3">
        <h5 class="card-title fw-bold mb-3">Booking Status Breakdown</h5>
        <div class="row g-2 text-center">
          <div class="col-6 col-md-3">
            <div class="p-2 rounded bg-light border">
              <span class="badge bg-primary px-3 py-1 mb-1">Booked</span>
              <h4 class="mb-0 fw-bold">{{ stats.bookings_by_status?.booked || 0 }}</h4>
            </div>
          </div>
          <div class="col-6 col-md-3">
            <div class="p-2 rounded bg-light border">
              <span class="badge bg-warning text-dark px-3 py-1 mb-1">Rescheduled</span>
              <h4 class="mb-0 fw-bold">{{ stats.bookings_by_status?.rescheduled || 0 }}</h4>
            </div>
          </div>
          <div class="col-6 col-md-3">
            <div class="p-2 rounded bg-light border">
              <span class="badge bg-success px-3 py-1 mb-1">Completed</span>
              <h4 class="mb-0 fw-bold">{{ stats.bookings_by_status?.completed || 0 }}</h4>
            </div>
          </div>
          <div class="col-6 col-md-3">
            <div class="p-2 rounded bg-light border">
              <span class="badge bg-secondary px-3 py-1 mb-1">Cancelled</span>
              <h4 class="mb-0 fw-bold">{{ stats.bookings_by_status?.cancelled || 0 }}</h4>
            </div>
          </div>
        </div>
      </div>

      <!-- Universal Search Section -->
      <div class="card shadow-sm border-0 mb-4 p-3">
        <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
          <div>
            <h5 class="card-title fw-bold mb-0">Universal Search</h5>
            <small class="text-muted">Search students, examiners, and examinations by name, ID, course, or status</small>
          </div>
          <div class="btn-group btn-group-sm" role="group">
            <button
              v-for="t in ['all', 'students', 'examiners', 'examinations']"
              :key="t"
              type="button"
              :class="['btn', searchType === t ? 'btn-primary' : 'btn-outline-secondary']"
              @click="setSearchType(t)"
            >
              {{ t.charAt(0).toUpperCase() + t.slice(1) }}
            </button>
          </div>
        </div>

        <div class="row g-2 mb-3">
          <div class="col-md-9">
            <input
              type="text"
              v-model="searchQuery"
              @keyup.enter="performSearch"
              class="form-control"
              placeholder="Search by keyword, name, email, course code, or ID..."
            />
          </div>
          <div class="col-md-3 d-flex gap-2">
            <button @click="performSearch" class="btn btn-primary w-100" :disabled="isSearching">
              {{ isSearching ? 'Searching...' : 'Search' }}
            </button>
            <button v-if="hasSearched" @click="clearSearch" class="btn btn-outline-secondary">
              Clear
            </button>
          </div>
        </div>

        <!-- Search Results Display -->
        <div v-if="hasSearched" class="mt-2">
          <!-- Students Results -->
          <div v-if="searchResults.students?.length" class="mb-3">
            <h6 class="fw-bold text-primary">Students ({{ searchResults.students.length }})</h6>
            <div class="table-responsive">
              <table class="table table-sm table-striped align-middle">
                <thead>
                  <tr>
                    <th>Student ID</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Bookings</th>
                    <th>Account Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="st in searchResults.students" :key="st.id">
                    <td>#{{ st.id }}</td>
                    <td><strong>{{ st.name }}</strong></td>
                    <td>{{ st.email }}</td>
                    <td><span class="badge bg-light text-dark border">{{ st.bookings_count }} bookings</span></td>
                    <td>
                      <span :class="['badge', st.active ? 'bg-success' : 'bg-secondary']">
                        {{ st.active ? 'Active' : 'Inactive' }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Examiners Results -->
          <div v-if="searchResults.examiners?.length" class="mb-3">
            <h6 class="fw-bold text-success">Examiners ({{ searchResults.examiners.length }})</h6>
            <div class="table-responsive">
              <table class="table table-sm table-striped align-middle">
                <thead>
                  <tr>
                    <th>Examiner ID</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Department</th>
                    <th>Slots Allocated</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="ex in searchResults.examiners" :key="ex.id">
                    <td>#{{ ex.id }}</td>
                    <td><strong>{{ ex.name }}</strong></td>
                    <td>{{ ex.email }}</td>
                    <td>{{ ex.department }}</td>
                    <td>{{ ex.slots_count }} slots</td>
                    <td><span class="badge bg-info text-dark">{{ ex.status }}</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Examinations Results -->
          <div v-if="searchResults.examinations?.length" class="mb-3">
            <h6 class="fw-bold text-warning">Examinations ({{ searchResults.examinations.length }})</h6>
            <div class="table-responsive">
              <table class="table table-sm table-striped align-middle">
                <thead>
                  <tr>
                    <th>Exam ID</th>
                    <th>Course</th>
                    <th>Exam Name</th>
                    <th>Type</th>
                    <th>Duration</th>
                    <th>Status</th>
                    <th>Slots</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="em in searchResults.examinations" :key="em.id">
                    <td>#{{ em.id }}</td>
                    <td><strong>{{ em.course_code }}</strong> - {{ em.course_name }}</td>
                    <td>{{ em.name }}</td>
                    <td>{{ em.exam_type }}</td>
                    <td>{{ em.duration }} min</td>
                    <td>
                      <span :class="['badge', em.status === 'published' ? 'bg-success' : (em.status === 'closed' ? 'bg-danger' : 'bg-secondary')]">
                        {{ em.status }}
                      </span>
                    </td>
                    <td>{{ em.slots_count }} slots</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div v-if="!searchResults.students?.length && !searchResults.examiners?.length && !searchResults.examinations?.length" class="alert alert-light border text-center my-2">
            No records matched your search query "{{ searchQuery }}".
          </div>
        </div>
      </div>

      <!-- Examiner Activity Report Table -->
      <div class="card shadow-sm border-0 mb-4 p-3">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h5 class="card-title fw-bold mb-0">Examiner Activity & Evaluation Progress</h5>
          <router-link to="/admin/examiners" class="btn btn-outline-primary btn-sm">Manage Examiners →</router-link>
        </div>

        <div v-if="!stats.examiner_activity?.length" class="text-muted text-center py-4">
          No examiner activity records found.
        </div>
        <div v-else class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th>Examiner</th>
                <th>Department</th>
                <th>Slots Created</th>
                <th>Evaluations Completed</th>
                <th>Pending Evaluations</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="act in stats.examiner_activity" :key="act.examiner_id">
                <td>
                  <strong>{{ act.name }}</strong>
                  <div class="small text-muted">{{ act.email }}</div>
                </td>
                <td>{{ act.department }}</td>
                <td><span class="badge bg-light text-dark border">{{ act.slots_count }}</span></td>
                <td>
                  <span class="badge bg-success">{{ act.evaluations_completed }} completed</span>
                </td>
                <td>
                  <span :class="['badge', act.pending_evaluations > 0 ? 'bg-warning text-dark' : 'bg-light text-muted border']">
                    {{ act.pending_evaluations }} pending
                  </span>
                </td>
                <td>
                  <span :class="['badge', act.status === 'active' ? 'bg-success' : 'bg-secondary']">
                    {{ act.status }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
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

// Universal search states
const searchQuery = ref('');
const searchType = ref('all');
const isSearching = ref(false);
const hasSearched = ref(false);
const searchResults = ref({ students: [], examiners: [], examinations: [] });

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

const setSearchType = (type) => {
  searchType.value = type;
  if (searchQuery.value) {
    performSearch();
  }
};

const performSearch = async () => {
  if (!searchQuery.value.trim()) return;
  isSearching.value = true;
  try {
    const res = await api.get(`/api/admin/search?q=${encodeURIComponent(searchQuery.value.trim())}&type=${searchType.value}`);
    searchResults.value = res;
    hasSearched.value = true;
  } catch (err) {
    error.value = err.message || 'Search request failed.';
  } finally {
    isSearching.value = false;
  }
};

const clearSearch = () => {
  searchQuery.value = '';
  hasSearched.value = false;
  searchResults.value = { students: [], examiners: [], examinations: [] };
};

onMounted(() => {
  loadDashboard();
});
</script>

<style scoped>
.stat-card {
  transition: transform 0.15s ease-in-out;
}
.stat-card:hover {
  transform: translateY(-2px);
}
</style>
