// astro.config.mjs
import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import dotenv from 'dotenv';
dotenv.config();

export default defineConfig({
  integrations: [tailwind()],
  vite: {
    define: {
      'import.meta.env.API_URL': JSON.stringify(process.env.API_URL),
    },
    server: {
      proxy: {
        '/api/auth': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          secure: false,
        },
      },
    },
  },
});
