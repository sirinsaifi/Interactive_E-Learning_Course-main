import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, signInWithEmail, loading } = useAuth();
  const [email, setEmail] = useState("");
  const [error, setError] = useState(null);

  const from = location.state?.from?.pathname || "/";

  if (isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    const trimmed = email.trim();
    if (!trimmed) {
      setError("Please enter your email address.");
      return;
    }
    try {
      await signInWithEmail(trimmed);
      navigate(from, { replace: true });
    } catch (err) {
      const msg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.detail ||
        err?.message ||
        "Sign-in failed. Please try again.";
      setError(msg);
    }
  };

  return (
    <section className="mx-auto max-w-md py-12">
      <div className="overflow-hidden rounded-3xl border border-line bg-surface shadow-[var(--shadow-pop)]">
        <div className="px-8 pt-8">
          <div className="flex items-center gap-3">
            <img
              src="/excelra-mark.svg"
              alt="Excelra"
              className="h-11 w-11 rounded-2xl shadow-sm"
            />
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-fg">Welcome back</h1>
              <p className="text-sm text-fg-subtle">Enter your email to continue learning.</p>
            </div>
          </div>
        </div>

        <div className="mt-8 border-y border-line bg-[#f8fafc] px-8 py-8 dark:bg-[#1e2332]">
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <label className="flex flex-col gap-1.5">
              <span className="text-xs font-semibold uppercase tracking-wide text-fg-subtle">
                Email address
              </span>
              <input
                type="email"
                autoComplete="email"
                placeholder="you@excelra.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full rounded-xl border border-line bg-surface px-4 py-2.5 text-sm text-fg placeholder:text-fg-subtle focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
              />
            </label>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-full bg-brand-600 px-4 py-2.5 text-sm font-semibold text-brand-fg shadow-sm transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Signing in…" : "Continue"}
            </button>
          </form>
        </div>

        <div className="px-8 pb-8 pt-6">
          {error && (
            <div className="mb-4 w-full rounded-2xl border border-danger/30 bg-danger-soft p-3 text-sm text-danger-soft-fg">
              {error}
            </div>
          )}
          <p className="text-xs text-fg-subtle">
            No password needed. Your role is determined by your email address.
            Instructor access is granted to the configured instructor email.
          </p>
        </div>
      </div>
    </section>
  );
}
