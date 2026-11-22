import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: { '/api': { target: process.env.API_PROXY_TARGET || 'http://127.0.0.1:8099', changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '') } },
  },
  build: {
    rollupOptions: { output: { manualChunks: (id) => {
      if (id.includes('node_modules/leaflet/')) return 'leaflet';
      if (id.includes('node_modules/@mui/') || id.includes('node_modules/@emotion/')) return 'ui';
      if (id.includes('node_modules/framer-motion/') || id.includes('node_modules/motion-')) return 'motion';
    } } },
  },
});
