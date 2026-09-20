import apiClient from "./apiClient.js";

export const adminService = {
  listUsers: () => apiClient.get("/admin/users").then((r) => r.data),
  getStats: () => apiClient.get("/admin/stats").then((r) => r.data),
  triggerSync: ({ prune = false } = {}) =>
    apiClient
      .post(`/admin/content/sync${prune ? "?prune=true" : ""}`)
      .then((r) => r.data),
};
