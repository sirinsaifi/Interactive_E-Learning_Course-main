import apiClient from "./apiClient.js";

export const healthService = {
  status: () => apiClient.get("/health").then((r) => r.data),
  live: () => apiClient.get("/health/live").then((r) => r.data),
  ready: () => apiClient.get("/health/ready").then((r) => r.data),
};
