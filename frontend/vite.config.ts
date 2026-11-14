import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// `base` must match the GitHub repository name so assets resolve on
// https://<user>.github.io/chicago-menu-time-machine/
export default defineConfig({
  base: '/chicago-menu-time-machine/',
  plugins: [react(), tailwindcss()],
})
