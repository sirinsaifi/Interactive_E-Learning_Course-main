import apiClient from "./apiClient.js";

export const quizService = {
  /** Fetch a quiz by section id (questions without correct answers). */
  getForSection: (sectionId) =>
    apiClient.get(`/sections/${sectionId}/quiz`).then((r) => r.data),

  /** Fetch a quiz by its own id (questions without correct answers). */
  getById: (quizId) =>
    apiClient.get(`/quizzes/${quizId}`).then((r) => r.data),

  /** Submit selected answers (array of 0-3 indices) and receive graded result. */
  submit: (quizId, answers) =>
    apiClient
      .post(`/quizzes/${quizId}/attempts`, { answers })
      .then((r) => r.data),

  /** Latest attempt for the current user on a quiz. */
  getMyAttempt: (quizId) =>
    apiClient.get(`/quizzes/${quizId}/my-attempt`).then((r) => r.data),

  /** All quiz IDs the current user has passed for a course. */
  getPassedForCourse: (courseId) =>
    apiClient.get(`/courses/${courseId}/passed-quizzes`).then((r) => r.data),
};
