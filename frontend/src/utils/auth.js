const API_URL = process.env.REACT_APP_BACKEND_URL;

export const authService = {
  async login(email, password) {
    const response = await fetch(`${API_URL}/api/admin/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Login failed');
    }

    localStorage.setItem('admin_token', data.access_token);
    localStorage.setItem('admin_user', JSON.stringify(data.user));
    return data;
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
