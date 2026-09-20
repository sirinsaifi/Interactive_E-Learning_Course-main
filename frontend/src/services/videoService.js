import apiClient from "./apiClient.js";

const API_BASE = apiClient.defaults.baseURL || "/api/v1";

export const videoService = {
  get: (id) => apiClient.get(`/videos/${id}`).then((r) => r.data),
  /**
   * Returns a URL suitable for the <video> `src` attribute.
   * The browser issues Range requests automatically.
   */
  streamUrl: (id) => `${API_BASE}/videos/${id}/stream`,
};
