import { useEffect, useMemo, useRef, useState } from "react";

/**
 * Sequence / Ordering activity.
 *
 * payload shape: { items: [string, ...] }
 * The stored items are the correct order; we shuffle for display and the
 * learner drags to reorder.
 */
export default function OrderingActivity({ activity, onCompleted }) {
  const correctOrder = activity?.payload?.items || [];

  const initial = useMemo(() => {
    const withIds = correctOrder.map((text, i) => ({
      id: `item-${i}`,
      text,
      correctIdx: i,
    }));
    return shuffle(withIds);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activity?.id]);

  const [items, setItems] = useState(initial);
  const [checked, setChecked] = useState(false);
  const dragIdRef = useRef(null);
  const notifiedRef = useRef(false);

  useEffect(() => {
    setItems(initial);
    setChecked(false);
    notifiedRef.current = false;
  }, [initial]);

  const onDragStart = (id) => {
    dragIdRef.current = id;
  };

  const onDragOver = (e) => {
    e.preventDefault();
  };

  const onDrop = (targetId) => {
    const sourceId = dragIdRef.current;
    dragIdRef.current = null;
    if (!sourceId || sourceId === targetId) return;
    setChecked(false);
    setItems((prev) => {
      const next = [...prev];
      const from = next.findIndex((x) => x.id === sourceId);
      const to = next.findIndex((x) => x.id === targetId);
      if (from === -1 || to === -1) return prev;
      const [moved] = next.splice(from, 1);
      next.splice(to, 0, moved);
      return next;
    });
  };

  const move = (idx, delta) => {
    setChecked(false);
    setItems((prev) => {
      const to = idx + delta;
      if (to < 0 || to >= prev.length) return prev;
      const next = [...prev];
      const [moved] = next.splice(idx, 1);
      next.splice(to, 0, moved);
      return next;
    });
  };

  const reset = () => {
    setItems(shuffle(correctOrder.map((text, i) => ({ id: `item-${i}`, text, correctIdx: i }))));
    setChecked(false);
  };

  const results = items.map((it, i) => it.correctIdx === i);
  const correctCount = results.filter(Boolean).length;
  const allCorrect = correctCount === items.length;

  return (
    <div className="space-y-4 animate-fade-in">
      {activity.instructions && (
        <p className="text-sm text-fg-muted">{activity.instructions}</p>
      )}

      <ol className="space-y-2 stagger-children">
        {items.map((it, idx) => {
          const status = checked ? results[idx] : null;
          return (
            <li
              key={it.id}
              draggable
              onDragStart={() => onDragStart(it.id)}
              onDragOver={onDragOver}
              onDrop={() => onDrop(it.id)}
              className={`flex items-center gap-3 rounded-xl border p-3 shadow-sm transition-all duration-300 ${
                status === true
                  ? "border-success bg-success-soft animate-pop"
                  : status === false
                  ? "border-danger bg-danger-soft animate-shake"
                  : "border-line bg-surface hover:-translate-y-0.5 hover:border-brand-500 hover:shadow-[var(--shadow-pop)]"
              }`}
              style={{ cursor: "move" }}
            >
              <span
                className={`inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                  status === true
                    ? "bg-success text-white"
                    : status === false
                    ? "bg-danger text-white"
                    : "bg-muted text-fg-muted"
                }`}
              >
                {idx + 1}
              </span>
              <span className="flex-1 text-sm text-fg">{it.text}</span>
              <span className="flex shrink-0 gap-1">
                <button
                  type="button"
                  onClick={() => move(idx, -1)}
                  disabled={idx === 0}
                  aria-label="Move up"
                  className="rounded-md border border-line px-2 py-0.5 text-xs text-fg-muted disabled:opacity-30 hover:text-fg"
                >
                  ↑
                </button>
                <button
                  type="button"
                  onClick={() => move(idx, 1)}
                  disabled={idx === items.length - 1}
                  aria-label="Move down"
                  className="rounded-md border border-line px-2 py-0.5 text-xs text-fg-muted disabled:opacity-30 hover:text-fg"
                >
                  ↓
                </button>
              </span>
            </li>
          );
        })}
      </ol>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm text-fg-muted">
          {checked ? (
            allCorrect ? (
              <span className="font-semibold text-success">
                ✓ Perfect order!
              </span>
            ) : (
              <span>
                <span className="font-semibold text-fg">{correctCount}</span> /{" "}
                {items.length} in the right place
              </span>
            )
          ) : (
            <span className="text-xs text-fg-subtle">
              Drag rows or use ↑ / ↓ to reorder.
            </span>
          )}
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={reset}
            className="hover-lift rounded-full border border-line bg-surface px-3 py-1.5 text-xs font-medium text-fg-muted hover:text-fg hover:border-line-strong"
          >
            Shuffle again
          </button>
          <button
            type="button"
            onClick={() => {
              setChecked(true);
              const allCorrect =
                items.length > 0 &&
                items.every((it, i) => it.correctIdx === i);
              if (allCorrect && !notifiedRef.current) {
                notifiedRef.current = true;
                if (onCompleted) onCompleted();
              }
            }}
            className="hover-lift rounded-full bg-brand-600 px-4 py-1.5 text-sm font-medium text-brand-fg shadow-sm transition hover:bg-brand-700"
          >
            Check order
          </button>
        </div>
      </div>
    </div>
  );
}

function shuffle(arr) {
  const out = [...arr];
  for (let i = out.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}
