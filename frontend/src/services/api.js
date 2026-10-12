/**
 * API Client with Flask-Security Token Authentication
 */

const API_BASE = ''; // Uses Vite proxy to forward /api to backend

export const api = {
  getToken() {
    return localStorage.getItem('auth_token') || '';
  },

  setToken(token) {
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  },

  getUser() {
    try {
      return JSON.parse(localStorage.getItem('user_info') || 'null');
    } catch {
      return null;
    }
  },

  setUser(user) {
    if (user) {
      localStorage.setItem('user_info', JSON.stringify(user));
    } else {
      localStorage.removeItem('user_info');
    }
  },

  async request(endpoint, options = {}) {
    const token = this.getToken();
    const isAuthEndpoint = endpoint.includes('/login') || endpoint.includes('/register');
    
    const headers = {
      'Content-Type': 'application/json',
      ...(token && !isAuthEndpoint ? { 'Authentication-Token': token } : {}),
      ...(options.headers || {})
    };

    const config = {
      ...options,
      headers
    };

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, config);
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const errorMsg = data.message || data.response?.errors?.[0] || data.description || 'Request failed';
        if (response.status === 401) {
          this.setToken(null);
          this.setUser(null);
        }
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      console.error(`API Error [${endpoint}]:`, err);
      throw err;
    }
  },

  get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  },

  post(endpoint, body) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body)
    });
  },

  put(endpoint, body) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body)
    });
  },

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
};
