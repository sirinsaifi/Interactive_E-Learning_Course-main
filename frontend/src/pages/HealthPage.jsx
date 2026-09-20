import { useCallback } from "react";

import Spinner from "../components/Spinner.jsx";
import useFetch from "../hooks/useFetch.js";
import { healthService } from "../services/healthService.js";

export default function HealthPage() {
  const fetcher = useCallback(() => healthService.status(), []);
  const { data, error, loading, refetch } = useFetch(fetcher, []);

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight text-fg">API health</h1>
        <button
          type="button"
          onClick={refetch}
          className="rounded-full bg-brand-600 px-4 py-1.5 text-sm font-medium text-brand-fg shadow-sm transition hover:bg-brand-700"
        >
          Refresh
        </button>
      </div>

      {loading && <Spinner />}

      {error && (
        <div className="rounded-2xl border border-danger/30 bg-danger-soft p-4 text-sm text-danger-soft-fg">
          Failed to reach the API.
          <pre className="mt-2 whitespace-pre-wrap text-xs">
            {error?.message || String(error)}
          </pre>
        </div>
      )}

      {data && (
        <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Field label="Status" value={data.status} highlight={data.status === "ok"} />
          <Field label="Database" value={data.database} highlight={data.database === "ok"} />
          <Field label="App" value={data.app} />
          <Field label="Version" value={data.version} />
          <Field label="Environment" value={data.environment} />
        </dl>
      )}
    </section>
  );
}

function Field({ label, value, highlight }) {
  return (
    <div className="rounded-2xl border border-line bg-surface p-4 shadow-[var(--shadow-card)]">
      <dt className="text-xs uppercase tracking-wide text-fg-subtle">{label}</dt>
      <dd
        className={`mt-1 text-sm font-medium ${
          highlight ? "text-success" : "text-fg"
        }`}
      >
        {value}
      </dd>
    </div>
  );
}
