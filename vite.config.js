import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    proxy: {
      // Forwards /api/* to the Express backend during development so the
      // frontend can call fetch('/api/...') with no CORS/base-URL juggling.
      '/api': {
        target: 'http://localhost:4000',
        changeOrigin: true,
      },
    },
  },
});
