import { useCallback, useEffect, useState } from "react";

import Spinner from "../Spinner.jsx";
import { instructorService } from "../../services/instructorService.js";

const KIND_OPTIONS = [
  { value: "matching", label: "Drag & Drop Matching" },
  { value: "flashcards", label: "Flip Flashcards" },
  { value: "ordering", label: "Sequence / Ordering" },
];

function emptyPayloadFor(kind) {
  if (kind === "matching")
    return {
      pairs: [
        { left: "Term 1", right: "Definition 1" },
        { left: "Term 2", right: "Definition 2" },
      ],
    };
  if (kind === "flashcards")
    return {
      cards: [{ front: "Front of card 1", back: "Back of card 1" }],
    };
  if (kind === "ordering")
    return { items: ["First step", "Second step"] };
  return {};
}

/**
 * Manages interactive activities for one section.
 * Rendered by the instructor course editor beneath the video/quiz row.
 */
export default function SectionActivitiesEditor({ sectionId, onError }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creatingKind, setCreatingKind] = useState("matching");
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setItems(await instructorService.listActivities(sectionId));
    } catch (e) {
      onError(errText(e, "Failed to load activities."));
    } finally {
      setLoading(false);
    }
  }, [sectionId, onError]);

  useEffect(() => {
    load();
  }, [load]);

  const handleCreate = async () => {
    setCreating(true);
    try {
      await instructorService.createActivity(sectionId, {
        kind: creatingKind,
        title: defaultTitle(creatingKind),
        payload: emptyPayloadFor(creatingKind),
      });
      await load();
    } catch (e) {
      onError(errText(e, "Failed to create activity."));
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this activity?")) return;
    try {
      await instructorService.deleteActivity(id);
      await load();
    } catch (e) {
      onError(errText(e, "Failed to delete activity."));
    }
  };

  return (
    <div className="space-y-3 border-t border-line bg-elevated/40 px-5 py-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-brand-700">
            Interactive activities
          </p>
          <p className="text-xs text-fg-subtle">
            Add drag-and-drop matches, flip flashcards, or ordering exercises
            for this section.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={creatingKind}
            onChange={(e) => setCreatingKind(e.target.value)}
            className="rounded-lg border border-line bg-surface px-2 py-1 text-xs text-fg focus:border-brand-500 focus:outline-none"
          >
            {KIND_OPTIONS.map((k) => (
              <option key={k.value} value={k.value}>
                {k.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={handleCreate}
            disabled={creating}
            className="rounded-full bg-brand-600 px-3 py-1.5 text-xs font-medium text-brand-fg shadow-sm hover:bg-brand-700 disabled:opacity-50"
          >
            {creating ? "Adding…" : "+ Add activity"}
          </button>
        </div>
      </div>

      {loading ? (
        <Spinner label="Loading activities…" />
      ) : items.length === 0 ? (
        <p className="rounded-xl border border-dashed border-line bg-surface p-4 text-xs text-fg-subtle">
          No activities yet. Pick a type above and click <b>+ Add activity</b>.
        </p>
      ) : (
        <div className="space-y-3">
          {items.map((a) => (
            <ActivityRow
              key={a.id}
              activity={a}
              onChanged={load}
              onError={onError}
              onDelete={() => handleDelete(a.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function ActivityRow({ activity, onChanged, onError, onDelete }) {
  const [expanded, setExpanded] = useState(false);
  const [title, setTitle] = useState(activity.title);
  const [instructions, setInstructions] = useState(activity.instructions || "");
  const [payload, setPayload] = useState(activity.payload);
  const [saving, setSaving] = useState(false);
  const dirty =
    title !== activity.title ||
    (instructions || "") !== (activity.instructions || "") ||
    JSON.stringify(payload) !== JSON.stringify(activity.payload);

  useEffect(() => {
    setTitle(activity.title);
    setInstructions(activity.instructions || "");
    setPayload(activity.payload);
  }, [activity]);

  const save = async () => {
    setSaving(true);
    try {
      await instructorService.updateActivity(activity.id, {
        title: title.trim(),
        instructions: instructions.trim(),
        payload,
      });
      await onChanged();
    } catch (e) {
      onError(errText(e, "Failed to save activity."));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="rounded-xl border border-line bg-surface">
      <header className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5">
        <div className="flex min-w-0 items-center gap-2">
          <KindChip kind={activity.kind} />
          <span className="truncate text-sm font-medium text-fg">
            {activity.title}
          </span>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="rounded-full border border-line px-3 py-1 text-xs font-medium text-fg-muted hover:text-fg hover:border-line-strong"
          >
            {expanded ? "Collapse" : "Edit"}
          </button>
          <button
            type="button"
            onClick={onDelete}
            className="rounded-full border border-danger/40 bg-danger-soft px-3 py-1 text-xs font-medium text-danger-soft-fg hover:border-danger/60"
          >
            Delete
          </button>
        </div>
      </header>

      {expanded && (
        <div className="space-y-3 border-t border-line px-4 py-4">
          <div className="grid gap-2 sm:grid-cols-2">
            <label className="block">
              <span className="block text-xs font-semibold uppercase tracking-wide text-fg-muted">
                Title
              </span>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="mt-1 w-full rounded-lg border border-line bg-elevated px-2 py-1.5 text-sm text-fg focus:border-brand-500 focus:outline-none"
              />
            </label>
            <label className="block">
              <span className="block text-xs font-semibold uppercase tracking-wide text-fg-muted">
                Instructions (optional)
              </span>
              <input
                type="text"
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                placeholder="Shown above the activity"
                className="mt-1 w-full rounded-lg border border-line bg-elevated px-2 py-1.5 text-sm text-fg focus:border-brand-500 focus:outline-none"
              />
            </label>
          </div>

          {activity.kind === "matching" && (
            <MatchingPayloadEditor payload={payload} onChange={setPayload} />
          )}
          {activity.kind === "flashcards" && (
            <FlashcardsPayloadEditor payload={payload} onChange={setPayload} />
          )}
          {activity.kind === "ordering" && (
            <OrderingPayloadEditor payload={payload} onChange={setPayload} />
          )}

          <div className="flex justify-end">
            <button
              type="button"
              onClick={save}
              disabled={!dirty || saving}
              className="rounded-full bg-brand-600 px-4 py-1.5 text-sm font-medium text-brand-fg shadow-sm hover:bg-brand-700 disabled:opacity-50"
            >
              {saving ? "Saving…" : dirty ? "Save changes" : "Saved"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function KindChip({ kind }) {
  const label =
    kind === "matching"
      ? "Matching"
      : kind === "flashcards"
      ? "Flashcards"
      : "Ordering";
  return (
    <span className="inline-flex items-center rounded-full bg-accent-soft px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-accent-soft-fg">
      {label}
    </span>
  );
}

/* ---- Per-kind payload editors ---- */

function MatchingPayloadEditor({ payload, onChange }) {
  const pairs = payload?.pairs || [];
  const set = (i, key, val) => {
    const next = pairs.map((p, idx) => (idx === i ? { ...p, [key]: val } : p));
    onChange({ pairs: next });
  };
  const add = () =>
    onChange({ pairs: [...pairs, { left: "", right: "" }] });
  const remove = (i) =>
    onChange({ pairs: pairs.filter((_, idx) => idx !== i) });

  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold uppercase tracking-wide text-fg-muted">
        Pairs (2–12)
      </p>
      {pairs.map((p, i) => (
        <div key={i} className="flex items-center gap-2">
          <input
            type="text"
            value={p.left}
            onChange={(e) => set(i, "left", e.target.value)}
            placeholder="Left item"
            className="flex-1 rounded-lg border border-line bg-elevated px-2 py-1.5 text-sm text-fg focus:border-brand-500 focus:outline-none"
          />
          <span className="text-fg-subtle">⇋</span>
          <input
            type="text"
            value={p.right}
            onChange={(e) => set(i, "right", e.target.value)}
            placeholder="Right match"
            className="flex-1 rounded-lg border border-line bg-elevated px-2 py-1.5 text-sm text-fg focus:border-brand-500 focus:outline-none"
          />
          <button
            type="button"
            onClick={() => remove(i)}
            disabled={pairs.length <= 2}
            className="rounded-md border border-line px-2 py-1 text-xs text-fg-muted hover:text-fg disabled:opacity-30"
          >
            ✕
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={add}
        disabled={pairs.length >= 12}
        className="rounded-full border border-line px-3 py-1 text-xs font-medium text-fg-muted hover:text-fg disabled:opacity-40"
      >
        + Add pair
      </button>
    </div>
  );
}

function FlashcardsPayloadEditor({ payload, onChange }) {
  const cards = payload?.cards || [];
  const set = (i, key, val) => {
    onChange({
      cards: cards.map((c, idx) => (idx === i ? { ...c, [key]: val } : c)),
    });
  };
  const add = () =>
    onChange({ cards: [...cards, { front: "", back: "" }] });
  const remove = (i) =>
    onChange({ cards: cards.filter((_, idx) => idx !== i) });

  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold uppercase tracking-wide text-fg-muted">
        Cards (1–30)
      </p>
      {cards.map((c, i) => (
        <div key={i} className="grid gap-2 rounded-lg border border-line bg-elevated p-2 sm:grid-cols-[1fr_1fr_auto]">
          <input
            type="text"
            value={c.front}
            onChange={(e) => set(i, "front", e.target.value)}
            placeholder="Front (prompt / term)"
            className="rounded-md border border-line bg-surface px-2 py-1.5 text-sm text-fg focus:border-brand-500 focus:outline-none"
          />
          <input
            type="text"
            value={c.back}
            onChange={(e) => set(i, "back", e.target.value)}
            placeholder="Back (answer / definition)"
            className="rounded-md border border-line bg-surface px-2 py-1.5 text-sm text-fg focus:border-brand-500 focus:outline-none"
          />
          <button
            type="button"
            onClick={() => remove(i)}
            disabled={cards.length <= 1}
            className="rounded-md border border-line px-2 py-1 text-xs text-fg-muted hover:text-fg disabled:opacity-30"
          >
            ✕
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={add}
        disabled={cards.length >= 30}
        className="rounded-full border border-line px-3 py-1 text-xs font-medium text-fg-muted hover:text-fg disabled:opacity-40"
      >
        + Add card
      </button>
    </div>
  );
}

function OrderingPayloadEditor({ payload, onChange }) {
  const items = payload?.items || [];
  const set = (i, val) =>
    onChange({ items: items.map((s, idx) => (idx === i ? val : s)) });
  const add = () => onChange({ items: [...items, ""] });
  const remove = (i) =>
    onChange({ items: items.filter((_, idx) => idx !== i) });
  const move = (i, delta) => {
    const to = i + delta;
    if (to < 0 || to >= items.length) return;
    const next = [...items];
    const [x] = next.splice(i, 1);
    next.splice(to, 0, x);
    onChange({ items: next });
  };

  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold uppercase tracking-wide text-fg-muted">
        Steps in the correct order (2–15). Learners will see them shuffled.
      </p>
      {items.map((s, i) => (
        <div key={i} className="flex items-center gap-2">
          <span className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-50 text-xs font-semibold text-brand-700">
            {i + 1}
          </span>
          <input
            type="text"
            value={s}
            onChange={(e) => set(i, e.target.value)}
            placeholder={`Step ${i + 1}`}
            className="flex-1 rounded-lg border border-line bg-elevated px-2 py-1.5 text-sm text-fg focus:border-brand-500 focus:outline-none"
          />
          <button
            type="button"
            onClick={() => move(i, -1)}
            disabled={i === 0}
            className="rounded-md border border-line px-2 py-1 text-xs text-fg-muted hover:text-fg disabled:opacity-30"
            aria-label="Move up"
          >
            ↑
          </button>
          <button
            type="button"
            onClick={() => move(i, 1)}
            disabled={i === items.length - 1}
            className="rounded-md border border-line px-2 py-1 text-xs text-fg-muted hover:text-fg disabled:opacity-30"
            aria-label="Move down"
          >
            ↓
          </button>
          <button
            type="button"
            onClick={() => remove(i)}
            disabled={items.length <= 2}
            className="rounded-md border border-line px-2 py-1 text-xs text-fg-muted hover:text-fg disabled:opacity-30"
          >
            ✕
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={add}
        disabled={items.length >= 15}
        className="rounded-full border border-line px-3 py-1 text-xs font-medium text-fg-muted hover:text-fg disabled:opacity-40"
      >
        + Add step
      </button>
    </div>
  );
}

function defaultTitle(kind) {
  if (kind === "matching") return "New matching activity";
  if (kind === "flashcards") return "New flashcard deck";
  if (kind === "ordering") return "New ordering activity";
  return "New activity";
}

function errText(e, fallback) {
  return (
    e?.response?.data?.error?.message ||
    e?.response?.data?.detail ||
    e?.message ||
    fallback
  );
}
