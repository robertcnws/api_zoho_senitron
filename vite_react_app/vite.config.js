import path from 'path';
import checker from 'vite-plugin-checker';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import { VitePWA } from 'vite-plugin-pwa';

// ----------------------------------------------------------------------

const PORT = 3030;

const lowMem = process.env.CI_LOW_MEM_BUILD === '1';

const enablePWA = process.env.VITE_DISABLE_PWA !== '1';

export default defineConfig({
  plugins: [
    react(),
    checker({
      eslint: {
        lintCommand: 'eslint "./src/**/*.{js,jsx,ts,tsx}"',
        dev: { logLevel: ['error'] },
      },
      overlay: {
        position: 'tl',
        initialIsOpen: false,
      },
    }),
    ...(enablePWA ? [VitePWA({
      registerType: 'autoUpdate',
      // workbox: {
      //   maximumFileSizeToCacheInBytes: 10 * 1024 * 1024,
      // },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        maximumFileSizeToCacheInBytes: 10 * 1024 * 1024,
        manifestTransforms: [
          async (entries) => {
            const manifest = entries.filter((e) => !/\/assets\/vendor-react-.*\.js$/.test(e.url))
            return { manifest, warnings: [] }
          },
        ],
        runtimeCaching: [
          {
            urlPattern: ({ sameOrigin, url }) => sameOrigin && url.pathname.startsWith('/assets/vendor-react-'),
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'vendor-react',
              expiration: { maxEntries: 5, maxAgeSeconds: 60 * 60 * 24 * 7 },
            },
          },
        ],
      },
      includeAssets: ['favicon.ico', 'robots.txt', 'apple-touch-icon.png'],
      manifest: {
        name: 'WMS App',
        short_name: 'WMS App',
        description: 'WMS APP',
        theme_color: '#ffffff',
        icons: [
          {
            src: '/icons/icon-192x192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: '/icons/icon-512x512.png',
            sizes: '512x512',
            type: 'image/png',
          },
          {
            src: '/icons/icon-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable',
          },
        ],
      },
    })] : []),
  ],
  resolve: {
    alias: [
      {
        find: /^~(.+)/,
        replacement: path.join(process.cwd(), 'node_modules/$1'),
      },
      {
        find: /^src(.+)/,
        replacement: path.join(process.cwd(), 'src/$1'),
      },
    ],
  },
  server: { port: PORT, host: true },
  preview: { port: PORT, host: true },
  build: {
    sourcemap: false,
    minify: lowMem ? false : 'esbuild',
    cssMinify: lowMem ? false : true,
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('react')) return 'vendor-react'
            if (id.includes('@mui')) return 'vendor-mui'
            if (id.includes('@tanstack') || id.includes('@apollo')) return 'vendor-graphql'
            if (id.includes('date-fns') || id.includes('dayjs')) return 'vendor-dates'
            if (id.includes('lodash')) return 'vendor-lodash'
            return 'vendor'
          }
        },
      },
      treeshake: true,
    },
  },
});
