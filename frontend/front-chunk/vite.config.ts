import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Accepte toutes les connexions
    port: 5173,
    strictPort: false
  },
  preview: {
    host: true, // Accepte toutes les connexions
    port: process.env.PORT ? parseInt(process.env.PORT) : 5173,
    strictPort: false,
    cors: true
  }
})