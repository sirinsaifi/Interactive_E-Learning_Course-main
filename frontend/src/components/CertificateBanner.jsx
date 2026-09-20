import { useCallback, useEffect, useState } from "react";

import { certificateService } from "../services/certificateService.js";

/**
 * CertificateBanner — shows a "Download Certificate" CTA once the learner
 * has completed every video and passed every quiz in the course. While the
 * learner is still in progress, it shows a friendly hint of what's left.
 *
 * The banner refetches eligibility whenever `percentComplete` changes (so
 * it flips from "in progress" to "ready" as soon as the last video is
 * marked complete) and whenever `refreshKey` changes (use this to nudge a
 * recheck after a quiz pass).
 */
export default function CertificateBanner({
  courseId,
  courseTitle,
  percentComplete = 0,
  refreshKey = 0,
}) {
  const [state, setState] = useState({ loading: true, data: null, error: null });
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState(null);

  const fetchEligibility = useCallback(async () => {
    if (!Number.isFinite(courseId)) return;
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await certificateService.getEligibility(courseId);
      setState({ loading: false, data, error: null });
    } catch (err) {
      setState({
        loading: false,
        data: null,
        error: err?.response?.data?.error?.message || "Failed to load certificate status.",
      });
    }
  }, [courseId]);

  useEffect(() => {
    fetchEligibility();
  }, [fetchEligibility, percentComplete, refreshKey]);

  // Auto-refetch when the tab becomes visible or regains focus. This covers
  // the case where the user finished a quiz/video in another tab or where a
  // parent prop refresh somehow didn't fire (stale closure on first load).
  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === "visible") fetchEligibility();
    };
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("focus", fetchEligibility);
    return () => {
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("focus", fetchEligibility);
    };
  }, [fetchEligibility]);

  const handleDownload = async () => {
    setDownloading(true);
    setDownloadError(null);
    try {
      const safeTitle = (courseTitle || "course")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-|-$/g, "");
      await certificateService.download(courseId, `${safeTitle}-certificate.pdf`);
      // After a successful download, refresh once so the timestamp stays in sync.
      fetchEligibility();
    } catch (err) {
      setDownloadError(
        err?.response?.data?.error?.message || "Could not download the certificate."
      );
    } finally {
      setDownloading(false);
    }
  };

  if (state.loading && !state.data) return null;
  if (state.error) {
    return (
      <div className="mt-4 rounded-2xl border border-line bg-bg-elev px-4 py-3 text-xs text-fg-muted">
        {state.error}
      </div>
    );
  }

  const data = state.data;
  if (!data) return null;

  if (data.eligible) {
    const dateStr = data.completion_date
      ? new Date(data.completion_date).toLocaleDateString(undefined, {
          year: "numeric",
          month: "long",
          day: "numeric",
        })
      : null;
    return (
      <div className="animate-bounce-in mt-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-success/30 bg-success-soft px-4 py-3 shadow-[var(--shadow-card)]">
        <div className="text-sm">
          <p className="font-semibold text-success-soft-fg">
            Course completed{dateStr ? ` on ${dateStr}` : ""} 🎉
          </p>
          <p className="text-xs text-success-soft-fg/80">
            {data.completed_videos}/{data.total_videos} videos · {data.passed_quizzes}/
            {data.total_quizzes} quizzes passed · {data.completed_activities ?? 0}/
            {data.total_activities ?? 0} activities
          </p>
          {downloadError && (
            <p className="mt-1 text-xs text-danger">{downloadError}</p>
          )}
        </div>
        <button
          type="button"
          onClick={handleDownload}
          disabled={downloading}
          className="hover-lift animate-pulse-ring inline-flex items-center gap-2 rounded-xl bg-success px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-success/90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {downloading ? "Preparing…" : "Download Certificate (PDF)"}
        </button>
      </div>
    );
  }

  // Not eligible yet — small hint of what's left, plus a manual recheck.
  return (
    <div className="animate-fade-in mt-4 flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-line bg-bg-elev px-4 py-3 text-xs text-fg-muted">
      <span>
        <span className="font-medium text-fg">Certificate</span>:{" "}
        {data.reason ||
          `${data.completed_videos}/${data.total_videos} videos · ${data.passed_quizzes}/${data.total_quizzes} quizzes · ${data.completed_activities ?? 0}/${data.total_activities ?? 0} activities`}
        .
      </span>
      <button
        type="button"
        onClick={fetchEligibility}
        disabled={state.loading}
        className="rounded-full border border-line px-3 py-1 text-xs font-medium text-fg transition hover:border-line-strong hover:bg-surface disabled:opacity-50"
      >
        {state.loading ? "Checking…" : "Check again"}
      </button>
    </div>
  );
}
