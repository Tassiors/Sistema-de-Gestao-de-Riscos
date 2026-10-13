import { createRouter, createWebHistory, NavigationGuardNext } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import Login from '../views/Login.vue';
import PainelRiscos from '../views/riscos/PainelRiscos.vue';
import MapeamentoWizard from '../views/riscos/MapeamentoWizard.vue';
import GestaoUsuariosVisibilidade from '../views/admin/GestaoUsuariosVisibilidade.vue';

const routes = [
  {
    path: '/',
    redirect: '/riscos',
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { layout: 'LoginLayout' },
  },
  {
    path: '/riscos',
    name: 'Painel de Riscos',
    component: PainelRiscos,
    meta: { requiresAuth: true },
  },
  {
    path: '/riscos/novo',
    name: 'Novo Mapeamento',
    component: MapeamentoWizard,
    meta: { requiresAuth: true },
  },
  {
    path: '/riscos/:id/editar',
    name: 'Editar Mapeamento',
    component: MapeamentoWizard,
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/usuarios',
    name: 'Gestão de Usuários & Visibilidade',
    component: GestaoUsuariosVisibilidade,
    meta: { requiresAuth: true, requiresAdmin: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  linkActiveClass: 'bg-paper-active-link',
  linkExactActiveClass: 'bg-paper-active-link',
});

router.beforeEach((to, _from, next: NavigationGuardNext) => {
  // Pinia store must be used inside a function to ensure it's initialized
  const authStore = useAuthStore();

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login' });
  } else if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next({ path: '/riscos' });
  } else {
    next();
  }
});

export default router;
