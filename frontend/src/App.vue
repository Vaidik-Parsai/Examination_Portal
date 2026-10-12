<template>
  <div id="root-app">
    <!-- Main Top Navigation -->
    <header class="navbar">
      <div class="nav-brand">
        <router-link to="/">Exam Portal</router-link>
      </div>

      <!-- Nav Links -->
      <nav class="nav-links">
        <template v-if="!auth.isAuthenticated.value">
          <router-link to="/" class="nav-link">Home</router-link>
          <router-link to="/login" class="nav-link">Login</router-link>
          <router-link to="/register" class="nav-link">Register</router-link>
        </template>

        <!-- Admin Navigation -->
        <template v-else-if="auth.hasRole('admin')">
          <router-link to="/admin/dashboard" class="nav-link">Dashboard</router-link>
          <router-link to="/admin/courses" class="nav-link">Courses</router-link>
          <router-link to="/admin/exams" class="nav-link">Exams</router-link>
          <router-link to="/admin/slots" class="nav-link">Slots</router-link>
          <router-link to="/admin/examiners" class="nav-link">Examiners</router-link>
          <router-link to="/admin/tasks" class="nav-link">Tasks & Reports</router-link>
        </template>

        <!-- Examiner Navigation -->
        <template v-else-if="auth.hasRole('examiner')">
          <router-link to="/examiner/dashboard" class="nav-link">Examiner Hub</router-link>
        </template>

        <!-- Student Navigation -->
        <template v-else-if="auth.hasRole('student')">
          <router-link to="/student/dashboard" class="nav-link">Dashboard</router-link>
          <router-link to="/student/slots" class="nav-link">Available Slots</router-link>
          <router-link to="/student/bookings" class="nav-link">My Bookings</router-link>
          <router-link to="/student/evaluations" class="nav-link">Results</router-link>
        </template>
      </nav>

      <!-- User Info & Logout -->
      <div class="nav-user">
        <template v-if="auth.isAuthenticated.value">
          <span class="user-name">{{ auth.user.value?.name || auth.user.value?.email }}</span>
          <span :class="['badge', `badge-${auth.primaryRole}`]">
            {{ auth.primaryRole }}
          </span>
          <button @click="handleLogout" class="btn btn-secondary btn-sm">Logout</button>
        </template>
        <template v-else>
          <router-link to="/login" class="btn btn-primary btn-sm">Sign In</router-link>
        </template>
      </div>
    </header>

    <!-- Main Content View -->
    <main class="main-wrapper">
      <router-view />
    </main>

    <!-- Global Footer -->
    <footer class="footer">
      <div class="app-container">
        <p>© 2026 Examination Portal. Built with Vue.js & Flask.</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { auth } from './services/auth';

const router = useRouter();

const handleLogout = async () => {
  await auth.logout();
  router.push('/login');
};
</script>

<style scoped>
#root-app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-wrapper {
  flex: 1;
}
</style>
