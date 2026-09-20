import { Link } from "react-router-dom";

import { formatTotalDuration } from "../utils/format.js";

export default function CourseCard({ course }) {
  return (
    <Link
      to={`/courses/${course.id}`}
      className="group flex flex-col overflow-hidden rounded-2xl border border-line bg-surface shadow-[var(--shadow-card)] transition duration-200 hover:-translate-y-0.5 hover:border-line-strong hover:shadow-[var(--shadow-pop)]"
    >
      <div className="aspect-video overflow-hidden bg-muted">
        {course.thumbnail_url ? (
          <img
            src={course.thumbnail_url}
            alt={course.title}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
            loading="lazy"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-brand-500 to-brand-700 text-2xl font-semibold text-brand-fg">
            {course.title?.[0] ?? "?"}
          </div>
        )}
      </div>
      <div className="flex flex-col gap-2 p-5">
        <h3 className="line-clamp-2 text-base font-semibold text-fg transition-colors group-hover:text-brand-700">
          {course.title}
        </h3>
        {course.instructor && (
          <p className="text-xs text-fg-subtle">by {course.instructor}</p>
        )}
        {course.description && (
          <p className="line-clamp-2 text-sm text-fg-muted">{course.description}</p>
        )}
        <div className="mt-auto flex flex-wrap items-center gap-x-3 gap-y-1 pt-2 text-xs text-fg-subtle">
          <span>{course.section_count} sections</span>
          <span className="text-line-strong">·</span>
          <span>{course.video_count} videos</span>
          <span className="text-line-strong">·</span>
          <span>{formatTotalDuration(course.total_duration_seconds)}</span>
        </div>
      </div>
    </Link>
  );
}
