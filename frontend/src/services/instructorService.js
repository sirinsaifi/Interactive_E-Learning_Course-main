import apiClient from "./apiClient.js";

/**
 * Calls into `/instructor/*` and `/admin/*` endpoints for course management.
 * The same `instructorService` is used by admins (who can see/edit every
 * course) and instructors (who only see their own).
 */
export const instructorService = {
  // ---- Courses ----
  listMyCourses: () =>
    apiClient.get("/instructor/courses").then((r) => r.data),
  getCourse: (courseId) =>
    apiClient.get(`/instructor/courses/${courseId}`).then((r) => r.data),
  createCourse: (payload) =>
    apiClient.post("/instructor/courses", payload).then((r) => r.data),
  updateCourse: (courseId, payload) =>
    apiClient.patch(`/instructor/courses/${courseId}`, payload).then((r) => r.data),
  deleteCourse: (courseId) =>
    apiClient.delete(`/instructor/courses/${courseId}`).then((r) => r.data),

  // ---- Sections ----
  addSection: (courseId, payload) =>
    apiClient
      .post(`/instructor/courses/${courseId}/sections`, payload)
      .then((r) => r.data),
  updateSection: (sectionId, payload) =>
    apiClient.patch(`/instructor/sections/${sectionId}`, payload).then((r) => r.data),
  deleteSection: (sectionId) =>
    apiClient.delete(`/instructor/sections/${sectionId}`).then((r) => r.data),

  // ---- Videos ----
  uploadVideo: (sectionId, file, { title, description, onProgress } = {}) => {
    const form = new FormData();
    form.append("file", file);
    if (title) form.append("title", title);
    if (description) form.append("description", description);
    return apiClient
      .post(`/instructor/sections/${sectionId}/videos`, form, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 0,
        onUploadProgress: (evt) => {
          if (onProgress && evt.total) {
            onProgress(Math.round((evt.loaded * 100) / evt.total));
          }
        },
      })
      .then((r) => r.data);
  },
  updateVideo: (videoId, payload) =>
    apiClient.patch(`/instructor/videos/${videoId}`, payload).then((r) => r.data),
  deleteVideo: (videoId) =>
    apiClient.delete(`/instructor/videos/${videoId}`).then((r) => r.data),

  // ---- Quizzes (editor view, includes correct answers) ----
  getQuizForEdit: (quizId) =>
    apiClient.get(`/instructor/quizzes/${quizId}`).then((r) => r.data),
  updateQuizMeta: (quizId, payload) =>
    apiClient.patch(`/instructor/quizzes/${quizId}`, payload).then((r) => r.data),
  updateQuestion: (quizId, questionId, payload) =>
    apiClient
      .patch(`/instructor/quizzes/${quizId}/questions/${questionId}`, payload)
      .then((r) => r.data),

  // ---- Interactive activities ----
  listActivities: (sectionId) =>
    apiClient
      .get(`/instructor/sections/${sectionId}/activities`)
      .then((r) => r.data),
  createActivity: (sectionId, payload) =>
    apiClient
      .post(`/instructor/sections/${sectionId}/activities`, payload)
      .then((r) => r.data),
  updateActivity: (activityId, payload) =>
    apiClient
      .patch(`/instructor/activities/${activityId}`, payload)
      .then((r) => r.data),
  deleteActivity: (activityId) =>
    apiClient
      .delete(`/instructor/activities/${activityId}`)
      .then((r) => r.data),
};

/** Admin-only endpoints related to instructor / course assignment. */
export const adminInstructorService = {
  setUserRole: (userId, role) =>
    apiClient.post(`/admin/users/${userId}/role`, { role }).then((r) => r.data),
  assignInstructor: (courseId, instructorId) =>
    apiClient
      .post(`/admin/courses/${courseId}/instructor`, {
        instructor_id: instructorId,
      })
      .then((r) => r.data),
};
