import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

/**
 * Gate a route behind the instructor role (or admin). Anonymous users are
 * bounced to /login first.
 */
export default function AdminRoute({ children }) {
  const { isAuthenticated, canManageCourses } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (!canManageCourses) {
    return (
      <section className="mx-auto max-w-md py-12">
        <div className="rounded-2xl border border-danger/30 bg-danger-soft p-6 text-center">
          <h1 className="text-lg font-semibold text-danger-soft-fg">Instructors only</h1>
          <p className="mt-2 text-sm text-danger-soft-fg/90">
            This page requires the instructor role on your account.
          </p>
        </div>
      </section>
    );
  }

  return children;
}
