export default function Spinner({ label = "Loading…" }) {
  return (
    <div className="flex items-center gap-2 text-sm text-fg-subtle">
      <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-line border-t-brand-600" />
      <span>{label}</span>
    </div>
  );
}
