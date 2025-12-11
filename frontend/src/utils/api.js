/**
 * API Utility for Battwheels Garages
 * Centralized API calls with error handling
 */

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';

/**
 * Generic API call function
 */
export const api = async (path, options = {}) => {
  try {
    const url = `${API_BASE_URL}${path}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API call failed for ${path}:`, error);
    throw error;
  }
};

// ========== SERVICES API ==========

export const servicesApi = {
  /**
   * Get all active services
   */
  getAll: async () => {
    return api('/api/services');
  },

  /**
   * Get a single service by slug
   */
  getBySlug: async (slug) => {
    return api(`/api/services/${slug}`);
  },
};

// ========== BLOGS API ==========

export const blogsApi = {
  /**
   * Get all published blogs
   */
  getAll: async (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return api(`/api/blogs${queryString ? `?${queryString}` : ''}`);
  },

  /**
   * Get a single blog by slug
   */
  getBySlug: async (slug) => {
    return api(`/api/blogs/${slug}`);
  },
};

// ========== TESTIMONIALS API ==========

export const testimonialsApi = {
  /**
   * Get all active testimonials
   */
  getAll: async (category = null) => {
    const params = category && category !== 'all' ? `?category=${category}` : '';
    return api(`/api/testimonials${params}`);
  },
};

// ========== JOBS API ==========

export const jobsApi = {
  /**
   * Get all active jobs
   */
  getAll: async () => {
    return api('/api/jobs');
  },

  /**
   * Get a single job by ID
   */
  getById: async (id) => {
    return api(`/api/jobs/${id}`);
  },
};

export default api;
