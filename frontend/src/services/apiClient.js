import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

const apiClient = axios.create({
  baseURL,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

// ---- Auth wiring ----
// Token is held in module scope and synchronized by AuthContext. We avoid
// reading localStorage on every request and keep AuthContext as the single
// source of truth for login/logout side effects.
let currentToken = null;
let onUnauthorized = null;

export function setAuthToken(token) {
  currentToken = token || null;
}

export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

apiClient.interceptors.request.use((config) => {
  if (currentToken) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${currentToken}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401 && typeof onUnauthorized === "function") {
      onUnauthorized();
    }
    if (import.meta.env.DEV) {
      // eslint-disable-next-line no-console
      console.error("[api]", error?.response?.status, error?.config?.url, error?.response?.data);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
