import { useAuth } from "../context/AuthContext.jsx";
import { useProgress } from "../context/ProgressContext.jsx";
import { useVideoPlayer } from "../context/VideoPlayerContext.jsx";
import { formatDuration } from "../utils/format.js";

function statusFor(progress) {
  if (!progress) return "none";
  if (progress.completed) return "done";
  if ((progress.position_seconds || 0) > 0) return "partial";
  return "none";
}

/**
 * Returns a Set of section IDs that are locked.
 * A section is fully complete only when:
 *   - all its videos are completed, AND
 *   - its quiz (if any) has been passed.
 * Instructors/admins are never locked.
 */
function computeLockedSections(sections, byVideoId, passedQuizIds, isInstructor) {
  if (isInstructor) return new Set();
  const locked = new Set();
  const sorted = [...(sections || [])].sort((a, b) => a.order_index - b.order_index);
  for (let i = 1; i < sorted.length; i++) {
    const prev = sorted[i - 1];
    const prevVideos = prev.videos || [];
    // All videos must be completed
    const videosComplete =
      prevVideos.length > 0 &&
      prevVideos.every((v) => byVideoId?.[v.id]?.completed === true);
    // Quiz (if any) must also be passed
    const quizComplete =
      !prev.quiz || passedQuizIds?.has(prev.quiz.id);
    const prevComplete = videosComplete && quizComplete;
    if (!prevComplete) {
      // Lock this section and all after it
      for (let j = i; j < sorted.length; j++) {
        locked.add(sorted[j].id);
      }
      break;
    }
  }
  return locked;
}

export default function PlaylistSidebar() {
  const {
    course,
    currentVideo,
    currentQuiz,
    currentActivity,
    selectVideo,
    selectQuiz,
    selectActivity,
  } = useVideoPlayer();
  const { byVideoId, passedQuizIds } = useProgress();
  const { isInstructor, isAdmin } = useAuth();

  if (!course) return null;

  const canBypassLock = isInstructor || isAdmin;
  const lockedSections = computeLockedSections(course.sections, byVideoId, passedQuizIds, canBypassLock);

  return (
    <aside className="flex h-full max-h-[80vh] flex-col overflow-hidden rounded-2xl border border-line bg-surface shadow-[var(--shadow-card)]">
      <header className="border-b border-line px-4 py-3">
        <h3 className="text-sm font-semibold text-fg">Course content</h3>
        <p className="text-xs text-fg-subtle">
          {course.sections?.length ?? 0} sections
        </p>
      </header>

      <div className="flex-1 overflow-y-auto">
        {(course.sections || []).map((section) => {
          const isLocked = lockedSections.has(section.id);
          return (
            <section key={section.id} className="border-b border-line last:border-b-0">
              {/* Section header */}
              <div
                className={`px-4 py-2 flex items-center gap-2 ${
                  isLocked ? "bg-muted/40 opacity-70" : "bg-muted/60"
                }`}
              >
                {isLocked && (
                  <span title="Complete the previous module to unlock" className="text-fg-subtle shrink-0">
                    <svg viewBox="0 0 20 20" fill="currentColor" className="h-3.5 w-3.5">
                      <path
                        fillRule="evenodd"
                        d="M10 1a4.5 4.5 0 00-4.5 4.5V9H5a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2v-6a2 2 0 00-2-2h-.5V5.5A4.5 4.5 0 0010 1zm3 8V5.5a3 3 0 10-6 0V9h6z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </span>
                )}
                <div className="min-w-0">
                  <p className="text-xs font-semibold uppercase tracking-wide text-fg-muted truncate">
                    {section.title}
                  </p>
                  <p className="text-[11px] text-fg-subtle">
                    {section.videos?.length ?? 0} {section.videos?.length === 1 ? "module" : "modules"}
                    {section.activities?.length
                      ? ` · ${section.activities.length} activit${
                          section.activities.length === 1 ? "y" : "ies"
                        }`
                      : ""}
                    {section.quiz ? " · quiz" : ""}
                    {isLocked ? " · 🔒 Locked" : ""}
                  </p>
                </div>
              </div>

              {/* Section items */}
              <ul>
                {(section.videos || []).map((video, idx) => {
                  const isActive =
                    currentQuiz == null && currentVideo?.id === video.id;
                  const status = statusFor(byVideoId?.[video.id]);
                  return (
                    <li key={video.id}>
                      {isLocked ? (
                        /* Locked item — not clickable */
                        <div
                          className="flex w-full items-start gap-3 px-4 py-2.5 text-sm opacity-40 cursor-not-allowed select-none"
                          title="Complete the previous module to unlock this one"
                        >
                          <LockBadge />
                          <span className="flex-1 truncate text-fg-muted">
                            {video.title}
                          </span>
                          {video.duration_seconds != null && (
                            <span className="shrink-0 text-xs text-fg-subtle">
                              {formatDuration(video.duration_seconds)}
                            </span>
                          )}
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => selectVideo(video.id)}
                          className={`flex w-full items-start gap-3 px-4 py-2.5 text-left text-sm transition-colors ${
                            isActive
                              ? "bg-brand-50 text-brand-700"
                              : "text-fg-muted hover:bg-muted hover:text-fg"
                          }`}
                        >
                          <StatusBadge status={status} isActive={isActive} index={idx + 1} />
                          <span
                            className={`flex-1 truncate ${
                              status === "done" && !isActive ? "text-fg-subtle" : ""
                            }`}
                          >
                            {video.title}
                          </span>
                          {video.duration_seconds != null && (
                            <span className="shrink-0 text-xs text-fg-subtle">
                              {formatDuration(video.duration_seconds)}
                            </span>
                          )}
                        </button>
                      )}
                    </li>
                  );
                })}

                {(section.activities || []).map((activity) => {
                  const isActive = currentActivity?.activityId === activity.id;
                  return (
                    <li key={`act-${activity.id}`}>
                      {isLocked ? (
                        <div
                          className="flex w-full items-start gap-3 px-4 py-2.5 text-sm opacity-40 cursor-not-allowed select-none"
                          title="Complete the previous module to unlock"
                        >
                          <LockBadge />
                          <span className="flex-1 truncate font-medium text-fg-muted">
                            {activity.title}
                          </span>
                          <span className="shrink-0 text-[10px] uppercase tracking-wide text-fg-subtle">
                            {activityShort(activity.kind)}
                          </span>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => selectActivity(section.id, activity.id)}
                          className={`flex w-full items-start gap-3 px-4 py-2.5 text-left text-sm transition-colors ${
                            isActive
                              ? "bg-brand-50 text-brand-700"
                              : "text-fg-muted hover:bg-muted hover:text-fg"
                          }`}
                        >
                          <ActivityBadge kind={activity.kind} isActive={isActive} />
                          <span className="flex-1 truncate font-medium">
                            {activity.title}
                          </span>
                          <span className="shrink-0 text-[10px] uppercase tracking-wide text-fg-subtle">
                            {activityShort(activity.kind)}
                          </span>
                        </button>
                      )}
                    </li>
                  );
                })}

                {section.quiz && (
                  <li>
                    {isLocked ? (
                      <div
                        className="flex w-full items-start gap-3 px-4 py-2.5 text-sm opacity-40 cursor-not-allowed select-none"
                        title="Complete the previous module to unlock this quiz"
                      >
                        <LockBadge />
                        <span className="flex-1 truncate font-medium text-fg-muted">
                          Section quiz
                        </span>
                        <span className="shrink-0 text-xs text-fg-subtle">
                          {section.quiz.question_count} Qs
                        </span>
                      </div>
                    ) : (
                      <button
                        type="button"
                        onClick={() => selectQuiz(section.id, section.quiz.id)}
                        className={`flex w-full items-start gap-3 px-4 py-2.5 text-left text-sm transition-colors ${
                          currentQuiz?.quizId === section.quiz.id
                            ? "bg-brand-50 text-brand-700"
                            : "text-fg-muted hover:bg-muted hover:text-fg"
                        }`}
                      >
                        <span
                          className={`mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full ${
                            currentQuiz?.quizId === section.quiz.id
                              ? "bg-brand-600 text-brand-fg"
                              : "bg-accent-soft text-accent-soft-fg"
                          }`}
                          title="Section quiz"
                        >
                          <svg viewBox="0 0 20 20" className="h-3 w-3" fill="currentColor" aria-hidden="true">
                            <path d="M10 2a8 8 0 100 16 8 8 0 000-16zm.75 12.5h-1.5v-1.5h1.5v1.5zM12 8.5c0 .9-.4 1.4-1.1 1.9-.6.4-.9.6-.9 1.1H8.5c0-1 .5-1.4 1.2-1.9.5-.4.8-.6.8-1.1 0-.5-.4-.9-1-.9s-1 .4-1.1.9H7c.1-1.3 1.1-2.3 2.5-2.3S12 7.2 12 8.5z" />
                          </svg>
                        </span>
                        <span className="flex-1 truncate font-medium">
                          Section quiz
                        </span>
                        <span className="shrink-0 text-xs text-fg-subtle">
                          {section.quiz.question_count} Qs
                        </span>
                      </button>
                    )}
                  </li>
                )}
              </ul>
            </section>
          );
        })}
      </div>
    </aside>
  );
}

function LockBadge() {
  return (
    <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-muted text-fg-subtle">
      <svg viewBox="0 0 20 20" fill="currentColor" className="h-3 w-3" aria-hidden="true">
        <path
          fillRule="evenodd"
          d="M10 1a4.5 4.5 0 00-4.5 4.5V9H5a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2v-6a2 2 0 00-2-2h-.5V5.5A4.5 4.5 0 0010 1zm3 8V5.5a3 3 0 10-6 0V9h6z"
          clipRule="evenodd"
        />
      </svg>
    </span>
  );
}

function StatusBadge({ status, isActive, index }) {
  if (status === "done") {
    return (
      <span
        title="Completed"
        className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-success text-white"
      >
        <svg viewBox="0 0 20 20" className="h-3 w-3" fill="currentColor" aria-hidden="true">
          <path
            fillRule="evenodd"
            d="M16.704 5.29a1 1 0 010 1.42l-7.5 7.5a1 1 0 01-1.414 0l-3.5-3.5a1 1 0 111.414-1.414l2.793 2.793 6.793-6.793a1 1 0 011.414 0z"
            clipRule="evenodd"
          />
        </svg>
      </span>
    );
  }
  return (
    <span
      className={`mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold ${
        isActive
          ? "bg-brand-600 text-brand-fg"
          : status === "partial"
          ? "bg-warning-soft text-warning-soft-fg ring-1 ring-warning/40"
          : "bg-muted text-fg-subtle"
      }`}
      title={status === "partial" ? "In progress" : undefined}
    >
      {index}
    </span>
  );
}

function ActivityBadge({ kind, isActive }) {
  const icon =
    kind === "matching" ? "⇋" : kind === "flashcards" ? "⇋" : "≡";
  const label =
    kind === "matching"
      ? "Matching activity"
      : kind === "flashcards"
      ? "Flashcards"
      : "Ordering";
  return (
    <span
      title={label}
      className={`mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold ${
        isActive
          ? "bg-brand-600 text-brand-fg"
          : "bg-accent-soft text-accent-soft-fg"
      }`}
    >
      {kind === "flashcards" ? "🂠" : icon}
    </span>
  );
}

function activityShort(kind) {
  if (kind === "matching") return "Match";
  if (kind === "flashcards") return "Cards";
  if (kind === "ordering") return "Order";
  return "";
}
