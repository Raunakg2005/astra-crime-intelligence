import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies /api to the local FastAPI analytics service (port 8000).
// In production the SPA is served by Catalyst Web Client Hosting and talks to the
// AppSail analytics service via the Catalyst API Gateway.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/health": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },
  build: { outDir: "dist", chunkSizeWarningLimit: 1500 },
});
