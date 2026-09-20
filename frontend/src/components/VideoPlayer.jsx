import { useEffect, useRef, useState } from "react";

import { useAuth } from "../context/AuthContext.jsx";
import { useProgress } from "../context/ProgressContext.jsx";
import { useVideoPlayer } from "../context/VideoPlayerContext.jsx";
import { videoService } from "../services/videoService.js";

export default function VideoPlayer() {
  const { currentVideo, playNext, hasNext, hasPrevious, playPrevious, course } =
    useVideoPlayer();
  const { byVideoId, recordPosition, markComplete, passedQuizIds } = useProgress();
  const { isInstructor, isAdmin } = useAuth();
  const videoRef = useRef(null);
  const resumedRef = useRef(null);
  const [htmlCompleted, setHtmlCompleted] = useState(false);

  const isHtml = currentVideo?.content_type === "html";
  const canBypassLock = isInstructor || isAdmin;

  // Determine whether the current section's quiz (if any) has been passed.
  // Instructors/admins bypass this gate.
  const currentSectionQuizPassed = (() => {
    if (canBypassLock) return true;
    if (!currentVideo || !course) return true;
    const section = course.sections?.find((s) => s.id === currentVideo.sectionId);
    if (!section?.quiz) return true; // no quiz → no gate
    return passedQuizIds?.has(section.quiz.id) ?? false;
  })();

  // Next is allowed only if there's a next item AND the current section quiz is passed.
  const canGoNext = hasNext && currentSectionQuizPassed;

  // When the selected video changes, reload <video> and reset HTML state.
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.load();
      resumedRef.current = null;
    }
    setHtmlCompleted(false);
  }, [currentVideo?.id]);

  // For HTML modules: auto-mark complete after 5 s so the learner can
  // proceed. They can also click "Mark Complete" manually.
  useEffect(() => {
    if (!isHtml || !currentVideo) return;
    const already = byVideoId?.[currentVideo.id]?.completed;
    if (already) {
      setHtmlCompleted(true);
      return;
    }
    const timer = setTimeout(async () => {
      await markComplete(currentVideo.id);
      setHtmlCompleted(true);
    }, 5000);
    return () => clearTimeout(timer);
  }, [currentVideo?.id, isHtml]);

  if (!currentVideo) {
    return (
      <div className="flex aspect-video w-full items-center justify-center rounded-2xl border border-line bg-black/95 text-sm text-fg-subtle">
        Select a module to start learning
      </div>
    );
  }

  // ── Video handlers ──────────────────────────────────────────────────────────

  const handleLoadedMetadata = () => {
    const el = videoRef.current;
    if (!el || resumedRef.current === currentVideo.id) return;
    resumedRef.current = currentVideo.id;
    const saved = byVideoId?.[currentVideo.id];
    if (!saved) return;
    const duration = el.duration || saved.position_seconds + 10;
    if (saved.completed) return;
    if (saved.position_seconds > 2 && saved.position_seconds < duration - 5) {
      try {
        el.currentTime = saved.position_seconds;
      } catch {
        /* ignore */
      }
    }
  };

  const handleTimeUpdate = () => {
    const el = videoRef.current;
    if (!el) return;
    recordPosition(currentVideo.id, el.currentTime, el.duration || null);
  };

  const handleEnded = async () => {
    await markComplete(currentVideo.id);
    // No auto-advance: learner must pass the section quiz first.
  };

  // ── HTML module manual mark-complete ────────────────────────────────────────

  const handleMarkComplete = async () => {
    await markComplete(currentVideo.id);
    setHtmlCompleted(true);
    // No auto-advance: learner must pass the section quiz first.
  };

  // ── Render ───────────────────────────────────────────────────────────────────

  const streamUrl = videoService.streamUrl(currentVideo.id);

  // Tooltip for a disabled Next button so learner knows why.
  const nextTitle = !hasNext
    ? undefined
    : !currentSectionQuizPassed
    ? "Pass this section's quiz to continue to the next module"
    : undefined;

  return (
    <div className="space-y-4">
      <div className="overflow-hidden rounded-2xl bg-white shadow-[var(--shadow-pop)] ring-1 ring-line">
        {isHtml ? (
          <iframe
            key={currentVideo.id}
            src={streamUrl}
            title={currentVideo.title}
            className="w-full border-0"
            style={{ height: "70vh", minHeight: "480px" }}
            sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
            allow="fullscreen"
          />
        ) : (
          <video
            ref={videoRef}
            key={currentVideo.id}
            className="aspect-video w-full bg-black"
            controls
            preload="metadata"
            playsInline
            onLoadedMetadata={handleLoadedMetadata}
            onTimeUpdate={handleTimeUpdate}
            onEnded={handleEnded}
          >
            <source src={streamUrl} />
            Your browser does not support the video tag.
          </video>
        )}
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-wide text-fg-subtle">
            {currentVideo.sectionTitle}
          </p>
          <h2 className="truncate text-lg font-semibold text-fg">
            {currentVideo.title}
          </h2>
        </div>
        <div className="flex shrink-0 gap-2">
          {isHtml && !htmlCompleted && (
            <button
              type="button"
              onClick={handleMarkComplete}
              className="rounded-full border border-brand-600 px-4 py-1.5 text-sm font-medium text-brand-600 transition hover:bg-brand-50"
            >
              ✓ Mark Complete
            </button>
          )}
          <button
            type="button"
            onClick={playPrevious}
            disabled={!hasPrevious}
            className="rounded-full border border-line bg-surface px-4 py-1.5 text-sm font-medium text-fg-muted transition hover:text-fg hover:border-line-strong disabled:cursor-not-allowed disabled:opacity-50"
          >
            ← Previous
          </button>
          <button
            type="button"
            onClick={canGoNext ? playNext : undefined}
            disabled={!canGoNext}
            title={nextTitle}
            className="rounded-full bg-brand-600 px-4 py-1.5 text-sm font-medium text-brand-fg shadow-sm transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Next →
          </button>
        </div>
      </div>

      {!currentSectionQuizPassed && hasNext && (
        <p className="text-xs text-fg-subtle">
          📝 Complete and pass the section quiz to unlock the next module.
        </p>
      )}

      {currentVideo.description && (
        <p className="text-sm text-fg-muted">{currentVideo.description}</p>
      )}
    </div>
  );
}
