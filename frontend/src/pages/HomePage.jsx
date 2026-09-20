import { useCallback } from "react";
import { Link } from "react-router-dom";

import CourseCard from "../components/CourseCard.jsx";
import Spinner from "../components/Spinner.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import useFetch from "../hooks/useFetch.js";
import { courseService } from "../services/courseService.js";

export default function HomePage() {
  const { canManageCourses } = useAuth();
  const fetcher = useCallback(() => courseService.list(), []);
  const { data, error, loading } = useFetch(fetcher, []);

  const featured = (data || []).slice(0, 6);

  return (
    <section className="space-y-10">
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-brand-600 via-brand-600 to-brand-700 p-8 text-brand-fg shadow-[var(--shadow-pop)] sm:p-12">
        <div className="absolute inset-0 opacity-30 [mask-image:radial-gradient(circle_at_top_right,white,transparent_70%)]">
          <div className="absolute -top-24 -right-24 h-72 w-72 rounded-full bg-white/30 blur-3xl" />
          <div className="absolute -bottom-24 -left-16 h-72 w-72 rounded-full bg-brand-500/40 blur-3xl" />
        </div>
        <div className="relative max-w-2xl">
          <span className="inline-flex items-center gap-1 rounded-full bg-white/15 px-3 py-1 text-xs font-medium uppercase tracking-wide ring-1 ring-white/20">
            <span className="h-1.5 w-1.5 rounded-full bg-white" />
            Stream &amp; resume seamlessly
          </span>
          <h1 className="mt-4 text-4xl font-bold tracking-tight sm:text-5xl">
            Learn at your own pace.
          </h1>
          <p className="mt-3 max-w-xl text-base text-white/85 sm:text-lg">
            Browse the catalog, pick a course, and pick up exactly where you left off.
          </p>
          <Link
            to="/courses"
            className="mt-6 inline-flex items-center gap-2 rounded-full bg-white px-5 py-2.5 text-sm font-semibold text-brand-700 shadow-sm transition hover:bg-white/90"
          >
            Browse all courses
            <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4" aria-hidden="true">
              <path fillRule="evenodd" d="M3 10a.75.75 0 0 1 .75-.75h10.638l-3.69-3.41a.75.75 0 1 1 1.018-1.1l5.25 4.85a.75.75 0 0 1 0 1.1l-5.25 4.85a.75.75 0 1 1-1.018-1.1l3.69-3.41H3.75A.75.75 0 0 1 3 10Z" clipRule="evenodd" />
            </svg>
          </Link>
        </div>
      </div>

      <div>
        <div className="mb-4 flex items-end justify-between">
          <div>
            <h2 className="text-xl font-semibold text-fg">Featured courses</h2>
            <p className="text-sm text-fg-subtle">Hand-picked starting points.</p>
          </div>
          <Link to="/courses" className="text-sm font-medium text-brand-700 hover:text-brand-600">
            See all →
          </Link>
        </div>

        {loading && <Spinner label="Loading courses…" />}

        {error && (
          <div className="rounded-2xl border border-danger/30 bg-danger-soft p-4 text-sm text-danger-soft-fg">
            Failed to load courses. Is the backend running?
          </div>
        )}

        {!loading && !error && featured.length === 0 && (
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

        {!loading && !error && featured.length > 0 && (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {featured.map((c) => (
              <CourseCard key={c.id} course={c} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
