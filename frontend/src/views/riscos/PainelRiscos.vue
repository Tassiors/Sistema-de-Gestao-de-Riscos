<template>
  <div class="space-y-6">
    <!-- Header com Ação Principal -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-xl shadow-sm border border-gray-200">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Painel Geral de Gestão de Riscos</h2>
        <p class="text-xs text-gray-500 mt-1">Acompanhamento dos riscos mapeados, severidade e planos de ação.</p>
      </div>
      <div>
        <router-link 
          to="/riscos/novo" 
          class="inline-flex items-center px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg shadow-sm transition space-x-2"
        >
          <span>+ Novo Mapeamento</span>
        </router-link>
      </div>
    </div>

    <!-- Cards de Métricas e Totais -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
      <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-200 text-center">
        <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider block">Total Mapeados</span>
        <span class="text-2xl font-extrabold text-gray-900 mt-1 block">{{ estatisticas.totais?.TOTAL || 0 }}</span>
      </div>
      <div class="bg-white p-4 rounded-xl shadow-sm border border-emerald-100 text-center">
        <span class="text-xs font-semibold text-emerald-600 uppercase tracking-wider block">Risco Baixo</span>
        <span class="text-2xl font-extrabold text-emerald-600 mt-1 block">{{ estatisticas.totais?.BAIXO || 0 }}</span>
      </div>
      <div class="bg-white p-4 rounded-xl shadow-sm border border-amber-100 text-center">
        <span class="text-xs font-semibold text-amber-600 uppercase tracking-wider block">Risco Médio</span>
        <span class="text-2xl font-extrabold text-amber-600 mt-1 block">{{ estatisticas.totais?.MEDIO || 0 }}</span>
      </div>
      <div class="bg-white p-4 rounded-xl shadow-sm border border-orange-100 text-center">
        <span class="text-xs font-semibold text-orange-600 uppercase tracking-wider block">Risco Alto</span>
        <span class="text-2xl font-extrabold text-orange-600 mt-1 block">{{ estatisticas.totais?.ALTO || 0 }}</span>
      </div>
      <div class="bg-white p-4 rounded-xl shadow-sm border border-rose-100 text-center col-span-2 md:col-span-1">
        <span class="text-xs font-semibold text-rose-600 uppercase tracking-wider block">Risco Extremo</span>
        <span class="text-2xl font-extrabold text-rose-600 mt-1 block">{{ estatisticas.totais?.EXTREMO || 0 }}</span>
      </div>
    </div>

    <!-- Matriz 5x5 e Filtros Rápidos -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2">
        <MatrizRisco5x5 :counts="estatisticas.quadrantes" />
      </div>

      <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-200 space-y-4 flex flex-col justify-between">
        <div>
          <h3 class="text-sm font-bold text-gray-800 flex items-center gap-1.5">
            <span>🛡️</span>
            <span>Diretrizes de Governança</span>
          </h3>
          <p class="text-xs text-gray-500 mt-1 leading-relaxed">
            A Matriz 5x5 reflete a distribuição dos riscos mapeados com status <strong>SUBMETIDO</strong> no HC-UFPE.
          </p>

          <div class="mt-4 p-3.5 bg-blue-50/70 rounded-xl border border-blue-100 text-xs space-y-2">
            <span class="font-bold text-blue-900 block">Tolerância Institucional</span>
            <p class="text-[11px] text-blue-800 leading-relaxed">
              Riscos com resultado residual <strong>superior a 7,99</strong> (Alto ou Extremo) excedem o apetite institucional e exigem obrigatoriamente a elaboração de Planos de Ação 5W2H e Planos de Contingência.
            </p>
          </div>
        </div>

        <div class="space-y-2 pt-4 border-t border-gray-100">
          <router-link 
            to="/riscos/mapeados" 
            class="w-full py-2.5 px-3 text-xs font-bold text-center text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg transition block"
          >
            📋 Ver Todas as Fichas Mapeadas
          </router-link>
          <router-link 
            to="/riscos/novo" 
            class="w-full py-2.5 px-3 text-xs font-bold text-center text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition block"
          >
            + Novo Mapeamento
          </router-link>
        </div>
      </div>
    </div>

    <!-- Card / Banner de Atalho para Fichas de Riscos Mapeados -->
    <div class="bg-gradient-to-r from-blue-900 to-indigo-900 text-white rounded-xl shadow-md p-6 flex flex-col md:flex-row items-center justify-between gap-4">
      <div class="space-y-1 text-center md:text-left">
        <h3 class="text-lg font-bold flex items-center justify-center md:justify-start gap-2">
          <span>📋</span>
          <span>Fichas de Riscos Mapeados</span>
        </h3>
        <p class="text-xs text-blue-200 max-w-xl leading-relaxed">
          Acesse a listagem detalhada de todas as fichas cadastradas, com filtros avançados por unidade (busca textual), status de tramitação, permissões de edição e exportação.
        </p>
      </div>
      <div>
        <router-link 
          to="/riscos/mapeados" 
          class="inline-flex items-center gap-2 px-5 py-2.5 bg-white text-blue-900 hover:bg-blue-50 text-xs font-bold rounded-lg shadow transition"
        >
          <span>Abrir Riscos Mapeados</span>
          <span>→</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import api from '../../services/api';
import MatrizRisco5x5 from '../../components/riscos/MatrizRisco5x5.vue';

const estatisticas = ref<any>({ quadrantes: {}, totais: {} });

async function carregarEstatisticas() {
  try {
    const res = await api.get('/api/riscos/painel/matriz');
    estatisticas.value = res.data;
  } catch (err) {
    console.error('Erro ao carregar estatísticas:', err);
  }
}

onMounted(async () => {
  await carregarEstatisticas();
});
</script>
