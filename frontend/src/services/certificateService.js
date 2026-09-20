import apiClient from "./apiClient.js";

export const certificateService = {
  /** Returns { eligible, total_videos, completed_videos, total_quizzes,
   *  passed_quizzes, completion_date, reason }. */
  getEligibility: (courseId) =>
    apiClient
      .get(`/courses/${courseId}/certificate/eligibility`)
      .then((r) => r.data),

  /** Streams the PDF and triggers a browser download. We have to fetch with
   *  auth headers (Bearer token), so a plain <a href> won't work. */
  download: async (courseId, filenameHint) => {
    const res = await apiClient.get(`/courses/${courseId}/certificate`, {
      responseType: "blob",
    });
    const blob = new Blob([res.data], { type: "application/pdf" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filenameHint || `course-${courseId}-certificate.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
