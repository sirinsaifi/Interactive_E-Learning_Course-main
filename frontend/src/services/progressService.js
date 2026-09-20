import apiClient from "./apiClient.js";

export const progressService = {
  /** Heartbeat: tell the server where the user currently is in a video. */
  updateVideoProgress: (videoId, { positionSeconds, durationSeconds }) =>
    apiClient
      .put(`/videos/${videoId}/progress`, {
        position_seconds: Math.max(0, Math.floor(positionSeconds || 0)),
        duration_seconds:
          durationSeconds && Number.isFinite(durationSeconds)
            ? Math.floor(durationSeconds)
            : null,
      })
      .then((r) => r.data),

  /** Explicit completion (called on the 'ended' event). */
  markVideoComplete: (videoId) =>
    apiClient.post(`/videos/${videoId}/progress/complete`).then((r) => r.data),

  /** Full progress summary for a single course. */
  getCourseProgress: (courseId) =>
    apiClient.get(`/courses/${courseId}/progress`).then((r) => r.data),

  /** Courses the current user has any progress on (Continue Learning). */
  listMyCourses: () =>
    apiClient.get("/me/progress/courses").then((r) => r.data),
};
