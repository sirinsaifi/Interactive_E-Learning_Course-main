import { useEffect, useMemo, useRef, useState } from "react";

/**
 * Drag-and-drop matching activity.
 *
 * payload shape: { pairs: [{ left, right }, ...] }
 *
 * The left column stays in place. Right-side chips are shuffled and the
 * learner drops each chip onto its matching left slot. We check correctness
 * against the original pair mapping.
 */
export default function MatchingActivity({ activity, onCompleted }) {
  const pairs = activity?.payload?.pairs || [];

  const rightItems = useMemo(
    () =>
      shuffle(pairs.map((p, i) => ({ id: `r-${i}`, text: p.right, correctIdx: i }))),
    // Reshuffle whenever the activity changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [activity?.id]
  );

  // Map: leftIndex -> rightItem (or null when empty)
  const [drops, setDrops] = useState(() => Array(pairs.length).fill(null));
  const [pool, setPool] = useState(rightItems);
  const [dragId, setDragId] = useState(null);
  const [checked, setChecked] = useState(false);
  const notifiedRef = useRef(false);

  useEffect(() => {
    setDrops(Array(pairs.length).fill(null));
    setPool(rightItems);
    setChecked(false);
    notifiedRef.current = false;
  }, [activity?.id, pairs.length, rightItems]);

  const onDragStart = (e, id) => {
    setDragId(id);
    e.dataTransfer.effectAllowed = "move";
  };

  const findChip = (id) => rightItems.find((r) => r.id === id) || null;

  const handleDrop = (leftIdx) => {
    if (!dragId) return;
    const chip = findChip(dragId);
    if (!chip) return;
    setChecked(false);
    setDrops((prev) => {
      const next = [...prev];
      // If a chip was already here, return it to the pool.
      const displaced = next[leftIdx];
      next[leftIdx] = chip;
      setPool((prevPool) => {
        let poolNext = prevPool.filter((c) => c.id !== chip.id);
        // Also remove chip from any other left slot it might occupy.
        for (let i = 0; i < next.length; i += 1) {
          if (i !== leftIdx && next[i]?.id === chip.id) next[i] = null;
        }
        if (displaced) poolNext = [...poolNext, displaced];
        return poolNext;
      });
      return next;
    });
    setDragId(null);
  };

  const handleReturnToPool = () => {
    if (!dragId) return;
    const chip = findChip(dragId);
    if (!chip) return;
    setChecked(false);
    setDrops((prev) => prev.map((c) => (c?.id === chip.id ? null : c)));
    setPool((prev) => (prev.some((c) => c.id === chip.id) ? prev : [...prev, chip]));
    setDragId(null);
  };

  const reset = () => {
    setDrops(Array(pairs.length).fill(null));
    setPool(rightItems);
    setChecked(false);
  };

  const results = drops.map((chip, i) => (chip ? chip.correctIdx === i : null));
  const correctCount = results.filter((r) => r === true).length;
  const allFilled = drops.every((c) => c !== null);

  return (
    <div className="space-y-4 animate-fade-in">
      {activity.instructions && (
        <p className="text-sm text-fg-muted">{activity.instructions}</p>
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-2 stagger-children">
          <p className="text-xs font-semibold uppercase tracking-wide text-fg-muted">
            Match each item…
          </p>
          {pairs.map((p, i) => {
            const status = checked ? results[i] : null;
            return (
              <div
                key={`left-${i}`}
                onDragOver={(e) => e.preventDefault()}
                onDrop={() => handleDrop(i)}
                className={`flex items-center gap-3 rounded-xl border border-line bg-elevated p-3 transition-colors duration-300 ${
                  status === false ? "animate-shake" : ""
                } ${status === true ? "animate-pop" : ""}`}
              >
                <span className="flex-1 text-sm text-fg">{p.left}</span>
                <span
                  className={`inline-flex min-h-[2.25rem] min-w-[9rem] items-center justify-center rounded-lg border-2 border-dashed px-3 py-1 text-sm ${
                    drops[i]
                      ? status === true
                        ? "border-success bg-success-soft text-success-soft-fg"
                        : status === false
                        ? "border-danger bg-danger-soft text-danger-soft-fg"
                        : "border-brand-500 bg-brand-50 text-brand-700"
                      : "border-line text-fg-subtle"
                  }`}
                >
                  {drops[i] ? (
                    <span
                      draggable
                      onDragStart={(e) => onDragStart(e, drops[i].id)}
                      className="cursor-move"
                    >
                      {drops[i].text}
                    </span>
                  ) : (
                    "Drop here"
                  )}
                </span>
              </div>
            );
          })}
        </div>

        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-fg-muted">
            …with the right label
          </p>
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleReturnToPool}
            className="min-h-[8rem] rounded-xl border-2 border-dashed border-line bg-muted/30 p-3"
          >
            {pool.length === 0 ? (
              <p className="text-xs text-fg-subtle">All chips placed.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {pool.map((chip) => (
                  <span
                    key={chip.id}
                    draggable
                    onDragStart={(e) => onDragStart(e, chip.id)}
                    className="hover-lift cursor-move rounded-full border border-line bg-surface px-3 py-1.5 text-sm text-fg shadow-sm hover:border-brand-500"
                  >
                    {chip.text}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm text-fg-muted">
          {checked ? (
            <span>
              <span className="font-semibold text-fg">{correctCount}</span> /{" "}
              {pairs.length} correct
            </span>
          ) : (
            <span className="text-xs text-fg-subtle">
              Drag the chips on the right onto their matching row.
            </span>
          )}
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={reset}
            className="hover-lift rounded-full border border-line bg-surface px-3 py-1.5 text-xs font-medium text-fg-muted hover:text-fg hover:border-line-strong"
          >
            Reset
          </button>
          <button
            type="button"
            onClick={() => {
              setChecked(true);
              const allCorrect =
                drops.length > 0 &&
                drops.every((c, i) => c && c.correctIdx === i);
              if (allCorrect && !notifiedRef.current) {
                notifiedRef.current = true;
                if (onCompleted) onCompleted();
              }
            }}
            disabled={!allFilled}
            className="hover-lift rounded-full bg-brand-600 px-4 py-1.5 text-sm font-medium text-brand-fg shadow-sm transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Check answers
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
