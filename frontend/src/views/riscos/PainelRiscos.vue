<template>
  <div class="space-y-6">
    <!-- Header Institucional -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-xl shadow-sm border border-gray-200">
      <div>
        <h2 class="text-xl font-bold text-gray-900 flex items-center gap-2">
          <span>📊</span>
          <span>SIGER — Painel Geral de Gestão de Riscos</span>
        </h2>
        <p class="text-xs text-gray-500 mt-1">
          Acompanhamento estratégico dos riscos mapeados, severidade, Matriz de Riscos e planos de ação no HC-UFPE.
        </p>
      </div>

      <!-- Badge de Status do Filtro Atual -->
      <div v-if="unidadeSelecionada" class="flex items-center gap-2 bg-blue-50 border border-blue-200 px-3 py-1.5 rounded-lg text-xs">
        <span class="text-blue-700 font-medium">Filtrando por:</span>
        <span class="font-bold text-blue-900">
          {{ unidadeSelecionada.sigla ? `[${unidadeSelecionada.sigla}] ` : '' }}{{ unidadeSelecionada.nome }}
        </span>
        <button 
          @click="limparFiltro" 
          class="text-blue-600 hover:text-blue-800 font-bold ml-1 hover:bg-blue-100 rounded-full w-4 h-4 inline-flex items-center justify-center transition"
          title="Remover filtro de unidade"
        >
          ✕
        </button>
      </div>
    </div>

    <!-- Barra de Filtro de Unidade Organizacional (Pesquisa Textual e por Sigla) -->
    <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-200 space-y-3">
      <div class="flex flex-col sm:flex-row justify-between sm:items-center gap-2">
        <label class="text-xs font-bold text-gray-800 flex items-center gap-1.5">
          <span>🏢</span>
          <span>Filtrar por Unidade Organizacional</span>
        </label>
        <span class="text-[11px] text-gray-400">
          Pesquise por nome ou sigla da unidade para refinar os indicadores
        </span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-12 gap-3">
        <!-- Seletor Combobox Pesquisável de Unidades (Busca por Nome e Sigla) -->
        <div class="md:col-span-10 relative" ref="dropdownUnidadeRef">
          <!-- Gatilho do Seletor -->
          <div 
            @click="toggleDropdownUnidade" 
            class="w-full text-xs border border-gray-300 rounded-lg p-2.5 flex items-center justify-between bg-white cursor-pointer hover:border-blue-400 focus-within:ring-2 focus-within:ring-blue-500 transition shadow-2xs"
            :class="{ 'ring-2 ring-blue-500 border-blue-500': dropdownUnidadeAberto }"
          >
            <div class="flex items-center gap-2 truncate pr-2">
              <span class="text-gray-400 shrink-0">🏢</span>
              <template v-if="unidadeSelecionada">
                <span v-if="unidadeSelecionada.sigla" class="px-1.5 py-0.5 rounded bg-blue-100 text-blue-800 font-mono font-bold text-[11px] shrink-0">
                  [{{ unidadeSelecionada.sigla }}]
                </span>
                <span class="font-medium text-gray-900 truncate">
                  {{ unidadeSelecionada.nome }}
                </span>
              </template>
              <template v-else>
                <span class="text-gray-700 font-medium truncate">
                  Todas as Unidades (Visão Geral Autorizada)
                </span>
              </template>
            </div>

            <div class="flex items-center gap-1.5 shrink-0 text-gray-400">
              <button 
                v-if="unidadeSelecionadaId" 
                type="button"
                @click.stop="selecionarUnidadeFiltro(null)" 
                class="p-0.5 hover:text-red-500 text-gray-400 rounded transition"
                title="Limpar seleção de unidade"
              >
                ✕
              </button>
              <svg 
                class="w-4 h-4 transition-transform duration-200" 
                :class="{ 'rotate-180 text-blue-600': dropdownUnidadeAberto }"
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>

          <!-- Menu Dropdown Flutuante Pesquisável -->
          <div 
            v-if="dropdownUnidadeAberto" 
            class="absolute left-0 right-0 top-full mt-1.5 bg-white rounded-xl shadow-xl border border-gray-200 z-50 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-150"
          >
            <!-- Campo de Busca Embutido -->
            <div class="p-2.5 border-b border-gray-100 bg-gray-50/70">
              <div class="relative">
                <input 
                  ref="inputBuscaUnidadeRef"
                  v-model="filtroTextoUnidade" 
                  type="text" 
                  placeholder="Buscar por nome ou sigla (ex: GAS, SUP, SETISD, Farmácia)..." 
                  class="w-full text-xs border border-gray-300 rounded-lg p-2 pl-8 pr-7 focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
                  @click.stop
                />
                <svg class="w-4 h-4 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <button 
                  v-if="filtroTextoUnidade" 
                  type="button"
                  @click.stop="filtroTextoUnidade = ''" 
                  class="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-xs"
                  title="Limpar busca"
                >
                  ✕
                </button>
              </div>
            </div>

            <!-- Lista de Opções -->
            <div class="max-h-64 overflow-y-auto divide-y divide-gray-50 text-xs">
              <!-- Opção Geral -->
              <div 
                @click="selecionarUnidadeFiltro(null)" 
                class="p-2.5 flex items-center justify-between cursor-pointer transition hover:bg-blue-50/70"
                :class="!unidadeSelecionadaId ? 'bg-blue-50 text-blue-900 font-bold' : 'text-gray-700'"
              >
                <div class="flex items-center gap-2">
                  <span class="text-sm">🏢</span>
                  <span>Todas as Unidades (Visão Geral Autorizada)</span>
                </div>
                <span v-if="!unidadeSelecionadaId" class="text-blue-600 font-bold text-xs">✓</span>
              </div>

              <!-- Unidades Filtradas por Nome e Sigla -->
              <div 
                v-for="u in unidadesFiltradas" 
                :key="u.id" 
                @click="selecionarUnidadeFiltro(u)"
                class="p-2.5 flex items-center justify-between cursor-pointer transition hover:bg-blue-50/70"
                :class="unidadeSelecionadaId === u.id ? 'bg-blue-50 text-blue-900 font-bold' : 'text-gray-700'"
              >
                <div class="flex items-center gap-2 truncate pr-2">
                  <span v-if="u.sigla" class="px-1.5 py-0.5 rounded bg-gray-100 text-gray-800 font-mono font-bold text-[10px] shrink-0">
                    [{{ u.sigla }}]
                  </span>
                  <span class="truncate">{{ u.nome }}</span>
                </div>
                <span v-if="unidadeSelecionadaId === u.id" class="text-blue-600 font-bold text-xs shrink-0">✓</span>
              </div>

              <!-- Estado Vazio -->
              <div v-if="unidadesFiltradas.length === 0" class="p-4 text-center text-gray-400 text-xs italic">
                Nenhuma unidade encontrada para "{{ filtroTextoUnidade }}".
              </div>
            </div>
          </div>
        </div>

        <!-- Botão Limpar Filtro -->
        <div class="md:col-span-2 flex items-center">
          <button 
            @click="limparFiltro" 
            :disabled="!unidadeSelecionadaId && !filtroTextoUnidade"
            class="w-full py-2.5 px-3 text-xs font-semibold rounded-lg border transition text-center"
            :class="[
              unidadeSelecionadaId || filtroTextoUnidade
                ? 'bg-gray-100 text-gray-700 hover:bg-gray-200 border-gray-300 cursor-pointer'
                : 'bg-gray-50 text-gray-300 border-gray-200 cursor-not-allowed'
            ]"
          >
            Limpar Filtros
          </button>
        </div>
      </div>
    </div>

    <!-- Cards Estruturados por Gerência (SUP, GAS, GAD e GEP) - Exclusivo para Administradores ou Gestores com acesso total na matriz de visibilidade -->
    <div v-if="estatisticas.pode_ver_gerencias">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-xs font-bold text-gray-700 uppercase tracking-wider flex items-center gap-1.5">
          <span>🏛️</span>
          <span>Riscos Mapeados por Gerência (Status: Submetido)</span>
        </h3>
        <span class="text-[11px] text-gray-400">Clique no card para filtrar os dados por gerência</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div 
          v-for="ger in estatisticas.gerencias || []" 
          :key="ger.sigla"
          @click="toggleFiltroGerencia(ger)"
          class="bg-white p-4 rounded-xl shadow-sm border transition-all cursor-pointer relative group"
          :class="[
            unidadeSelecionadaId === ger.id 
              ? 'ring-2 ring-blue-600 border-blue-400 bg-blue-50/30 shadow-md' 
              : 'border-gray-200 hover:border-blue-300 hover:shadow-md hover:-translate-y-0.5'
          ]"
        >
          <!-- Cabeçalho do Card da Gerência: Sigla, Nome e Botão de Detalhes (i) -->
          <div class="flex items-center justify-between gap-2 mb-2.5">
            <div class="flex items-center gap-2 min-w-0">
              <span 
                class="px-2 py-0.5 rounded-md text-xs font-black tracking-wide font-mono shrink-0"
                :class="getGerenciaBadgeStyle(ger.sigla)"
              >
                {{ ger.sigla }}
              </span>
              <span class="text-xs font-bold text-gray-800 truncate" :title="ger.nome">
                {{ ger.nome }}
              </span>
            </div>

            <div class="flex items-center gap-1.5 shrink-0">
              <span v-if="unidadeSelecionadaId === ger.id" class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-blue-600 text-white">
                Ativo
              </span>
              <button
                type="button"
                @click.stop="abrirInfocardGerencia(ger)"
                class="w-5 h-5 rounded-full bg-gray-50 hover:bg-blue-50 text-gray-400 hover:text-blue-600 border border-gray-200 hover:border-blue-300 transition flex items-center justify-center cursor-pointer shadow-2xs"
                title="Ver relação de unidades subordinadas desta gerência"
              >
                <svg class="w-3.5 h-3.5 text-current group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Total Mapeados e Cobertura Integrados em uma única linha fluida -->
          <div class="flex items-baseline justify-between mb-3">
            <div>
              <span class="text-2xl font-black text-gray-900 tracking-tight">{{ ger.total || 0 }}</span>
              <span class="text-xs font-medium text-gray-400 ml-1.5">{{ (ger.total || 0) === 1 ? 'risco' : 'riscos' }}</span>
            </div>
            <div class="text-right text-xs">
              <span class="text-gray-500 font-medium">
                Cobertura: <strong class="text-gray-900">{{ ger.unidades_com_risco || 0 }}/{{ ger.total_unidades || 0 }}</strong>
              </span>
              <span class="text-[10px] text-blue-700 font-bold ml-1">({{ ger.percentual_mapeado || 0 }}%)</span>
            </div>
          </div>

          <!-- Distribuição por Severidade: Pílulas limpas sem bordas pesadas -->
          <div class="grid grid-cols-4 gap-1.5 pt-2.5 border-t border-gray-100 text-center">
            <div class="bg-emerald-50/70 rounded-lg py-1 px-0.5">
              <span class="text-[9px] font-semibold text-emerald-700 block">Baixo</span>
              <span class="text-xs font-black text-emerald-900 block">{{ ger.baixo || 0 }}</span>
            </div>
            <div class="bg-amber-50/70 rounded-lg py-1 px-0.5">
              <span class="text-[9px] font-semibold text-amber-700 block">Médio</span>
              <span class="text-xs font-black text-amber-900 block">{{ ger.medio || 0 }}</span>
            </div>
            <div class="bg-orange-50/70 rounded-lg py-1 px-0.5">
              <span class="text-[9px] font-semibold text-orange-700 block">Alto</span>
              <span class="text-xs font-black text-orange-900 block">{{ ger.alto || 0 }}</span>
            </div>
            <div class="bg-rose-50/70 rounded-lg py-1 px-0.5">
              <span class="text-[9px] font-semibold text-rose-700 block">Extremo</span>
              <span class="text-xs font-black text-rose-900 block">{{ ger.extremo || 0 }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Mapa de Calor e Diretrizes de Governança -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2">
        <MapaCalorRiscos :counts="estatisticas.quadrantes" />
      </div>

      <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-200 space-y-4 flex flex-col justify-between">
        <div>
          <h3 class="text-sm font-bold text-gray-800 flex items-center gap-1.5">
            <span>🛡️</span>
            <span>Diretrizes de Governança</span>
          </h3>
          <p class="text-xs text-gray-500 mt-1 leading-relaxed">
            O Mapa de Calor reflete a distribuição e densidade dos riscos mapeados com status <strong>SUBMETIDO</strong> no HC-UFPE.
          </p>

          <div class="mt-4 p-3.5 bg-blue-50/70 rounded-xl border border-blue-100 text-xs space-y-2">
            <span class="font-bold text-blue-900 block">Tolerância Institucional</span>
            <p class="text-[11px] text-blue-800 leading-relaxed">
              Riscos com resultado residual <strong>superior a 7,99</strong> (Alto ou Extremo) excedem o apetite institucional e exigem obrigatoriamente a elaboração de Planos de Ação e Planos de Contingência.
            </p>
          </div>

          <div class="mt-3 p-3 bg-gray-50 rounded-xl border border-gray-200 text-xs text-gray-600 space-y-1">
            <span class="font-bold text-gray-700 block text-[11px]">Controle de Acesso</span>
            <p class="text-[11px] text-gray-500 leading-relaxed">
              Os dados exibidos respeitam as permissões do seu setor, divisões/unidades vinculadas e eventuais acessos concedidos na matriz de visibilidade institucional.
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal / Infocard Detalhado de Unidades da Gerência -->
    <div 
      v-if="gerenciaInfocardModal" 
      class="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4"
      @click.self="gerenciaInfocardModal = null"
    >
      <div class="bg-white rounded-2xl shadow-2xl border border-gray-200 max-w-lg w-full max-h-[85vh] flex flex-col overflow-hidden">
        <!-- Cabeçalho do Infocard -->
        <div class="p-5 border-b border-gray-100 flex items-start justify-between bg-slate-50">
          <div>
            <div class="flex items-center gap-2">
              <span 
                class="px-2 py-0.5 rounded text-xs font-black font-mono"
                :class="getGerenciaBadgeStyle(gerenciaInfocardModal.sigla)"
              >
                {{ gerenciaInfocardModal.sigla }}
              </span>
              <h3 class="text-sm font-bold text-gray-900">
                {{ gerenciaInfocardModal.nome }}
              </h3>
            </div>
            <p class="text-xs text-gray-500 mt-1">
              Relação de unidades subordinadas vinculadas e seus respectivos riscos mapeados.
            </p>
          </div>
          <button 
            type="button" 
            @click="gerenciaInfocardModal = null"
            class="text-gray-400 hover:text-gray-700 font-bold p-1 rounded-lg hover:bg-gray-200 transition"
          >
            ✕
          </button>
        </div>

        <!-- Explicação da Métrica -->
        <div class="p-4 bg-blue-50/70 border-b border-blue-100 text-xs text-blue-900 flex items-start gap-2.5">
          <span class="text-base mt-0.5">ℹ️</span>
          <div class="leading-relaxed">
            <strong class="font-bold">Critério do Indicador:</strong> 
            Considera unidades subordinadas que possuem <strong>ao menos um risco mapeado com status Submetido</strong> (desconsiderando a própria gerência).
            <div class="mt-1 font-semibold text-blue-950">
              Cobertura: {{ gerenciaInfocardModal.unidades_com_risco }} de {{ gerenciaInfocardModal.total_unidades }} unidades subordinadas ({{ gerenciaInfocardModal.percentual_mapeado }}%).
            </div>
          </div>
        </div>

        <!-- Lista de Unidades com Destaque para quem possui risco mapeado -->
        <div class="p-4 overflow-y-auto space-y-2 flex-1 divide-y divide-gray-100">
          <div 
            v-for="u in (gerenciaInfocardModal.unidades_detalhes || []).filter((item: any) => item.id !== gerenciaInfocardModal.id)" 
            :key="u.id"
            class="pt-2 first:pt-0 flex items-center justify-between text-xs p-2.5 rounded-xl transition-all"
            :class="u.total_riscos > 0 ? 'bg-emerald-50/80 border border-emerald-200 shadow-2xs' : 'bg-gray-50/40 border border-gray-100 text-gray-600'"
          >
            <div class="min-w-0 pr-3">
              <div class="flex items-center gap-2">
                <span 
                  v-if="u.sigla" 
                  class="font-mono font-bold text-[10px] px-1.5 py-0.5 rounded"
                  :class="u.total_riscos > 0 ? 'bg-emerald-200 text-emerald-950 border border-emerald-300' : 'bg-gray-200 text-gray-700'"
                >
                  {{ u.sigla }}
                </span>
                <span class="font-medium truncate" :class="u.total_riscos > 0 ? 'text-emerald-950 font-bold' : 'text-gray-700'">
                  {{ u.nome }}
                </span>
              </div>
            </div>

            <!-- Badge de Total de Riscos -->
            <div class="shrink-0 flex items-center gap-1.5">
              <span 
                class="px-2.5 py-1 rounded-full text-xs font-black shadow-2xs flex items-center gap-1"
                :class="u.total_riscos > 0 ? 'bg-emerald-600 text-white' : 'bg-gray-200 text-gray-500 font-semibold'"
              >
                <span v-if="u.total_riscos > 0">✓</span>
                <span>{{ u.total_riscos }} {{ u.total_riscos === 1 ? 'risco' : 'riscos' }}</span>
              </span>
            </div>
          </div>
        </div>

        <!-- Rodapé do Modal -->
        <div class="p-3 border-t border-gray-200 bg-gray-50 text-right">
          <button 
            type="button" 
            @click="gerenciaInfocardModal = null" 
            class="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 text-xs font-bold rounded-lg transition"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import api from '../../services/api';
import MapaCalorRiscos from '../../components/riscos/MapaCalorRiscos.vue';

const estatisticas = ref<any>({ quadrantes: {}, totais: {}, gerencias: [], pode_ver_gerencias: false });
const unidades = ref<any[]>([]);
const filtroTextoUnidade = ref('');
const unidadeSelecionadaId = ref<number | null>(null);
const carregando = ref(false);
const gerenciaInfocardModal = ref<any>(null);

// Combobox Dropdown Pesquisável
const dropdownUnidadeAberto = ref(false);
const dropdownUnidadeRef = ref<HTMLElement | null>(null);
const inputBuscaUnidadeRef = ref<HTMLInputElement | null>(null);

function abrirInfocardGerencia(ger: any) {
  gerenciaInfocardModal.value = ger;
}

function normalizarTexto(txt: string) {
  return (txt || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();
}

const unidadesFiltradas = computed(() => {
  const q = normalizarTexto(filtroTextoUnidade.value.trim());
  if (!q) return unidades.value;
  return unidades.value.filter((u: any) => {
    const nome = normalizarTexto(u.nome || '');
    const sigla = normalizarTexto(u.sigla || '');
    return nome.includes(q) || sigla.includes(q);
  });
});

const unidadeSelecionada = computed(() => {
  if (!unidadeSelecionadaId.value) return null;
  return unidades.value.find((u: any) => u.id === unidadeSelecionadaId.value) || null;
});

async function toggleDropdownUnidade() {
  dropdownUnidadeAberto.value = !dropdownUnidadeAberto.value;
  if (dropdownUnidadeAberto.value) {
    await nextTick();
    if (inputBuscaUnidadeRef.value) {
      inputBuscaUnidadeRef.value.focus();
    }
  }
}

async function selecionarUnidadeFiltro(u: any) {
  unidadeSelecionadaId.value = u ? u.id : null;
  dropdownUnidadeAberto.value = false;
  filtroTextoUnidade.value = '';
  await carregarEstatisticas();
}

function handleClickOutside(event: MouseEvent) {
  if (dropdownUnidadeRef.value && !dropdownUnidadeRef.value.contains(event.target as Node)) {
    dropdownUnidadeAberto.value = false;
  }
}

function getGerenciaBadgeStyle(sigla: string) {
  switch (sigla) {
    case 'SUP': return 'bg-indigo-100 text-indigo-800 border border-indigo-200';
    case 'GAS': return 'bg-teal-100 text-teal-800 border border-teal-200';
    case 'GAD': return 'bg-blue-100 text-blue-800 border border-blue-200';
    case 'GEP': return 'bg-purple-100 text-purple-800 border border-purple-200';
    default: return 'bg-gray-100 text-gray-800 border border-gray-200';
  }
}

async function carregarEstatisticas() {
  carregando.value = true;
  try {
    const params: any = {};
    if (unidadeSelecionadaId.value) {
      params.unidade_id = unidadeSelecionadaId.value;
    }
    const res = await api.get('/api/riscos/painel/matriz', { params });
    estatisticas.value = res.data;
  } catch (err) {
    console.error('Erro ao carregar estatísticas:', err);
  } finally {
    carregando.value = false;
  }
}

async function carregarUnidades() {
  try {
    const res = await api.get('/api/unidades', { params: { apenas_autorizadas: true } });
    unidades.value = res.data;
  } catch (err) {
    console.error('Erro ao carregar lista de unidades:', err);
  }
}

async function toggleFiltroGerencia(ger: any) {
  if (!ger.id) return;
  if (unidadeSelecionadaId.value === ger.id) {
    unidadeSelecionadaId.value = null;
  } else {
    unidadeSelecionadaId.value = ger.id;
  }
  await carregarEstatisticas();
}

async function limparFiltro() {
  unidadeSelecionadaId.value = null;
  filtroTextoUnidade.value = '';
  dropdownUnidadeAberto.value = false;
  await carregarEstatisticas();
}

onMounted(async () => {
  document.addEventListener('click', handleClickOutside);
  await Promise.all([
    carregarEstatisticas(),
    carregarUnidades()
  ]);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>
