/**
 * API Utilities for Multi-Tenant Support
 * Unified API client — auth, org context, CSRF, period-lock & feature-gate handling.
 */

// ─── Cookie helper ──────────────────────────────────────────
function getCookie(name) {
  const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return match ? decodeURIComponent(match[2]) : null;
}

// ─── Organization helpers ───────────────────────────────────
export const getOrganizationId = () => localStorage.getItem("organization_id");

export const setOrganizationId = (orgId) => {
  if (orgId) {
    localStorage.setItem("organization_id", orgId);
  } else {
    localStorage.removeItem("organization_id");
  }
};

// ─── Header builder ─────────────────────────────────────────
export const getAuthHeaders = (includeOrgId = true) => {
  const headers = { "Content-Type": "application/json" };

  const token = localStorage.getItem("token");
  if (token) headers["Authorization"] = `Bearer ${token}`;

  if (includeOrgId) {
    const orgId = getOrganizationId();
    if (orgId) headers["X-Organization-ID"] = orgId;
  }

  return headers;
};

// Methods that mutate state — require CSRF token
const UNSAFE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

// ─── Core fetch wrapper ─────────────────────────────────────
export const apiFetch = async (url, options = {}) => {
  const defaultHeaders = getAuthHeaders(options.includeOrgId !== false);

  // Inject CSRF token for unsafe methods (Double Submit Cookie pattern)
  const method = (options.method || "GET").toUpperCase();
  if (UNSAFE_METHODS.has(method)) {
    const csrfToken = getCookie("csrf_token");
    if (csrfToken) {
      defaultHeaders["X-CSRF-Token"] = csrfToken;
    }
  }

  const mergedOptions = {
    ...options,
    credentials: "include",
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  delete mergedOptions.includeOrgId;

  const response = await fetch(url, mergedOptions);

  // ── Global interceptors ──────────────────────────────────

  // 401 Token expired or invalid — redirect to login
  if (response.status === 401) {
    localStorage.removeItem("token");
    localStorage.removeItem("organization_id");
    window.location.href = "/login?reason=session_expired";
    return response;
  }

  // 409 Period Locked
  if (response.status === 409) {
    try {
      const cloned = response.clone();
      const body = await cloned.json();
      const detail = body?.detail;
      if (detail && typeof detail === "object" && detail.code === "PERIOD_LOCKED") {
        window.dispatchEvent(new CustomEvent("period_locked", { detail }));
      }
    } catch (_) {}
  }

  // 403 Feature not available
  if (response.status === 403) {
    try {
      const cloned = response.clone();
      const body = await cloned.json();
      const detail = body?.detail;
      if (detail && typeof detail === "object" && detail.error === "feature_not_available") {
        window.dispatchEvent(new CustomEvent("feature_not_available", { detail }));
      }
    } catch (_) {}
  }

  // 403 CSRF token errors — refresh token and optionally retry
  if (response.status === 403) {
    try {
      const cloned = response.clone();
      const body = await cloned.json();
      if (body?.code === "CSRF_MISSING" || body?.code === "CSRF_INVALID") {
        // Fetch a fresh CSRF cookie from a safe GET endpoint
        await fetch(url.replace(/\/api\/.*/, "/api/health"), { credentials: "include" });
      }
    } catch (_) {}
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
