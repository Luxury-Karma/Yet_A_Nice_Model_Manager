import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    host: '127.0.0.1', // Forces Vite to use explicit IPv4 instead of ambiguous localhost
    port: 5173,
    proxy: {
      // Directs frontend API traffic smoothly over to your Flask application
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
});