import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // Ensure production builds work correctly
    outDir: 'dist',
    sourcemap: false,
    minify: 'terser',
  },
  define: {
    // Ensure production mode is set correctly
    __APP_ENV__: JSON.stringify(process.env.NODE_ENV || 'development'),
  },
})
