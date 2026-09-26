/**
 * Configuration file for backend API connection.
 *
 * Set VITE_API_BASE_URL in your environment (or a .env file) to point at the
 * deployed backend.  Vite replaces `import.meta.env.VITE_*` variables at
 * build time, so the correct URL is baked into the static bundle.
 *
 * Local development  →  no .env needed; falls back to http://localhost:8000
 * Production (Vercel) →  set VITE_API_BASE_URL=https://your-app.onrender.com
 */
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
