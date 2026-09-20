import { useEffect, useRef, useState } from "react";

/**
 * Flip flashcards.
 *
 * payload shape: { cards: [{ front, back }, ...] }
 *
 * Learner clicks a card to flip front <-> back. Prev/Next moves through the
 * deck and always resets to the front face so the next card lands unflipped.
 * The deck is considered "completed" once every card has been flipped to its
 * back at least once.
 */
export default function FlashcardsActivity({ activity, onCompleted }) {
  const cards = activity?.payload?.cards || [];
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [known, setKnown] = useState(() => new Set());
  const [seenBacks, setSeenBacks] = useState(() => new Set());
  const notifiedRef = useRef(false);

  useEffect(() => {
    setIndex(0);
    setFlipped(false);
    setKnown(new Set());
    setSeenBacks(new Set());
    notifiedRef.current = false;
  }, [activity?.id]);

  useEffect(() => {
    if (
      cards.length > 0 &&
      seenBacks.size === cards.length &&
      !notifiedRef.current
    ) {
      notifiedRef.current = true;
      if (onCompleted) onCompleted();
    }
  }, [seenBacks, cards.length, onCompleted]);

  if (cards.length === 0) {
    return (
      <p className="rounded-2xl border border-dashed border-line p-6 text-sm text-fg-subtle">
        No cards in this deck yet.
      </p>
    );
  }

  const card = cards[index];
  const goto = (delta) => {
    setFlipped(false);
    setIndex((i) => (i + delta + cards.length) % cards.length);
  };

  const toggleFlip = () => {
    setFlipped((v) => {
      const next = !v;
      if (next) {
        setSeenBacks((prev) => {
          if (prev.has(index)) return prev;
          const s = new Set(prev);
          s.add(index);
          return s;
        });
      }
      return next;
    });
  };

  const toggleKnown = () => {
    setKnown((prev) => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  };

  return (
    <div className="space-y-4 animate-fade-in">
      {activity.instructions && (
        <p className="text-sm text-fg-muted">{activity.instructions}</p>
      )}

      <div className="flex items-center justify-between text-xs text-fg-subtle">
        <span>
          Card <span className="font-semibold text-fg">{index + 1}</span> of{" "}
          {cards.length}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-success" />
          {known.size} marked known
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-1 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-brand-gradient transition-[width] duration-500 ease-out"
          style={{ width: `${((index + 1) / cards.length) * 100}%` }}
        />
      </div>

      <div
        key={index}
        className="mx-auto w-full max-w-xl animate-pop"
        style={{ perspective: "1400px" }}
      >
        <button
          type="button"
          onClick={toggleFlip}
          aria-label={flipped ? "Show front of card" : "Show back of card"}
          className="group relative block w-full text-left focus:outline-none"
          style={{ minHeight: "18rem" }}
        >
          <div
            className="relative h-72 w-full transition-transform duration-700"
            style={{
              transformStyle: "preserve-3d",
              transform: flipped ? "rotateY(180deg)" : "rotateY(0deg)",
              transitionTimingFunction: "cubic-bezier(0.22, 1, 0.36, 1)",
            }}
          >
            {/* Front face */}
            <div
              className="absolute inset-0 overflow-hidden rounded-3xl shadow-[var(--shadow-pop)] transition-transform duration-300 group-hover:scale-[1.015]"
              style={{ backfaceVisibility: "hidden" }}
            >
              <div className="bg-brand-gradient absolute inset-0" />
              <div
                className="absolute inset-0 opacity-30"
                style={{
                  backgroundImage:
                    "radial-gradient(circle at 20% 15%, rgba(255,255,255,0.35), transparent 40%), radial-gradient(circle at 85% 90%, rgba(255,255,255,0.25), transparent 45%)",
                }}
              />
              {/* Corner badge */}
              <span className="absolute right-4 top-4 rounded-full bg-white/25 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-white backdrop-blur">
                {index + 1} / {cards.length}
              </span>
              <div className="relative flex h-full flex-col items-center justify-center p-8 text-center text-white">
                <div className="animate-float text-3xl">💡</div>
                <p className="mt-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-white/80">
                  Question
                </p>
                <p className="mt-4 text-2xl font-semibold leading-snug drop-shadow-sm">
                  {card.front}
                </p>
                <p className="mt-6 inline-flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wider text-white/80">
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-white animate-pulse" />
                  Click to flip
                </p>
              </div>
            </div>

            {/* Back face */}
            <div
              className="absolute inset-0 overflow-hidden rounded-3xl border border-brand-500/40 bg-surface shadow-[var(--shadow-pop)]"
              style={{
                backfaceVisibility: "hidden",
                transform: "rotateY(180deg)",
              }}
            >
              <div
                className="absolute inset-x-0 top-0 h-1"
                style={{
                  background:
                    "linear-gradient(90deg, var(--brand-500), #8b5cf6, #ec4899)",
                }}
              />
              <div
                className="absolute inset-0 opacity-50"
                style={{
                  backgroundImage:
                    "radial-gradient(circle at 15% 100%, var(--brand-100), transparent 55%)",
                }}
              />
              <span className="absolute right-4 top-4 rounded-full bg-brand-50 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-brand-700">
                Answer
              </span>
              <div className="relative flex h-full flex-col items-center justify-center p-8 text-center">
                <div className="text-3xl">📖</div>
                <p className="mt-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-brand-700">
                  {card.front}
                </p>
                <p className="mt-4 text-xl font-medium leading-snug text-fg">
                  {card.back}
                </p>
                <p className="mt-6 text-[11px] font-medium uppercase tracking-wider text-fg-subtle">
                  Click to flip back
                </p>
              </div>
            </div>
          </div>
        </button>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => goto(-1)}
            className="hover-lift rounded-full border border-line bg-surface px-3 py-1.5 text-sm font-medium text-fg-muted hover:text-fg hover:border-line-strong"
          >
            ← Previous
          </button>
          <button
            type="button"
            onClick={() => goto(1)}
            className="hover-lift rounded-full border border-line bg-surface px-3 py-1.5 text-sm font-medium text-fg-muted hover:text-fg hover:border-line-strong"
          >
            Next →
          </button>
        </div>
        <button
          type="button"
          onClick={toggleKnown}
          className={`hover-lift rounded-full px-4 py-1.5 text-sm font-medium shadow-sm transition ${
            known.has(index)
              ? "bg-success text-white hover:brightness-95 animate-pop"
              : "bg-brand-600 text-brand-fg hover:bg-brand-700"
          }`}
        >
          {known.has(index) ? "✓ I know this" : "Mark as known"}
        </button>
      </div>
    </div>
  );
}
