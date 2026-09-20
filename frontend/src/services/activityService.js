import apiClient from "./apiClient.js";

/** Public/learner endpoints for interactive activities. */
export const activityService = {
  listForSection: (sectionId) =>
    apiClient.get(`/sections/${sectionId}/activities`).then((r) => r.data),
  get: (activityId) =>
    apiClient.get(`/activities/${activityId}`).then((r) => r.data),
  markComplete: (activityId) =>
    apiClient
      .post(`/activities/${activityId}/complete`)
      .then((r) => r.data),
};

/** Instructor CRUD for interactive activities. */
export const instructorActivityService = {
  listForSection: (sectionId) =>
    apiClient
      .get(`/instructor/sections/${sectionId}/activities`)
      .then((r) => r.data),
  create: (sectionId, payload) =>
    apiClient
      .post(`/instructor/sections/${sectionId}/activities`, payload)
      .then((r) => r.data),
  update: (activityId, payload) =>
    apiClient
      .patch(`/instructor/activities/${activityId}`, payload)
      .then((r) => r.data),
  remove: (activityId) =>
    apiClient.delete(`/instructor/activities/${activityId}`).then((r) => r.data),
};
