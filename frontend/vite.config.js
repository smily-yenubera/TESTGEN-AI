import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  // ── Development server ────────────────────────────────────────────────────
  server: {
    port: 3000,
    host: 'localhost',
  },

  // ── Production build ──────────────────────────────────────────────────────
  build: {
    // Output directory (default is 'dist').  Vercel picks this up automatically
    // when the framework is set to "Vite" or "Other" with root directory "frontend".
    outDir: 'dist',
    // Generate source maps so errors in production can be traced back to source.
    sourcemap: false,
  },

  // Vite automatically exposes any env variable whose name starts with VITE_
  // to the client bundle via import.meta.env.  No extra configuration is
  // required here; this comment is a reminder of the naming convention.
  // Set VITE_API_BASE_URL in the Vercel environment variables dashboard.
})
