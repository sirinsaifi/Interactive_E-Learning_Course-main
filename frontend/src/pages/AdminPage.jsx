import { useCallback, useEffect, useMemo, useState } from "react";

import Spinner from "../components/Spinner.jsx";
import { adminService } from "../services/adminService.js";
import {
  adminInstructorService,
  instructorService,
} from "../services/instructorService.js";

const ROLES = ["learner", "instructor", "admin"];

export default function AdminPage() {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [syncing, setSyncing] = useState(false);
  const [lastSync, setLastSync] = useState(null);
  const [rowBusy, setRowBusy] = useState({});

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, u, c] = await Promise.all([
        adminService.getStats(),
        adminService.listUsers(),
        instructorService.listMyCourses(),
      ]);
      setStats(s);
      setUsers(u);
      setCourses(c);
    } catch (e) {
      setError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to load admin data."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleSync = async (prune) => {
    setSyncing(true);
    try {
      const res = await adminService.triggerSync({ prune });
      setLastSync(res);
      await refresh();
    } catch (e) {
      setError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Sync failed."
      );
    } finally {
      setSyncing(false);
    }
  };

  const handleRoleChange = async (userId, newRole) => {
    setRowBusy((b) => ({ ...b, [`u-${userId}`]: true }));
    setError(null);
    try {
      await adminInstructorService.setUserRole(userId, newRole);
      await refresh();
    } catch (e) {
      setError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to change role."
      );
    } finally {
      setRowBusy((b) => ({ ...b, [`u-${userId}`]: false }));
    }
  };

  const handleAssignInstructor = async (courseId, value) => {
    const instructorId = value === "" ? null : Number(value);
    setRowBusy((b) => ({ ...b, [`c-${courseId}`]: true }));
    setError(null);
    try {
      await adminInstructorService.assignInstructor(courseId, instructorId);
      await refresh();
    } catch (e) {
      setError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to assign instructor."
      );
    } finally {
      setRowBusy((b) => ({ ...b, [`c-${courseId}`]: false }));
    }
  };

  const instructorOptions = useMemo(
    () => users.filter((u) => u.role === "instructor" || u.role === "admin"),
    [users]
  );

  if (loading) {
    return (
      <div className="py-12">
        <Spinner label="Loading admin…" />
      </div>
    );
  }

  return (
    <section className="space-y-8">
      <header>
        <h1 className="text-3xl font-bold tracking-tight text-fg">Admin</h1>
        <p className="mt-1 text-sm text-fg-subtle">
          Catalog stats, content sync, role management, and instructor assignment.
        </p>
      </header>

      {error && (
        <div className="rounded-2xl border border-danger/30 bg-danger-soft p-3 text-sm text-danger-soft-fg">
          {error}
        </div>
      )}

      {stats && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
          <StatCard label="Users" value={stats.users} />
          <StatCard label="Courses" value={stats.courses} />
          <StatCard label="Sections" value={stats.sections} />
          <StatCard label="Videos" value={stats.videos} />
          <StatCard label="Progress rows" value={stats.progress_rows} />
        </div>
      )}

      <div className="rounded-2xl border border-line bg-surface p-5 shadow-[var(--shadow-card)]">
        <h2 className="text-sm font-semibold text-fg">Content sync</h2>
        <p className="mt-1 text-xs text-fg-subtle">
          Re-scans <code className="rounded bg-muted px-1 py-0.5 text-fg-muted">storage/videos/</code> and upserts the catalog. Stable IDs are preserved.
        </p>
        <p className="mt-2 rounded-lg border border-warning/30 bg-warning-soft p-2 text-[11px] text-warning-soft-fg">
          Heads up: <strong>Sync &amp; prune</strong> will delete any course that isn’t present on disk — including courses created in the instructor UI. Avoid prune on environments where instructors author content.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => handleSync(false)}
            disabled={syncing}
            className="rounded-full bg-brand-600 px-4 py-1.5 text-sm font-medium text-brand-fg shadow-sm transition hover:bg-brand-700 disabled:opacity-50"
          >
            {syncing ? "Syncing…" : "Sync now"}
          </button>
          <button
            type="button"
            onClick={() => handleSync(true)}
            disabled={syncing}
            className="rounded-full border border-line bg-surface px-4 py-1.5 text-sm font-medium text-fg-muted transition hover:text-fg hover:border-line-strong disabled:opacity-50"
          >
            Sync &amp; prune missing
          </button>
        </div>
        {lastSync && (
          <pre className="mt-3 overflow-x-auto rounded-xl bg-elevated p-3 text-[11px] text-fg-muted ring-1 ring-line">
            {JSON.stringify(lastSync, null, 2)}
          </pre>
        )}
      </div>

      <div className="overflow-hidden rounded-2xl border border-line bg-surface shadow-[var(--shadow-card)]">
        <header className="border-b border-line px-5 py-4">
          <h2 className="text-sm font-semibold text-fg">
            Courses <span className="text-fg-subtle">({courses.length})</span>
          </h2>
          <p className="mt-1 text-xs text-fg-subtle">
            Assign a managing instructor. Selecting “— Unassigned —” clears it.
          </p>
        </header>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-muted/60 text-left text-xs uppercase tracking-wide text-fg-muted">
              <tr>
                <th className="px-5 py-2.5">Course</th>
                <th className="px-5 py-2.5">Sections / Videos</th>
                <th className="px-5 py-2.5">Managed by</th>
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
                    {c.section_count} / {c.video_count}
                  </td>
                  <td className="px-5 py-3">
                    <select
                      value={c.instructor_user?.id ?? ""}
                      disabled={rowBusy[`c-${c.id}`]}
                      onChange={(e) => handleAssignInstructor(c.id, e.target.value)}
                      className="rounded-lg border border-line bg-elevated px-2 py-1 text-xs text-fg focus:border-brand-500 focus:outline-none disabled:opacity-50"
                    >
                      <option value="">— Unassigned —</option>
                      {instructorOptions.map((u) => (
                        <option key={u.id} value={u.id}>
                          {(u.name || u.email)}
                          {u.role === "admin" ? " (admin)" : ""}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
              {courses.length === 0 && (
                <tr>
                  <td colSpan={3} className="px-5 py-10 text-center text-fg-subtle">
                    No courses yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-line bg-surface shadow-[var(--shadow-card)]">
        <header className="border-b border-line px-5 py-4">
          <h2 className="text-sm font-semibold text-fg">
            Users <span className="text-fg-subtle">({users.length})</span>
          </h2>
        </header>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-muted/60 text-left text-xs uppercase tracking-wide text-fg-muted">
              <tr>
                <th className="px-5 py-2.5">ID</th>
                <th className="px-5 py-2.5">User</th>
                <th className="px-5 py-2.5">Email</th>
                <th className="px-5 py-2.5">Role</th>
                <th className="px-5 py-2.5">Change role</th>
                <th className="px-5 py-2.5">Joined</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-muted/40">
                  <td className="px-5 py-3 text-fg-subtle">{u.id}</td>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      {u.picture_url ? (
                        <img
                          src={u.picture_url}
                          alt=""
                          referrerPolicy="no-referrer"
                          className="h-6 w-6 rounded-full"
                        />
                      ) : (
                        <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-muted text-[11px] font-semibold text-fg-muted">
                          {(u.name || u.email || "?")[0].toUpperCase()}
                        </span>
                      )}
                      <span className="text-fg">{u.name || "—"}</span>
                    </div>
                  </td>
                  <td className="px-5 py-3 text-fg-muted">{u.email}</td>
                  <td className="px-5 py-3">
                    <RoleBadge role={u.role} />
                  </td>
                  <td className="px-5 py-3">
                    <select
                      value={u.role}
                      disabled={rowBusy[`u-${u.id}`]}
                      onChange={(e) => handleRoleChange(u.id, e.target.value)}
                      className="rounded-lg border border-line bg-elevated px-2 py-1 text-xs text-fg focus:border-brand-500 focus:outline-none disabled:opacity-50"
                    >
                      {ROLES.map((r) => (
                        <option key={r} value={r}>
                          {r}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-5 py-3 text-xs text-fg-subtle">
                    {new Date(u.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-5 py-10 text-center text-fg-subtle">
                    No users yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="rounded-2xl border border-line bg-surface p-4 shadow-[var(--shadow-card)]">
      <p className="text-xs uppercase tracking-wide text-fg-subtle">{label}</p>
      <p className="mt-1.5 text-2xl font-bold text-fg">{value}</p>
    </div>
  );
}

function RoleBadge({ role }) {
  const style =
    role === "admin"
      ? "bg-accent-soft text-accent-soft-fg"
      : role === "instructor"
        ? "bg-warning-soft text-warning-soft-fg"
        : "bg-muted text-fg-muted";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${style}`}
    >
      {role}
    </span>
  );
}
