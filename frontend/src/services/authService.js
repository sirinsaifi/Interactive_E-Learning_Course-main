import apiClient from "./apiClient.js";

export const authService = {
  /**
   * Log in with an email address. The server determines the role (instructor
   * or learner) based on the configured INSTRUCTOR_EMAIL env var.
   */
  loginWithEmail: (email) =>
    apiClient.post("/auth/login", { email }).then((r) => r.data),

  /** Log out the current session on the server. */
  logout: () =>
    apiClient.post("/auth/logout").then((r) => r.data).catch(() => {}),

  /** Get the currently authenticated user. Requires the bearer token. */
  me: () => apiClient.get("/auth/me").then((r) => r.data),
};
