import { useCallback, useEffect, useState } from "react";

import { quizService } from "../services/quizService.js";
import Spinner from "./Spinner.jsx";

/**
 * Renders a section quiz for a learner: 4 multiple-choice questions, a
 * submit action, and a graded result view with per-question feedback.
 */
export default function QuizPanel({ quizId, sectionTitle, onSubmitted }) {
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({}); // { [questionId]: 0..3 }
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    setAnswers({});
    try {
      const data = await quizService.getById(quizId);
      setQuiz(data);
      // If the learner already has a previous attempt, surface it.
      try {
        const last = await quizService.getMyAttempt(quizId);
        if (last) setResult(last);
      } catch {
        /* no prior attempt - that's fine */
      }
    } catch (e) {
      setError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to load quiz."
      );
    } finally {
      setLoading(false);
    }
  }, [quizId]);

  useEffect(() => {
    if (quizId) load();
  }, [quizId, load]);

  const handleSelect = (questionId, optionIndex) => {
    setAnswers((prev) => ({ ...prev, [questionId]: optionIndex }));
  };

  const handleSubmit = async () => {
    if (!quiz) return;
    const ordered = [...quiz.questions].sort((a, b) => a.position - b.position);
    const payload = ordered.map((q) => answers[q.id] ?? -1);
    if (payload.some((v) => v < 0)) {
      setError("Please answer every question before submitting.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const res = await quizService.submit(quiz.id, payload);
      setResult(res);
      if (typeof onSubmitted === "function") onSubmitted(res);
    } catch (e) {
      setError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to submit quiz."
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleRetry = () => {
    setResult(null);
    setAnswers({});
    setError(null);
  };

  if (loading) {
    return (
      <div className="rounded-2xl border border-line bg-surface p-8 shadow-[var(--shadow-card)]">
        <Spinner label="Loading quiz…" />
      </div>
    );
  }

  if (error && !quiz) {
    return (
      <div className="rounded-2xl border border-danger/30 bg-danger-soft p-4 text-sm text-danger-soft-fg">
        {error}
      </div>
    );
  }

  if (!quiz) return null;

  const ordered = [...quiz.questions].sort((a, b) => a.position - b.position);

  return (
    <article className="rounded-2xl border border-line bg-surface p-6 shadow-[var(--shadow-card)]">
      <header className="mb-5">
        <p className="text-xs font-semibold uppercase tracking-wider text-brand-700">
          Section quiz
        </p>
        <h2 className="mt-1 text-xl font-bold text-fg">{quiz.title}</h2>
        {sectionTitle && (
          <p className="text-sm text-fg-subtle">{sectionTitle}</p>
        )}
        <p className="mt-2 text-xs text-fg-subtle">
          {ordered.length} questions · {quiz.pass_threshold}% to pass
        </p>
      </header>

      {error && (
        <div className="mb-4 rounded-xl border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger-soft-fg">
          {error}
        </div>
      )}

      {result ? (
        <ResultView result={result} onRetry={handleRetry} />
      ) : (
        <>
          <ol className="space-y-5">
            {ordered.map((q, idx) => (
              <QuestionCard
                key={q.id}
                question={q}
                index={idx}
                selected={answers[q.id]}
                onSelect={(i) => handleSelect(q.id, i)}
              />
            ))}
          </ol>
          <div className="mt-6 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={handleSubmit}
              disabled={submitting}
              className="rounded-full bg-brand-600 px-5 py-2 text-sm font-medium text-brand-fg shadow-sm transition hover:bg-brand-700 disabled:opacity-50"
            >
              {submitting ? "Submitting…" : "Submit quiz"}
            </button>
          </div>
        </>
      )}
    </article>
  );
}

function QuestionCard({ question, index, selected, onSelect }) {
  return (
    <li className="rounded-xl border border-line bg-elevated p-4">
      <p className="text-sm font-semibold text-fg">
        <span className="mr-2 text-fg-subtle">Q{index + 1}.</span>
        {question.text}
      </p>
      <div className="mt-3 space-y-2">
        {question.options.map((opt, i) => {
          const isSelected = selected === i;
          return (
            <label
              key={i}
              className={`flex cursor-pointer items-start gap-3 rounded-lg border px-3 py-2 text-sm transition ${
                isSelected
                  ? "border-brand-500 bg-brand-50 text-fg"
                  : "border-line bg-surface text-fg-muted hover:border-line-strong hover:text-fg"
              }`}
            >
              <input
                type="radio"
                name={`q-${question.id}`}
                value={i}
                checked={isSelected}
                onChange={() => onSelect(i)}
                className="mt-0.5 accent-brand-600"
              />
              <span className="flex-1">{opt}</span>
            </label>
          );
        })}
      </div>
    </li>
  );
}

function ResultView({ result, onRetry }) {
  const pct = result.percent ?? 0;
  return (
    <div className="space-y-5">
      <div
        className={`rounded-2xl border p-5 ${
          result.passed
            ? "border-success/40 bg-success-soft text-success-soft-fg"
            : "border-warning/40 bg-warning-soft text-warning-soft-fg"
        }`}
      >
        <p className="text-xs font-semibold uppercase tracking-wider">
          {result.passed ? "Passed" : "Try again"}
        </p>
        <p className="mt-1 text-2xl font-bold">
          {result.score} / {result.total}
          <span className="ml-2 text-base font-normal opacity-80">({pct}%)</span>
        </p>
      </div>

      <ol className="space-y-3">
        {result.questions.map((q, idx) => (
          <li
            key={q.question_id}
            className="rounded-xl border border-line bg-elevated p-4"
          >
            <p className="text-sm font-semibold text-fg">
              <span className="mr-2 text-fg-subtle">Q{idx + 1}.</span>
              {q.text}
            </p>
            <ul className="mt-3 space-y-1.5 text-sm">
              {q.options.map((opt, i) => {
                const isCorrect = i === q.correct_index;
                const isPicked = i === q.selected_index;
                let cls = "border-line bg-surface text-fg-muted";
                if (isCorrect) cls = "border-success/50 bg-success-soft text-success-soft-fg";
                else if (isPicked) cls = "border-danger/50 bg-danger-soft text-danger-soft-fg";
                return (
                  <li
                    key={i}
                    className={`rounded-lg border px-3 py-2 ${cls}`}
                  >
                    <span className="font-medium">{opt}</span>
                    {isCorrect && (
                      <span className="ml-2 text-xs opacity-80">(correct)</span>
                    )}
                    {isPicked && !isCorrect && (
                      <span className="ml-2 text-xs opacity-80">(your answer)</span>
                    )}
                  </li>
                );
              })}
            </ul>
          </li>
        ))}
      </ol>

      <div className="flex justify-end">
        <button
          type="button"
          onClick={onRetry}
          className="rounded-full border border-line bg-surface px-5 py-2 text-sm font-medium text-fg-muted transition hover:text-fg hover:border-line-strong"
        >
          Retake quiz
        </button>
      </div>
    </div>
  );
}
