import { reactive, computed } from 'vue';
import { api } from './api';

const state = reactive({
  token: api.getToken(),
  user: api.getUser()
});

export const auth = {
  state,

  isAuthenticated: computed(() => !!state.token),
  
  user: computed(() => state.user),

  roles: computed(() => state.user?.roles || []),

  hasRole(role) {
    if (!state.user || !state.user.roles) return false;
    return state.user.roles.includes(role);
  },

  get primaryRole() {
    if (!state.user || !state.user.roles || state.user.roles.length === 0) return null;
    if (state.user.roles.includes('admin')) return 'admin';
    if (state.user.roles.includes('examiner')) return 'examiner';
    if (state.user.roles.includes('student')) return 'student';
    return state.user.roles[0];
  },

  async login(email, password) {
    // Clear old token before trying login
    state.token = null;
    state.user = null;
    api.setToken(null);
    api.setUser(null);

    const data = await api.post('/api/auth/login', { email, password });
    
    const user = data.user || data.response?.user || data;
    const token = data.token || user.authentication_token || data.response?.token;

    if (!token) {
      throw new Error('Authentication token not received from server.');
    }

    state.token = token;
    state.user = user;
    api.setToken(token);
    api.setUser(user);

    return user;
  },

  async registerStudent(name, email, password) {
    return await api.post('/api/auth/student/register', { name, email, password });
  },

  async logout() {
    try {
      await api.post('/api/auth/logout', {});
    } catch (e) {
      // ignore
    }
    state.token = null;
    state.user = null;
    api.setToken(null);
    api.setUser(null);
  }
};
