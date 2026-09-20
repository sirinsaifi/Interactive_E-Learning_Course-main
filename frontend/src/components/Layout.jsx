import Navbar from "./Navbar.jsx";

const currentYear = new Date().getFullYear();

export default function Layout({ children }) {
  return (
    <div className="min-h-full flex flex-col bg-bg text-fg">
      <Navbar />
      <main className="flex-1">
        <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">{children}</div>
      </main>
      <footer className="border-t border-line bg-surface/60 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 py-6 sm:flex-row sm:px-6">
          <div className="flex items-center gap-2 text-sm text-fg-muted">
            <img src="/excelra-mark.svg" alt="Excelra" className="h-6 w-6 rounded-md" />
            <span className="font-semibold text-fg">LearnSphere</span>
            <span className="text-fg-subtle">· by Excelra</span>
          </div>
          <p className="text-xs text-fg-subtle">
            © {currentYear} Excelra. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
