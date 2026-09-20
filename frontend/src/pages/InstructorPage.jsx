import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import Spinner from "../components/Spinner.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { instructorService } from "../services/instructorService.js";

export default function InstructorPage() {
  const { isAdmin } = useAuth();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ title: "", description: "" });

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setCourses(await instructorService.listMyCourses());
    } catch (e) {
      setError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to load your courses."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.title.trim()) return;
    setCreating(true);
    setError(null);
    try {
      await instructorService.createCourse({
        title: form.title.trim(),
        description: form.description.trim() || null,
      });
      setForm({ title: "", description: "" });
      setShowForm(false);
      await refresh();
    } catch (e) {
      setError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to create course."
      );
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <div className="py-12">
        <Spinner label="Loading your courses…" />
      </div>
    );
  }

  return (
    <section className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-fg">
            {isAdmin ? "All courses" : "My courses"}
          </h1>
          <p className="mt-1 text-sm text-fg-subtle">
            {isAdmin
              ? "Admins can manage every course on the platform."
              : "Create new courses or update the ones assigned to you."}
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowForm((v) => !v)}
          className="rounded-full bg-brand-600 px-4 py-1.5 text-sm font-medium text-brand-fg shadow-sm transition hover:bg-brand-700"
        >
          {showForm ? "Cancel" : "+ New course"}
        </button>
      </header>

      {error && (
        <div className="rounded-2xl border border-danger/30 bg-danger-soft p-3 text-sm text-danger-soft-fg">
          {error}
        </div>
      )}

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="space-y-3 rounded-2xl border border-line bg-surface p-5 shadow-[var(--shadow-card)]"
        >
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-fg-muted">
              Title
            </label>
            <input
              type="text"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="mt-1 w-full rounded-lg border border-line bg-elevated px-3 py-2 text-sm text-fg focus:border-brand-500 focus:outline-none"
              placeholder="Intro to Astrophysics"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-fg-muted">
              Description
            </label>
            <textarea
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
              className="mt-1 w-full rounded-lg border border-line bg-elevated px-3 py-2 text-sm text-fg focus:border-brand-500 focus:outline-none"
              rows={3}
              placeholder="What learners will gain…"
            />
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={creating}
              className="rounded-full bg-brand-600 px-4 py-1.5 text-sm font-medium text-brand-fg shadow-sm transition hover:bg-brand-700 disabled:opacity-50"
            >
              {creating ? "Creating…" : "Create course"}
            </button>
          </div>
        </form>
      )}

      <div className="overflow-hidden rounded-2xl border border-line bg-surface shadow-[var(--shadow-card)]">
        <table className="min-w-full text-sm">
          <thead className="bg-muted/60 text-left text-xs uppercase tracking-wide text-fg-muted">
            <tr>
              <th className="px-5 py-2.5">Course</th>
              <th className="px-5 py-2.5">Instructor</th>
              <th className="px-5 py-2.5">Sections</th>
              <th className="px-5 py-2.5">Videos</th>
              <th className="px-5 py-2.5"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {courses.map((c) => (
              <tr key={c.id} className="hover:bg-muted/40">
                <td className="px-5 py-3">
                  <p className="font-medium text-fg">{c.title}</p>
                  <p className="text-xs text-fg-subtle">{c.slug}</p>
                </td>
                <td className="px-5 py-3 text-fg-muted">
                  {c.instructor_user?.name ||
                    c.instructor_user?.email ||
                    c.instructor ||
                    "—"}
                </td>
                <td className="px-5 py-3 text-fg-muted">{c.section_count}</td>
                <td className="px-5 py-3 text-fg-muted">{c.video_count}</td>
                <td className="px-5 py-3 text-right">
                  <Link
                    to={`/instructor/courses/${c.id}`}
                    className="rounded-full border border-line bg-surface px-3 py-1 text-xs font-medium text-fg-muted transition hover:text-fg hover:border-line-strong"
                  >
                    Manage
                  </Link>
                </td>
              </tr>
            ))}
            {courses.length === 0 && (
              <tr>
                <td
                  colSpan={5}
                  className="px-5 py-10 text-center text-fg-subtle"
                >
                  No courses yet. Click “+ New course” to start.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
