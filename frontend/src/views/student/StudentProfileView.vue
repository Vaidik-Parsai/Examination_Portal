<template>
  <div class="student-profile app-container">
    <div class="page-header">
      <div>
        <h1 class="page-title">My Profile</h1>
        <p class="page-subtitle">View and update your account details</p>
      </div>
    </div>

    <!-- Alert / Message -->
    <div v-if="feedback.text" :class="['alert', feedback.isError ? 'alert-error' : 'alert-success']">
      {{ feedback.text }}
    </div>

    <div v-if="loading" class="text-muted" style="padding: 2rem;">Loading profile...</div>

    <div v-else class="simple-card profile-card">
      <div class="profile-info">
        <div class="info-row">
          <span class="info-label">Name</span>
          <span class="info-value">{{ profile.name }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Email</span>
          <span class="info-value">{{ profile.email }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Role</span>
          <span class="badge badge-student">student</span>
        </div>
        <div class="info-row">
          <span class="info-label">Total Bookings</span>
          <span class="info-value">{{ profile.total_bookings }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Account Since</span>
          <span class="info-value">{{ profile.created_at ? profile.created_at.split('T')[0] : '—' }}</span>
        </div>
      </div>

      <hr style="margin: 1.5rem 0;" />

      <h3 style="margin-bottom:1rem;">Update Details</h3>
      <form @submit.prevent="saveProfile" style="max-width: 440px;">
        <div class="form-group">
          <label class="form-label" for="p-name">Full Name</label>
          <input
            id="p-name"
            v-model="form.name"
            type="text"
            class="form-input"
            placeholder="Enter your full name"
            required
            minlength="2"
          />
        </div>

        <div class="form-group">
          <label class="form-label" for="p-pass">New Password <span class="text-muted">(leave blank to keep current)</span></label>
          <input
            id="p-pass"
            v-model="form.password"
            type="password"
            class="form-input"
            placeholder="At least 6 characters"
            minlength="6"
            autocomplete="new-password"
          />
        </div>

        <button type="submit" class="btn btn-primary" :disabled="saving">
          {{ saving ? 'Saving...' : 'Update Profile' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { api } from '../../services/api';
import { auth } from '../../services/auth';

const profile = ref(null);
const loading = ref(true);
const saving = ref(false);

const form = reactive({ name: '', password: '' });

const feedback = reactive({ text: '', isError: false });
const showFeedback = (text, isError = false) => {
  feedback.text = text;
  feedback.isError = isError;
  setTimeout(() => { feedback.text = ''; }, 5000);
};

const loadProfile = async () => {
  loading.value = true;
  try {
    const data = await api.get('/api/student/profile');
    profile.value = data;
    form.name = data.name || '';
    form.password = '';
  } catch (err) {
    showFeedback(err.message || 'Failed to load profile.', true);
  } finally {
    loading.value = false;
  }
};

const saveProfile = async () => {
  saving.value = true;
  try {
    const payload = { name: form.name.trim() };
    if (form.password.trim()) {
      payload.password = form.password.trim();
    }
    const res = await api.put('/api/student/profile', payload);
    showFeedback(res.message || 'Profile updated successfully.');
    form.password = '';
    // Update navbar name
    if (auth.state.user) {
      auth.state.user.name = res.name || form.name;
    }
    loadProfile();
  } catch (err) {
    showFeedback(err.message || 'Failed to update profile.', true);
  } finally {
    saving.value = false;
  }
};

onMounted(() => { loadProfile(); });
</script>

<style scoped>
.page-header { margin-bottom: 1.5rem; }
.text-muted { color: #6c757d; }

.profile-card { max-width: 600px; }

.profile-info { display: flex; flex-direction: column; gap: 10px; }
.info-row { display: flex; align-items: center; gap: 12px; }
.info-label { font-weight: 600; font-size: 13px; color: #6c757d; min-width: 130px; }
.info-value { font-size: 14px; }
</style>

