import { createRouter, createWebHistory } from 'vue-router';
import { auth } from '../services/auth';

// Views
import HomeView from '../views/HomeView.vue';
import LoginView from '../views/LoginView.vue';
import RegisterView from '../views/RegisterView.vue';

// Admin Views
import AdminDashboardView from '../views/admin/AdminDashboardView.vue';
import AdminCoursesView from '../views/admin/AdminCoursesView.vue';
import AdminExamsView from '../views/admin/AdminExamsView.vue';
import AdminSlotsView from '../views/admin/AdminSlotsView.vue';
import AdminExaminersView from '../views/admin/AdminExaminersView.vue';
import AdminTasksView from '../views/admin/AdminTasksView.vue';

// Examiner Views
import ExaminerDashboardView from '../views/examiner/ExaminerDashboardView.vue';
import ExaminerSlotBookingsView from '../views/examiner/ExaminerSlotBookingsView.vue';

// Student Views
import StudentDashboardView from '../views/student/StudentDashboardView.vue';
import StudentSlotsView from '../views/student/StudentSlotsView.vue';
import StudentBookingsView from '../views/student/StudentBookingsView.vue';
import StudentEvaluationsView from '../views/student/StudentEvaluationsView.vue';

const routes = [
  { path: '/', name: 'Home', component: HomeView },
  { path: '/login', name: 'Login', component: LoginView },
  { path: '/register', name: 'Register', component: RegisterView },

  // Admin Routes
  {
    path: '/admin/dashboard',
    name: 'AdminDashboard',
    component: AdminDashboardView,
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/admin/courses',
    name: 'AdminCourses',
    component: AdminCoursesView,
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/admin/exams',
    name: 'AdminExams',
    component: AdminExamsView,
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/admin/slots',
    name: 'AdminSlots',
    component: AdminSlotsView,
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/admin/examiners',
    name: 'AdminExaminers',
    component: AdminExaminersView,
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/admin/tasks',
    name: 'AdminTasks',
    component: AdminTasksView,
    meta: { requiresAuth: true, role: 'admin' }
  },

  // Examiner Routes
  {
    path: '/examiner/dashboard',
    name: 'ExaminerDashboard',
    component: ExaminerDashboardView,
    meta: { requiresAuth: true, role: 'examiner' }
  },
  {
    path: '/examiner/slots/:slotId/bookings',
    name: 'ExaminerSlotBookings',
    component: ExaminerSlotBookingsView,
    meta: { requiresAuth: true, role: 'examiner' }
  },

  // Student Routes
  {
    path: '/student/dashboard',
    name: 'StudentDashboard',
    component: StudentDashboardView,
    meta: { requiresAuth: true, role: 'student' }
  },
  {
    path: '/student/slots',
    name: 'StudentSlots',
    component: StudentSlotsView,
    meta: { requiresAuth: true, role: 'student' }
  },
  {
    path: '/student/bookings',
    name: 'StudentBookings',
    component: StudentBookingsView,
    meta: { requiresAuth: true, role: 'student' }
  },
  {
    path: '/student/evaluations',
    name: 'StudentEvaluations',
    component: StudentEvaluationsView,
    meta: { requiresAuth: true, role: 'student' }
  },

  // Catch-all
  { path: '/:pathMatch(.*)*', redirect: '/' }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth && !auth.isAuthenticated.value) {
    return next({ path: '/login', query: { redirect: to.fullPath } });
  }

  if (to.meta.role && !auth.hasRole(to.meta.role)) {
    const primary = auth.primaryRole;
    if (primary === 'admin') return next('/admin/dashboard');
    if (primary === 'examiner') return next('/examiner/dashboard');
    if (primary === 'student') return next('/student/dashboard');
    return next('/login');
  }

  next();
});

export default router;
