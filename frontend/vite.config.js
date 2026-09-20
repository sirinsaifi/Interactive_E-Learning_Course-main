import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiTarget = env.VITE_API_PROXY_TARGET || "http://localhost:8000";

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "src"),
      },
    },
    server: {
      host: true,
      port: 5174,
      strictPort: false,
      // Allow any *.nip.io subdomain (we use it for VM deploys behind Caddy /
      // nginx). For other custom domains, set VITE_ALLOWED_HOSTS to a comma-
      // separated list in the environment.
      allowedHosts: [
        ".nip.io",
        ...(env.VITE_ALLOWED_HOSTS
          ? env.VITE_ALLOWED_HOSTS.split(",").map((h) => h.trim()).filter(Boolean)
          : []),
      ],
      proxy: {
        "/api": {
          target: apiTarget,
          changeOrigin: true,
        },
      },
    },
    preview: {
      port: 4173,
    },
    build: {
      outDir: "dist",
      sourcemap: true,
    },
  };
});
