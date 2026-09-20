# LearnSphere Frontend (React 19 + Vite)

Single-page application that talks to the FastAPI backend.

## Stack

- React 19
- Vite 6
- React Router v7
- Axios
- Tailwind CSS v4 (via `@tailwindcss/vite`)

## Project layout

```
src/
  components/     # Reusable presentational components (Navbar, Layout, Spinner)
  pages/          # Route-level pages
  routes/         # Route table
  services/       # Axios client + per-domain API services
  hooks/          # Reusable hooks (useFetch, …)
  context/        # React context providers (app-wide state)
  index.css       # Tailwind entry
  main.jsx        # App bootstrap
  App.jsx         # App shell
```

## Getting started

```bash
cd frontend
copy .env.example .env          # Windows
# cp .env.example .env          # macOS / Linux
npm install
npm run dev
```

Visit <http://localhost:5173>.

The dev server proxies `/api/*` to `VITE_API_PROXY_TARGET` (default `http://localhost:8000`),
so axios calls to `/api/v1/health` reach the FastAPI backend without CORS friction.

## Adding a new feature (template)

1. Create the API client in `src/services/<feature>Service.js`.
2. Create the page in `src/pages/<Feature>Page.jsx`.
3. Register the route in `src/routes/AppRoutes.jsx`.
4. Add navigation to `src/components/Navbar.jsx` if needed.

## Build

```bash
npm run build      # outputs to dist/
npm run preview    # serve the built bundle
```
