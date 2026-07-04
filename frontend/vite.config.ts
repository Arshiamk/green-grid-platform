import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    // Mirror the nginx setup used in Docker: the SPA calls /api on its own
    // origin and the dev server forwards it to the Django backend.
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
})
