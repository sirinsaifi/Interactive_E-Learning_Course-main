import apiClient from "./apiClient.js";

export const courseService = {
  list: () => apiClient.get("/courses").then((r) => r.data),
  get: (id) => apiClient.get(`/courses/${id}`).then((r) => r.data),
};
