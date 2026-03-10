const { configure } = require('quasar/wrappers');

module.exports = configure(function (/* ctx */) {
  return {
    boot: ['axios', 'auth', 'offline'],

    css: ['app.css'],

    extras: [
      'roboto-font',
      'material-icons',
      'material-icons-outlined',
      'fontawesome-v6'
    ],

    build: {
      target: {
        browser: ['es2019', 'edge88', 'firefox78', 'chrome87', 'safari13.1'],
        node: 'node16'
      },

      vueRouterMode: 'hash',

      env: {
        API_URL: process.env.API_URL || 'http://localhost:8000',
        PANEL_URL: process.env.PANEL_URL || 'http://localhost:5100'
      }
    },

    devServer: {
      open: true,
      port: 9000
    },

    framework: {
      config: {
        brand: {
          primary: '#1976D2',
          secondary: '#26A69A',
          accent: '#9C27B0',
          dark: '#1d1d1d',
          positive: '#21BA45',
          negative: '#C10015',
          info: '#31CCEC',
          warning: '#F2C037'
        }
      },

      iconSet: 'material-icons',
      lang: 'en-US',

      plugins: ['Notify', 'Dialog', 'Loading', 'LocalStorage', 'SessionStorage']
    },

    animations: [],

    pwa: {
      workboxMode: 'generateSW',
      injectPwaMetaTags: false,  // Disable automatic meta tag injection to avoid CSP conflicts
      swFilename: 'sw.js',
      manifestFilename: 'manifest.json',
      useCredentialsForManifestTag: false,

      workboxOptions: {
        skipWaiting: true,
        clientsClaim: true,
        navigateFallback: 'index.html',
        navigateFallbackDenylist: [/^\/api/, /^\/auth/],
        runtimeCaching: [
          {
            urlPattern: /\/(hubs|batteries|users|pue|rentals|battery-rentals|pue-rentals|settings|notifications|job-cards|accounts|analytics|data|inspections|return-survey|subscriptions)\b/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxAgeSeconds: 60 * 60 // 1 hour
              },
              networkTimeoutSeconds: 5
            }
          },
          {
            urlPattern: /\.(png|jpg|jpeg|svg|gif|webp|ico|woff2?|ttf|eot)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'static-assets',
              expiration: {
                maxAgeSeconds: 7 * 24 * 60 * 60 // 1 week
              }
            }
          }
        ]
      },

      manifest: {
        name: 'BEPPP',
        short_name: 'BEPPP',
        description: 'Battery Rental Management System',
        display: 'standalone',
        orientation: 'portrait',
        background_color: '#ffffff',
        theme_color: '#1976D2',
        icons: [
          {
            src: 'icons/icon-128x128.png',
            sizes: '128x128',
            type: 'image/png',
            purpose: 'any'
          },
          {
            src: 'icons/icon-192x192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any'
          },
          {
            src: 'icons/icon-256x256.png',
            sizes: '256x256',
            type: 'image/png',
            purpose: 'any'
          },
          {
            src: 'icons/icon-384x384.png',
            sizes: '384x384',
            type: 'image/png',
            purpose: 'any'
          },
          {
            src: 'icons/icon-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any'
          }
        ]
      }
    }
  };
});
