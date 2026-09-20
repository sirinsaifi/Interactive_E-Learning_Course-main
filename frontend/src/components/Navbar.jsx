import { NavLink, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import ThemeToggle from "./ThemeToggle.jsx";

const linkBase =
  "px-3 py-1.5 rounded-full text-sm font-medium transition-colors";
const linkInactive = "text-fg-muted hover:text-fg hover:bg-muted";
const linkActive = "bg-brand-50 text-brand-700";

export default function Navbar() {
  const { isAuthenticated, isAdmin, canManageCourses, user, logout } = useAuth();
  const navigate = useNavigate();

  const handleSignOut = () => {
    logout();
    navigate("/", { replace: true });
  };

  return (
    <header className="sticky top-0 z-30 border-b border-line bg-surface/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <NavLink to="/" className="flex shrink-0 items-center gap-2.5">
          <img
            src="/excelra-mark.svg"
            alt="Excelra"
            className="h-8 w-8 rounded-lg shadow-sm"
          />
          <span className="flex flex-col leading-tight">
            <span className="text-base font-semibold tracking-tight text-fg">LearnSphere</span>
            <span className="text-[10px] font-medium uppercase tracking-wider text-fg-subtle">by Excelra</span>
          </span>
        </NavLink>

        <nav className="hidden flex-1 items-center gap-1 sm:flex">
          <NavLink
            to="/"
            end
            className={({ isActive }) => `${linkBase} ${isActive ? linkActive : linkInactive}`}
          >
            Home
          </NavLink>
          <NavLink
            to="/courses"
            className={({ isActive }) => `${linkBase} ${isActive ? linkActive : linkInactive}`}
          >
            Courses
          </NavLink>
          {canManageCourses && (
            <NavLink
              to="/instructor"
              className={({ isActive }) => `${linkBase} ${isActive ? linkActive : linkInactive}`}
            >
              Instructor
            </NavLink>
          )}
          {isAdmin && (
            <>
              <NavLink
                to="/admin"
                className={({ isActive }) => `${linkBase} ${isActive ? linkActive : linkInactive}`}
              >
                Admin
              </NavLink>
              <NavLink
                to="/health"
                className={({ isActive }) => `${linkBase} ${isActive ? linkActive : linkInactive}`}
              >
                Health
              </NavLink>
            </>
          )}
        </nav>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          {isAuthenticated ? (
            <div className="flex items-center gap-2">
              <div className="hidden items-center gap-2 rounded-full border border-line bg-surface px-2 py-1 sm:flex">
                {user?.picture_url ? (
                  <img
                    src={user.picture_url}
                    alt=""
                    referrerPolicy="no-referrer"
                    className="h-6 w-6 rounded-full"
                  />
                ) : (
                  <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-brand-600 text-[11px] font-semibold text-brand-fg">
                    {(user?.name || user?.email || "?")[0].toUpperCase()}
                  </span>
                )}
                <span className="max-w-[140px] truncate text-sm text-fg-muted">
                  {user?.name || user?.email}
                </span>
                {isAdmin && (
                  <span className="rounded-full bg-accent-soft px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-accent-soft-fg">
                    admin
                  </span>
                )}
                {!isAdmin && canManageCourses && (
                  <span className="rounded-full bg-warning-soft px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-warning-soft-fg">
                    instructor
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={handleSignOut}
                className="rounded-full border border-line bg-surface px-3 py-1.5 text-sm font-medium text-fg-muted transition hover:text-fg hover:border-line-strong"
              >
                Sign out
              </button>
            </div>
          ) : (
            <NavLink
              to="/login"
              className="rounded-full bg-brand-600 px-4 py-1.5 text-sm font-medium text-brand-fg shadow-sm transition hover:bg-brand-700"
            >
              Sign in
            </NavLink>
          )}
        </div>
      </div>
    </header>
  );
}
