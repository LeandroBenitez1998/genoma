import vinext from "vinext";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [vinext()],

  // Proxy /api/* to FastAPI backend (:8000)
  // Vinext también lee next.config.ts rewrites, pero esto es explícito
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
