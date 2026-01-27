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
        component: () => import('pages/UsersPage.vue')
      },
      {
        path: 'users/:id',
        name: 'user-detail',
        component: () => import('pages/UserDetailPage.vue')
      },
      {
        path: 'pue',
        name: 'pue',
        component: () => import('pages/PUEPage.vue')
      },
      {
        path: 'pue/:id',
        name: 'pue-detail',
        component: () => import('pages/PUEDetailPage.vue')
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
        path: 'rentals/battery/create',
        name: 'create-battery-rental',
        component: () => import('pages/CreateBatteryRentalPage.vue')
      },
      {
        path: 'rentals/pue/create',
        name: 'create-pue-rental',
        component: () => import('pages/CreatePUERentalPage.vue')
      },
      {
        path: 'rentals/battery/:id',
        name: 'battery-rental-detail',
        component: () => import('pages/RentalDetailPage.vue')
      },
      {
        path: 'rentals/pue/:id',
        name: 'pue-rental-detail',
        component: () => import('pages/RentalDetailPage.vue')
      },
      {
        path: 'admin/webhooks',
        name: 'webhook-logs',
        meta: { requiresAdmin: true },
        component: () => import('pages/admin/WebhookLogsPage.vue')
      },
      {
        path: 'settings',
        name: 'settings',
        meta: { requiresAdmin: true },
        component: () => import('pages/SettingsPage.vue')
      },
      {
        path: 'accounts',
        name: 'accounts',
        meta: { requiresAdmin: true },
        component: () => import('pages/AccountsPage.vue')
      },
      {
        path: 'job-cards',
        name: 'job-cards',
        component: () => import('pages/JobCardsPage.vue')
      },
      {
        path: 'help',
        name: 'help',
        component: () => import('pages/HelpPage.vue')
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
