import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Local dev runs behind the SWA CLI (`swa start`, see swa-cli.config.json at the
// repo root), which serves this dev server on http://localhost:4280 and emulates
// /.auth and the /api proxy.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, strictPort: true },
});
