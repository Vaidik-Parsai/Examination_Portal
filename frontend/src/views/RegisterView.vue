<template>
  <div class="auth-page app-container">
    <div class="simple-card auth-card">
      <div class="auth-header">
        <h2>Student Registration</h2>
        <p>Create an account to book examination slots</p>
      </div>

      <div v-if="errorMessage" class="alert alert-error">
        {{ errorMessage }}
      </div>

      <div v-if="successMessage" class="alert alert-success">
        {{ successMessage }}
      </div>

      <form @submit.prevent="handleRegister" class="auth-form" v-if="!successMessage">
        <div class="form-group">
          <label class="form-label" for="reg-name">Full Name</label>
          <input
            id="reg-name"
            v-model="form.name"
            type="text"
            class="form-input"
            placeholder="e.g. Rahul Sharma"
            required
          />
        </div>

        <div class="form-group">
          <label class="form-label" for="reg-email">Email Address</label>
          <input
            id="reg-email"
            v-model="form.email"
            type="email"
            class="form-input"
            placeholder="student@example.com"
            required
          />
        </div>

        <div class="form-group">
          <label class="form-label" for="reg-password">Password</label>
          <input
            id="reg-password"
            v-model="form.password"
            type="password"
            class="form-input"
            placeholder="Enter password"
            required
          />
        </div>

        <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
          <span v-if="loading">Creating Account...</span>
          <span v-else>Register</span>
        </button>
      </form>

      <div v-else class="post-success-action">
        <router-link to="/login" class="btn btn-primary btn-block">Go to Login →</router-link>
      </div>

      <div class="auth-footer">
        <p>Already have an account? <router-link to="/login">Sign in here</router-link></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { auth } from '../services/auth';

const form = reactive({
  name: '',
  email: '',
  password: ''
});

const loading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

const handleRegister = async () => {
  loading.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  try {
    const res = await auth.registerStudent(form.name, form.email, form.password);
    successMessage.value = res.message || 'Account created successfully! You can now log in.';
  } catch (err) {
    errorMessage.value = err.message || 'Registration failed. Please check your inputs.';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  padding-top: 40px;
}

.auth-card {
  width: 100%;
  max-width: 400px;
}

.auth-header {
  margin-bottom: 20px;
  text-align: center;
}

.auth-header h2 {
  margin-bottom: 5px;
}

.auth-header p {
  color: #6c757d;
  font-size: 13px;
}

.auth-form {
  display: flex;
  flex-direction: column;
}

.btn-block {
  margin-top: 10px;
  padding: 9px;
  font-size: 15px;
}

.post-success-action {
  margin-top: 10px;
}

.auth-footer {
  text-align: center;
  margin-top: 15px;
  font-size: 13px;
  color: #6c757d;
}
</style>
