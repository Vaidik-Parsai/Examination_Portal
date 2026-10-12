<template>
  <div class="home-container app-container">
    <!-- Hero / Welcome Banner -->
    <div class="simple-card welcome-banner">
      <h1>Online Examination Portal</h1>
      <p class="lead">
        A web application for scheduling, conducting, and evaluating oral viva examinations.
      </p>

      <div class="banner-buttons" v-if="!auth.isAuthenticated.value">
        <router-link to="/login" class="btn btn-primary">Login</router-link>
        <router-link to="/register" class="btn btn-secondary">Student Registration</router-link>
      </div>
      <div class="banner-buttons" v-else>
        <router-link :to="dashboardRoute" class="btn btn-primary">
          Go to {{ auth.primaryRole }} Dashboard →
        </router-link>
      </div>
    </div>

    <!-- Portals Overview -->
    <div class="portals-grid">
      <div class="simple-card portal-box">
        <h3>Admin Portal</h3>
        <p>Manage courses, configure exams and scoring rubrics, assign slots to examiners, and download results.</p>
        <router-link to="/login" class="btn btn-secondary btn-sm">Admin Login</router-link>
      </div>

      <div class="simple-card portal-box">
        <h3>Examiner Portal</h3>
        <p>Schedule viva time slots, review booked candidates, enter evaluation marks and remarks, and finalize slots.</p>
        <router-link to="/login" class="btn btn-secondary btn-sm">Examiner Login</router-link>
      </div>

      <div class="simple-card portal-box">
        <h3>Student Portal</h3>
        <p>Register as a student, browse available open examination slots, reserve seats, and view results.</p>
        <router-link to="/login" class="btn btn-secondary btn-sm">Student Login</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { auth } from '../services/auth';

const dashboardRoute = computed(() => {
  const role = auth.primaryRole;
  if (role === 'admin') return '/admin/dashboard';
  if (role === 'examiner') return '/examiner/dashboard';
  if (role === 'student') return '/student/dashboard';
  return '/';
});
</script>

<style scoped>
.welcome-banner {
  text-align: center;
  padding: 35px 20px;
  background-color: #ffffff;
}

.welcome-banner h1 {
  margin-bottom: 10px;
  color: #0d6efd;
}

.lead {
  font-size: 16px;
  color: #495057;
  margin-bottom: 20px;
}

.banner-buttons {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.portals-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-top: 10px;
}

.portal-box {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.portal-box p {
  color: #6c757d;
  font-size: 14px;
  margin: 10px 0 15px 0;
  flex: 1;
}
</style>
