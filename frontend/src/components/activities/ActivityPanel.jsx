import { useCallback, useEffect, useState } from "react";

import Spinner from "../Spinner.jsx";
import { activityService } from "../../services/activityService.js";
import FlashcardsActivity from "./FlashcardsActivity.jsx";
import MatchingActivity from "./MatchingActivity.jsx";
import OrderingActivity from "./OrderingActivity.jsx";

/** Renders one activity (fetched by id) using the component for its kind. */
export default function ActivityPanel({ activityId, sectionTitle, onCompleted }) {
  const [activity, setActivity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [justCompleted, setJustCompleted] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    setJustCompleted(false);
    try {
      setActivity(await activityService.get(activityId));
    } catch (e) {
      setError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to load activity."
      );
    } finally {
      setLoading(false);
    }
  }, [activityId]);

  useEffect(() => {
    if (Number.isFinite(activityId)) load();
  }, [activityId, load]);

  const handleCompleted = useCallback(async () => {
    try {
      await activityService.markComplete(activityId);
      setJustCompleted(true);
      if (onCompleted) onCompleted(activityId);
    } catch {
      // Non-fatal — the learner already saw the success state.
    }
  }, [activityId, onCompleted]);

  if (loading) {
    return (
      <div className="rounded-2xl border border-line bg-surface p-6">
        <Spinner label="Loading activity…" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-danger/30 bg-danger-soft p-4 text-sm text-danger-soft-fg">
        {error}
      </div>
    );
  }

  if (!activity) return null;

  return (
    <section className="animate-fade-up rounded-2xl border border-line bg-surface p-5 shadow-[var(--shadow-card)]">
      <header className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-brand-700">
            {kindLabel(activity.kind)}
            {sectionTitle ? ` · ${sectionTitle}` : ""}
          </p>
          <h2 className="text-lg font-semibold text-fg">{activity.title}</h2>
        </div>
        {justCompleted && (
          <span className="animate-bounce-in inline-flex items-center gap-1 rounded-full bg-success-soft px-3 py-1 text-xs font-semibold text-success-soft-fg shadow-sm">
            ✓ Activity completed
          </span>
        )}
      </header>
      <ActivityBody activity={activity} onCompleted={handleCompleted} />
    </section>
  );
}

function ActivityBody({ activity, onCompleted }) {
  if (activity.kind === "matching")
    return <MatchingActivity activity={activity} onCompleted={onCompleted} />;
  if (activity.kind === "flashcards")
    return <FlashcardsActivity activity={activity} onCompleted={onCompleted} />;
  if (activity.kind === "ordering")
    return <OrderingActivity activity={activity} onCompleted={onCompleted} />;
  return (
    <p className="text-sm text-fg-subtle">
      Unsupported activity type: <code>{activity.kind}</code>
    </p>
  );
}

function kindLabel(kind) {
  if (kind === "matching") return "Drag & Drop Matching";
  if (kind === "flashcards") return "Flip Flashcards";
  if (kind === "ordering") return "Sequence / Ordering";
  return "Activity";
}
