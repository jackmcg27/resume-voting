import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../static',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/api/auth': { target: 'http://localhost:3001', changeOrigin: true },
      '/api': 'http://localhost:8000',
      '/uploads': 'http://localhost:8000',
      '/socket.io': { target: 'http://localhost:8000', changeOrigin: true, ws: true },
    },
  },
})
