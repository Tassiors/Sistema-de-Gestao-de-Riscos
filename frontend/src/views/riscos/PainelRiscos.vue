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
        <span class="text-xs font-semibold text-rose-600 uppercase tracking-wider block">Acima do Apetite</span>
        <span class="text-2xl font-extrabold text-rose-600 mt-1 block">{{ estatisticas.totais?.ACIMA_APETITE || 0 }}</span>
      </div>
    </div>

    <!-- Matriz 5x5 e Filtros Rápidos -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2">
        <MatrizRisco5x5 :counts="estatisticas.quadrantes" />
      </div>

      <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-200 space-y-4">
        <h3 class="text-sm font-bold text-gray-800">Filtros de Visualização</h3>
        
        <div>
          <label class="block text-xs font-semibold text-gray-600 mb-1">Unidade Organizacional</label>
          <select v-model="filtroUnidade" @change="carregarMapeamentos" class="w-full text-xs border-gray-300 rounded-lg p-2 border">
            <option :value="null">Todas as Unidades Autorizadas</option>
            <option v-for="u in unidades" :key="u.id" :value="u.id">{{ u.nome }}</option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-semibold text-gray-600 mb-1">Status da Tramitação</label>
          <select v-model="filtroStatus" @change="carregarMapeamentos" class="w-full text-xs border-gray-300 rounded-lg p-2 border">
            <option :value="null">Todos os Status</option>
            <option value="RASCUNHO">Rascunho</option>
            <option value="SUBMETIDO">Submetido para UGERC</option>
            <option value="EM_MONITORAMENTO">Em Monitoramento</option>
          </select>
        </div>

        <div class="pt-2">
          <button 
            @click="limparFiltros" 
            class="w-full py-2 text-xs font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition"
          >
            Limpar Filtros
          </button>
        </div>
      </div>
    </div>

    <!-- Tabela de Mapeamentos -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
        <h3 class="text-sm font-bold text-gray-800">Fichas de Riscos Mapeados ({{ mapeamentos.length }})</h3>
      </div>

      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200 text-left text-xs">
          <thead class="bg-gray-50 text-gray-600 font-semibold uppercase tracking-wider text-[11px]">
            <tr>
              <th class="py-3 px-4">Setor / Unidade</th>
              <th class="py-3 px-4">Processo</th>
              <th class="py-3 px-4">Evento de Risco</th>
              <th class="py-3 px-4 text-center">Residual</th>
              <th class="py-3 px-4 text-center">Severidade</th>
              <th class="py-3 px-4 text-center">Status</th>
              <th class="py-3 px-4 text-right">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-if="mapeamentos.length === 0">
              <td colspan="7" class="py-8 text-center text-gray-400">
                Nenhum mapeamento de risco encontrado para os filtros selecionados.
              </td>
            </tr>
            <tr v-for="m in mapeamentos" :key="m.id" class="hover:bg-gray-50 transition">
              <td class="py-3.5 px-4 font-medium text-gray-900 max-w-xs truncate">
                {{ m.unidade?.nome }}
              </td>
              <td class="py-3.5 px-4 text-gray-600 max-w-xs truncate">
                <span class="block truncate">{{ m.processo?.nome }}</span>
                <span v-if="m.possui_projeto" class="text-[10px] text-blue-600 font-semibold block">Projeto: {{ m.nome_projeto }}</span>
              </td>
              <td class="py-3.5 px-4 text-gray-700 max-w-md truncate">
                <span v-if="m.eventos && m.eventos.length > 0">
                  {{ m.eventos[0].descricao_evento }}
                </span>
                <span v-else class="text-gray-400 italic">Sem eventos cadastrados</span>
              </td>
              <td class="py-3.5 px-4 text-center font-bold text-gray-900">
                {{ m.eventos && m.eventos[0]?.avaliacao ? m.eventos[0].avaliacao.risco_residual : '-' }}
              </td>
              <td class="py-3.5 px-4 text-center">
                <span 
                  v-if="m.eventos && m.eventos[0]?.avaliacao"
                  :class="getClassificacaoBadge(m.eventos[0].avaliacao.classificacao)"
                  class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase"
                >
                  {{ m.eventos[0].avaliacao.classificacao }}
                </span>
                <span v-else>-</span>
              </td>
              <td class="py-3.5 px-4 text-center">
                <span 
                  :class="m.status === 'RASCUNHO' ? 'bg-amber-100 text-amber-800' : 'bg-blue-100 text-blue-800'"
                  class="px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase"
                >
                  {{ m.status }}
                </span>
              </td>
              <td class="py-3.5 px-4 text-right space-x-2">
                <router-link 
                  :to="'/riscos/' + m.id + '/editar'"
                  class="text-blue-600 hover:text-blue-800 font-semibold"
                >
                  Editar
                </router-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import api from '../../services/api';
import MatrizRisco5x5 from '../../components/riscos/MatrizRisco5x5.vue';

const mapeamentos = ref<any[]>([]);
const unidades = ref<any[]>([]);
const estatisticas = ref<any>({ quadrantes: {}, totais: {} });

const filtroUnidade = ref<number | null>(null);
const filtroStatus = ref<string | null>(null);

function getClassificacaoBadge(classif: string) {
  switch (classif) {
    case 'BAIXO': return 'bg-emerald-100 text-emerald-800';
    case 'MEDIO': return 'bg-amber-100 text-amber-800';
    case 'ALTO': return 'bg-orange-100 text-orange-800';
    default: return 'bg-rose-100 text-rose-800';
  }
}

async function carregarEstatisticas() {
  try {
    const res = await api.get('/api/riscos/painel/matriz');
    estatisticas.value = res.data;
  } catch (err) {
    console.error('Erro ao carregar estatísticas:', err);
  }
}

async function carregarMapeamentos() {
  try {
    const params: any = {};
    if (filtroUnidade.value) params.unidade_id = filtroUnidade.value;
    if (filtroStatus.value) params.status = filtroStatus.value;
    const res = await api.get('/api/riscos', { params });
    mapeamentos.value = res.data;
  } catch (err) {
    console.error('Erro ao carregar mapeamentos:', err);
  }
}

async function carregarUnidades() {
  try {
    const res = await api.get('/api/unidades');
    unidades.value = res.data;
  } catch (err) {
    console.error('Erro ao carregar unidades:', err);
  }
}

function limparFiltros() {
  filtroUnidade.value = null;
  filtroStatus.value = null;
  carregarMapeamentos();
}

onMounted(async () => {
  await Promise.all([
    carregarEstatisticas(),
    carregarMapeamentos(),
    carregarUnidades()
  ]);
});
</script>
