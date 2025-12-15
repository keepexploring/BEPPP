const { configure } = require('quasar/wrappers');

module.exports = configure(function (/* ctx */) {
  return {
    boot: ['axios', 'auth'],

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
      injectPwaMetaTags: true,
      swFilename: 'sw.js',
      manifestFilename: 'manifest.json',
      useCredentialsForManifestTag: false,

      // Custom CSP for PWA - allow API and Panel connections
      metaVariables: {
        appleMobileWebAppCapable: 'yes',
        appleMobileWebAppStatusBarStyle: 'default',
        appleTouchIcon120: 'icons/apple-icon-120x120.png',
        appleTouchIcon180: 'icons/apple-icon-180x180.png',
        appleTouchIcon152: 'icons/apple-icon-152x152.png',
        appleTouchIcon167: 'icons/apple-icon-167x167.png',
        appleSafariPinnedTab: 'icons/safari-pinned-tab.svg',
        msapplicationTileImage: 'icons/ms-icon-144x144.png',
        msapplicationTileColor: '#000000'
      },

      metaVariablesFn: (manifest) => {
        return [{
          // Override CSP to allow API connections
          tagName: 'meta',
          attributes: {
            'http-equiv': 'Content-Security-Policy',
            content: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' data: https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.beppp.cloud https://panel.beppp.cloud wss: ws:;"
          }
        }]
      },

      manifest: {
        name: 'Battery Hub Manager',
        short_name: 'Battery Hub',
        description: 'Battery Rental Management System',
        display: 'standalone',
        orientation: 'portrait',
        background_color: '#ffffff',
        theme_color: '#1976D2',
        icons: [
          {
            src: 'icons/icon-128x128.png',
            sizes: '128x128',
            type: 'image/png'
          },
          {
            src: 'icons/icon-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'icons/icon-256x256.png',
            sizes: '256x256',
            type: 'image/png'
          },
          {
            src: 'icons/icon-384x384.png',
            sizes: '384x384',
            type: 'image/png'
          },
          {
            src: 'icons/icon-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
    }
  };
});
