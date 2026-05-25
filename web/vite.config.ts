import { defineConfig } from 'vite'

// Minimal Vite config without importing the ESM-only plugin to avoid
// require/ESM interop issues in some Node/npm setups. You can re-add
// `@vitejs/plugin-react` later if your environment supports ESM plugins.
export default defineConfig({
    server: {
        port: 5173,
    },
})
