import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/login', component: () => import('@/views/LoginView.vue'), meta: { guest: true } },
  { path: '/register', component: () => import('@/views/LoginView.vue'), meta: { guest: true } },
  { path: '/dashboard', component: () => import('@/views/DashboardView.vue'), meta: { requiresAuth: true } },
  { path: '/accounts', component: () => import('@/views/AccountsView.vue'), meta: { requiresAuth: true } },
  { path: '/loans', component: () => import('@/views/LoansView.vue'), meta: { requiresAuth: true } },
  { path: '/loans/:id', component: () => import('@/views/LoanDetailView.vue'), meta: { requiresAuth: true } },
  { path: '/recurring', component: () => import('@/views/RecurringView.vue'), meta: { requiresAuth: true } },
  { path: '/categories', component: () => import('@/views/CategoriesView.vue'), meta: { requiresAuth: true } },
  { path: '/transactions', component: () => import('@/views/TransactionsView.vue'), meta: { requiresAuth: true } },
  { path: '/reports', component: () => import('@/views/ReportsView.vue'), meta: { requiresAuth: true } },
  { path: '/year', component: () => import('@/views/YearView.vue'), meta: { requiresAuth: true } },
  { path: '/month', component: () => import('@/views/MonthView.vue'), meta: { requiresAuth: true } },
  { path: '/net-worth', component: () => import('@/views/NetWorthView.vue'), meta: { requiresAuth: true } },
  { path: '/goals', component: () => import('@/views/GoalsView.vue'), meta: { requiresAuth: true } },
  { path: '/import', component: () => import('@/views/ImportView.vue'), meta: { requiresAuth: true } },
  { path: '/settings', component: () => import('@/views/SettingsView.vue'), meta: { requiresAuth: true } },
  { path: '/backup', component: () => import('@/views/BackupView.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin', component: () => import('../views/AdminView.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/oidc-callback', component: () => import('../views/OidcCallbackView.vue') },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (auth.token && !auth.user) {
    try { await auth.fetchUser() } catch {}
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { path: '/login' }
  }
  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return { path: '/dashboard' }
  }
  if (to.meta.guest && auth.isAuthenticated) {
    return { path: '/dashboard' }
  }
})

export default router
