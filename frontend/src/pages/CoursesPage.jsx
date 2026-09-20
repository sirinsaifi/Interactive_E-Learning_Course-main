import { useCallback } from "react";

import CourseCard from "../components/CourseCard.jsx";
import Spinner from "../components/Spinner.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import useFetch from "../hooks/useFetch.js";
import { courseService } from "../services/courseService.js";

export default function CoursesPage() {
  const { canManageCourses } = useAuth();
  const fetcher = useCallback(() => courseService.list(), []);
  const { data, error, loading, refetch } = useFetch(fetcher, []);

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-fg">All courses</h1>
          <p className="mt-1 text-sm text-fg-subtle">Browse the catalog and pick a course to start learning.</p>
        </div>
        <button
          type="button"
          onClick={refetch}
          className="rounded-full border border-line bg-surface px-4 py-1.5 text-sm font-medium text-fg-muted transition hover:text-fg hover:border-line-strong"
        >
          Refresh
        </button>
      </div>

      {loading && <Spinner label="Loading courses…" />}

      {error && (
        <div className="rounded-2xl border border-danger/30 bg-danger-soft p-4 text-sm text-danger-soft-fg">
          Failed to load courses. Is the backend running?
        </div>
      )}

      {!loading && !error && data?.length === 0 && (
        <div className="rounded-2xl border border-dashed border-line bg-surface p-10 text-center text-fg-subtle">
          {canManageCourses ? (
            <>
              No courses yet. Drop videos under{" "}
              <code className="rounded bg-muted px-1.5 py-0.5 text-fg-muted">backend/storage/videos/</code>
              {" "}and trigger a sync.
            </>
          ) : (
            <>No courses are available yet. Please check back soon.</>
          )}
        </div>
      )}

      {!loading && !error && data?.length > 0 && (
        <div className="stagger-children grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((c) => (
            <CourseCard key={c.id} course={c} />
          ))}
        </div>
      )}
    </section>
  );
}
