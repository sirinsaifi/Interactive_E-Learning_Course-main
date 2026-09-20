import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <section className="py-20 text-center">
      <p className="text-sm font-semibold uppercase tracking-wider text-brand-600">404</p>
      <h1 className="mt-2 text-4xl font-bold tracking-tight text-fg">Page not found</h1>
      <p className="mt-2 text-fg-subtle">The page you’re looking for doesn’t exist.</p>
      <Link
        to="/"
        className="mt-6 inline-block rounded-full bg-brand-600 px-5 py-2 text-sm font-medium text-brand-fg shadow-sm transition hover:bg-brand-700"
      >
        Go home
      </Link>
    </section>
  );
}
