import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  root: ".",
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    host: "0.0.0.0"
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          // React core
          if (id.includes('node_modules/react/') ||
              id.includes('node_modules/react-dom/') ||
              id.includes('node_modules/react-router')) {
            return 'react-vendor';
          }
          // Map libraries
          if (id.includes('node_modules/maplibre-gl/') ||
              id.includes('node_modules/react-map-gl/')) {
            return 'map-vendor';
          }
          // UI libraries
          if (id.includes('node_modules/framer-motion/') ||
              id.includes('node_modules/lucide-react/')) {
            return 'ui-vendor';
          }
          // Radix UI components
          if (id.includes('node_modules/@radix-ui/')) {
            return 'radix-vendor';
          }
        },
      },
    },
    chunkSizeWarningLimit: 600,
  },
});
