<template>
  <div class="auth-page app-container">
    <div class="simple-card auth-card">
      <div class="auth-header">
        <h2>Sign In</h2>
        <p>Enter your credentials to access the examination portal</p>
      </div>

      <!-- Error Alert -->
      <div v-if="errorMessage" class="alert alert-error">
        {{ errorMessage }}
      </div>

      <form @submit.prevent="handleLogin" class="auth-form">
        <div class="form-group">
          <label class="form-label" for="login-email">Email Address</label>
          <input
            id="login-email"
            v-model="form.email"
            type="email"
            class="form-input"
            placeholder="admin@example.com"
            required
          />
        </div>

        <div class="form-group">
          <label class="form-label" for="login-password">Password</label>
          <input
            id="login-password"
            v-model="form.password"
            type="password"
            class="form-input"
            placeholder="Enter password"
            required
          />
        </div>

        <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
          <span v-if="loading">Signing in...</span>
          <span v-else>Sign In</span>
        </button>
      </form>

      <!-- Quick Fill Helper for Demo / Testing -->
      <div class="quick-fill-section">
        <span class="quick-fill-label">Demo Admin Credentials:</span>
        <button type="button" @click="fillCreds('admin@example.com', 'admin123')" class="btn btn-secondary btn-sm">
          Fill Default Admin
        </button>
      </div>

      <div class="auth-footer">
        <p>New Student? <router-link to="/register">Register here</router-link></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { auth } from '../services/auth';

const router = useRouter();
const route = useRoute();

const form = reactive({
  email: '',
  password: ''
});

const loading = ref(false);
const errorMessage = ref('');

const fillCreds = (email, password) => {
  form.email = email;
  form.password = password;
  errorMessage.value = '';
};

const handleLogin = async () => {
  loading.value = true;
  errorMessage.value = '';

  try {
    await auth.login(form.email, form.password);

    // Redirect to requested redirect route or role dashboard
    const redirect = route.query.redirect;
    if (redirect) {
      router.push(redirect);
      return;
    }

    const role = auth.primaryRole;
    if (role === 'admin') router.push('/admin/dashboard');
    else if (role === 'examiner') router.push('/examiner/dashboard');
    else router.push('/student/dashboard');
  } catch (err) {
    errorMessage.value = err.message || 'Invalid email or password.';
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

.quick-fill-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #dee2e6;
}

.quick-fill-label {
  font-size: 12px;
  color: #6c757d;
}

.auth-footer {
  text-align: center;
  margin-top: 15px;
  font-size: 13px;
  color: #6c757d;
}
</style>
