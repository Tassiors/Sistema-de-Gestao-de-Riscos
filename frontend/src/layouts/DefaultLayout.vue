<template>
  <div class="relative h-screen overflow-hidden md:flex print:h-auto print:overflow-visible print:block">
    <!-- Mobile Menu Header -->
    <div class="bg-paper-sidebar text-gray-100 flex justify-between items-center px-4 py-3 md:hidden shrink-0 print:hidden">
      <router-link to="/riscos" class="flex items-center space-x-2 text-white font-bold">
        <img src="/siger_icon.jpg" alt="SIGER" class="w-8 h-8 rounded-lg object-contain bg-white p-0.5 shadow-sm" />
        <span>SIGER</span>
      </router-link>
      <button @click="sidebarOpen = !sidebarOpen" class="p-2 focus:outline-none focus:bg-paper-active-link rounded-lg">
        <Bars3Icon class="h-6 w-6" />
      </button>
    </div>

    <!-- Sidebar (Expansível / Recolhível) -->
    <aside 
      :class="[
        sidebarOpen ? 'translate-x-0' : '-translate-x-full',
        isCollapsed ? 'md:w-20' : 'md:w-64'
      ]" 
      class="bg-paper-sidebar text-gray-100 pt-7 pb-2 px-2 absolute inset-y-0 left-0 transform md:relative md:translate-x-0 transition-all duration-300 ease-in-out z-20 h-full shrink-0 flex flex-col justify-between print:hidden"
    >
      <div>
        <!-- Clique em "SIGER" recolhe/expande a barra lateral -->
        <div 
          @click="toggleSidebar" 
          title="Clique para recolher / expandir o menu"
          class="cursor-pointer text-white flex items-center space-x-3 px-3 mb-6 hover:opacity-95 transition duration-150 group"
        >
          <div class="w-10 h-10 rounded-xl bg-white p-0.5 shadow-sm flex items-center justify-center shrink-0 overflow-hidden group-hover:scale-105 transition-transform">
            <img src="/siger_icon.jpg" alt="SIGER" class="w-full h-full object-contain rounded-lg" />
          </div>
          <div v-if="!isCollapsed" class="truncate select-none">
            <span class="text-lg font-black tracking-wider text-white block leading-tight">SIGER</span>
            <span class="text-[9px] font-semibold text-emerald-300 tracking-wider block uppercase truncate">Gestão de Riscos</span>
          </div>
        </div>

        <div class="px-3 my-4">
          <div class="border-t border-white border-opacity-20"></div>
        </div>

        <!-- Links de Navegação -->
        <nav class="space-y-2">
          <router-link 
            v-if="authStore.isAuthenticated" 
            to="/riscos" 
            :title="isCollapsed ? 'Painel de Riscos' : ''"
            :class="[isCollapsed ? 'justify-center px-2' : 'px-4']"
            class="flex items-center space-x-3 py-2.5 rounded transition duration-200 hover:bg-paper-active-link hover:text-white"
          >
            <ShieldExclamationIcon class="h-6 w-6 shrink-0 text-amber-300" />
            <span v-if="!isCollapsed" class="truncate font-medium">Painel de Riscos</span>
          </router-link>

          <router-link 
            v-if="authStore.isAuthenticated" 
            to="/riscos/novo" 
            :title="isCollapsed ? 'Novo Mapeamento' : ''"
            :class="[isCollapsed ? 'justify-center px-2' : 'px-4']"
            class="flex items-center space-x-3 py-2.5 rounded transition duration-200 hover:bg-paper-active-link hover:text-white"
          >
            <PlusCircleIcon class="h-6 w-6 shrink-0 text-emerald-300" />
            <span v-if="!isCollapsed" class="truncate font-medium">Novo Mapeamento</span>
          </router-link>

          <router-link 
            v-if="authStore.isAuthenticated" 
            to="/riscos/mapeados" 
            :title="isCollapsed ? 'Riscos Mapeados' : ''"
            :class="[isCollapsed ? 'justify-center px-2' : 'px-4']"
            class="flex items-center space-x-3 py-2.5 rounded transition duration-200 hover:bg-paper-active-link hover:text-white"
          >
            <ClipboardDocumentListIcon class="h-6 w-6 shrink-0 text-cyan-300" />
            <span v-if="!isCollapsed" class="truncate font-medium">Riscos Mapeados</span>
          </router-link>

          <router-link 
            v-if="authStore.isAuthenticated && authStore.isAdmin" 
            to="/admin/usuarios" 
            :title="isCollapsed ? 'Gestores & Visibilidade' : ''"
            :class="[isCollapsed ? 'justify-center px-2' : 'px-4']"
            class="flex items-center space-x-3 py-2.5 rounded transition duration-200 hover:bg-paper-active-link hover:text-white"
          >
            <UsersIcon class="h-6 w-6 shrink-0 text-blue-300" />
            <span v-if="!isCollapsed" class="truncate">Gestores & Visibilidade</span>
          </router-link>
        </nav>
      </div>

      <!-- Rodapé de Versão da Sidebar -->
      <div v-if="!isCollapsed" class="px-4 pt-3 pb-1 border-t border-white/10 text-xs text-gray-400 mt-auto truncate transition-opacity duration-200">
        <p class="font-semibold text-gray-200 truncate">{{ APP_NAME }}</p>
        <p class="text-[11px] text-gray-400 truncate">Versão {{ APP_VERSION }} | HC-UFPE</p>
      </div>
      <div v-else class="px-2 pt-3 pb-1 border-t border-white/10 text-[10px] text-center text-gray-400 mt-auto">
        v{{ APP_VERSION }}
      </div>
    </aside>

    <!-- Content -->
    <div class="flex-1 flex flex-col bg-paper-bg overflow-y-auto h-full print:h-auto print:overflow-visible print:bg-white print:block">
      <header class="flex justify-between items-center p-6 bg-white/80 backdrop-blur-md border-b border-gray-300 sticky top-0 z-10 print:hidden">
        <div>
          <h1 class="text-2xl font-semibold text-paper-text">{{ $route.name }}</h1>
        </div>
        <div>
          <router-link v-if="!authStore.isAuthenticated" to="/login">
            <Button variant="primary">
              <template #icon>
                <ArrowRightOnRectangleIcon class="h-5 w-5" />
              </template>
              Login
            </Button>
          </router-link>
          <ProfileDropdown v-else />
        </div>
      </header>
      <main class="flex-1 print:p-0 print:m-0 print:block">
        <div class="container py-4 md:py-6 print:p-0 print:m-0 print:max-w-none print:w-full">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import {
  Bars3Icon,
  ArrowRightOnRectangleIcon,
  ShieldExclamationIcon,
  ClipboardDocumentListIcon,
  PlusCircleIcon,
  UsersIcon,
} from '@heroicons/vue/24/outline';
import ProfileDropdown from '../components/ProfileDropdown.vue';
import Button from '../components/Button.vue';
import { useAuthStore } from '../stores/auth';
import { APP_VERSION, APP_NAME } from '../config/version';

const sidebarOpen = ref(false);
const isCollapsed = ref(false);

const route = useRoute();
const authStore = useAuthStore();

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value;
};

// Close mobile sidebar on route change
watch(() => route.path, () => {
  sidebarOpen.value = false;
});
</script>