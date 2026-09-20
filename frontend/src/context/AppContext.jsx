import { createContext, useContext, useMemo, useState } from "react";

const AppContext = createContext(null);

/**
 * Application-wide context.
 *
 * Phase 1 is intentionally minimal — no auth state. Auth slices (currentUser,
 * token, login/logout) will be added here in Phase 2 without changing the
 * component API.
 */
export function AppProvider({ children }) {
  const [theme, setTheme] = useState("light");

  const value = useMemo(
    () => ({
      theme,
      setTheme,
    }),
    [theme]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppContext() {
  const ctx = useContext(AppContext);
  if (!ctx) {
    throw new Error("useAppContext must be used inside <AppProvider>");
  }
  return ctx;
}
