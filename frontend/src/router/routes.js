const routes = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'dashboard',
        component: () => import('pages/DashboardPage.vue')
      },
      {
        path: 'analytics',
        name: 'analytics',
        component: () => import('pages/AnalyticsPage.vue')
      },
      {
        path: 'hubs',
        name: 'hubs',
        component: () => import('pages/HubsPage.vue')
      },
      {
        path: 'hubs/:id',
        name: 'hub-detail',
        component: () => import('pages/HubDetailPage.vue')
      },
      {
        path: 'batteries',
        name: 'batteries',
        component: () => import('pages/BatteriesPage.vue')
      },
      {
        path: 'batteries/:id',
        name: 'battery-detail',
        component: () => import('pages/BatteryDetailPage.vue')
      },
      {
        path: 'users',
        name: 'users',
        meta: { requiresAdmin: true },
        component: () => import('pages/UsersPage.vue')
      },
      {
        path: 'pue',
        name: 'pue',
        component: () => import('pages/PUEPage.vue')
      },
      {
        path: 'rentals',
        name: 'rentals',
        component: () => import('pages/RentalsPage.vue')
      },
      {
        path: 'rentals/:id',
        name: 'rental-detail',
        component: () => import('pages/RentalDetailPage.vue')
      },
      {
        path: 'admin/webhooks',
        name: 'webhook-logs',
        meta: { requiresAdmin: true },
        component: () => import('pages/admin/WebhookLogsPage.vue')
      }
    ]
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('pages/LoginPage.vue')
  },
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue')
  }
]

export default routes
