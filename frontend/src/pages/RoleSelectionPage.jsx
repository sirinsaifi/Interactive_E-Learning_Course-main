/**
 * RoleSelectionPage — removed.
 *
 * Role is now assigned automatically on login based on the server's
 * INSTRUCTOR_EMAIL configuration. This file is kept as a redirect stub
 * so that any stale link lands somewhere sensible.
 */
import { Navigate } from "react-router-dom";

export default function RoleSelectionPage() {
  return <Navigate to="/" replace />;
}
