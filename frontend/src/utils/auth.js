const API_URL = process.env.REACT_APP_BACKEND_URL;

export const authService = {
  async login(email, password) {
    // Ensure credentials are trimmed
    const trimmedEmail = email.trim().toLowerCase();
    const trimmedPassword = password;

    console.log('Auth Service - Login attempt');
    console.log('API Endpoint:', `${API_URL}/api/admin/auth/login`);

    try {
      const response = await fetch(`${API_URL}/api/admin/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: trimmedEmail, password: trimmedPassword }),
      });

      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);

      const data = await response.json();
      console.log('Response data keys:', Object.keys(data));
      
      if (!response.ok) {
        console.error('Login failed with status:', response.status);
        console.error('Error detail:', data.detail);
        throw new Error(data.detail || 'Login failed');
      }

      console.log('Login successful, storing token...');
      localStorage.setItem('admin_token', data.access_token);
      localStorage.setItem('admin_user', JSON.stringify(data.user));
      return data;
    } catch (err) {
      console.error('Auth service error:', err);
      if (err.message === 'Failed to fetch') {
        throw new Error('Unable to connect to server. Please check your internet connection.');
      }
      throw err;
    }
  },

  logout() {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user');
  },

  getToken() {
    return localStorage.getItem('admin_token');
  },

  getUser() {
    const user = localStorage.getItem('admin_user');
    return user ? JSON.parse(user) : null;
  },

  isAuthenticated() {
    return !!this.getToken();
  },

  getAuthHeaders() {
    const token = this.getToken();
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    };
  },
};
