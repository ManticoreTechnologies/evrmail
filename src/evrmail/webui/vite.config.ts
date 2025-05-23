import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { viteSingleFile } from 'vite-plugin-singlefile'

export default defineConfig({
  plugins: [react(), viteSingleFile()],
  build: {
    target: 'esnext',
    assetsInlineLimit: Infinity,
    rollupOptions: {
      output: {
        // Removed manualChunks as it conflicts with inlineDynamicImports used by viteSingleFile
      },
    },
  },
})
