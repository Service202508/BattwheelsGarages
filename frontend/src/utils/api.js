/**
 * API Utilities for Multi-Tenant Support
 * Provides helper functions to add organization context to API calls
 */

// Get the current organization ID from localStorage
export const getOrganizationId = () => {
  return localStorage.getItem("organization_id");
};

// Set the current organization ID in localStorage
export const setOrganizationId = (orgId) => {
  if (orgId) {
    localStorage.setItem("organization_id", orgId);
  } else {
    localStorage.removeItem("organization_id");
  }
};

// Helper to read CSRF token from cookie
const getCsrfToken = () => {
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
};

// Get standard headers with authentication and organization context
export const getAuthHeaders = (includeOrgId = true) => {
  const headers = {
    "Content-Type": "application/json",
  };
  
  const token = localStorage.getItem("token");
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  
  if (includeOrgId) {
    const orgId = getOrganizationId();
    if (orgId) {
      headers["X-Organization-ID"] = orgId;
    }
  }
  
  // CSRF: attach token on every request (backend validates on state-changing methods)
  const csrfToken = getCsrfToken();
  if (csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }
  
  return headers;
};

// Wrapper for fetch that automatically includes auth and org headers
export const apiFetch = async (url, options = {}) => {
  const defaultHeaders = getAuthHeaders(options.includeOrgId !== false);
  
  const mergedOptions = {
    ...options,
    credentials: "include",
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };
  
  // Remove custom option before passing to fetch
  delete mergedOptions.includeOrgId;
  
  const response = await fetch(url, mergedOptions);

  // Intercept 403 feature_not_available globally
  if (response.status === 403) {
    try {
      const cloned = response.clone();
      const body = await cloned.json();
      const detail = body?.detail;
      if (detail && typeof detail === "object" && detail.error === "feature_not_available") {
        window.dispatchEvent(new CustomEvent("feature_not_available", { detail }));
      }
    } catch (_) {
      // JSON parse failed — not a feature_not_available response, pass through
    }
  }

  return response;
};

// GET request helper
export const apiGet = async (url, includeOrgId = true) => {
  return apiFetch(url, {
    method: "GET",
    includeOrgId,
  });
};

// POST request helper
export const apiPost = async (url, data, includeOrgId = true) => {
  return apiFetch(url, {
    method: "POST",
    body: JSON.stringify(data),
    includeOrgId,
  });
};

// PUT request helper
export const apiPut = async (url, data, includeOrgId = true) => {
  return apiFetch(url, {
    method: "PUT",
    body: JSON.stringify(data),
    includeOrgId,
  });
};

// PATCH request helper
export const apiPatch = async (url, data, includeOrgId = true) => {
  return apiFetch(url, {
    method: "PATCH",
    body: JSON.stringify(data),
    includeOrgId,
  });
};

// DELETE request helper
export const apiDelete = async (url, includeOrgId = true) => {
  return apiFetch(url, {
    method: "DELETE",
    includeOrgId,
  });
};

// Fetch organization info and store it
export const initializeOrganization = async (api) => {
  try {
    const token = localStorage.getItem("token");
    if (!token) return null;
    
    const response = await fetch(`${api}/org`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    
    if (response.ok) {
      const org = await response.json();
      if (org.organization_id) {
        setOrganizationId(org.organization_id);
        return org;
      }
    }
    return null;
  } catch (error) {
    console.error("Failed to initialize organization:", error);
    return null;
  }
};
