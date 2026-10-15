<template>
  <div>
    <!-- Conteúdo Visual da Tela (Oculto estritamente durante a impressão da Ficha) -->
    <div class="space-y-6 print:hidden">
      <!-- Header com Título e Ação Principal -->
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-xl shadow-sm border border-gray-200">
      <div>
        <h2 class="text-xl font-bold text-gray-900 flex items-center gap-2">
          <span>📋</span>
          <span>Fichas de Riscos Mapeados</span>
        </h2>
        <p class="text-xs text-gray-500 mt-1">
          Consulte, filtre e gerencie as fichas de riscos institucionais homologadas e em tramitação.
        </p>
      </div>
      <div class="flex items-center gap-2">
        <router-link 
          to="/riscos/novo" 
          class="inline-flex items-center px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg shadow-sm transition space-x-2"
        >
          <span>+ Novo Mapeamento</span>
        </router-link>
      </div>
    </div>

    <!-- Barra de Filtros: Unidade (com busca textual), Status e Termo Geral -->
    <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-200 space-y-4">
      <div class="flex items-center justify-between border-b pb-3">
        <div class="flex items-center gap-2">
          <span class="text-sm font-bold text-gray-800">Filtros de Pesquisa</span>
          <span class="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full font-semibold">
            {{ mapeamentosFiltrados.length }} ficha(s) encontrada(s)
          </span>
        </div>
        <button 
          @click="limparFiltros" 
          type="button"
          class="text-xs font-semibold text-blue-600 hover:text-blue-800 transition"
        >
          Limpar Filtros
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- 1. Filtro de Unidade com Busca Textual / Combobox -->
        <div>
          <label class="block text-xs font-semibold text-gray-700 mb-1">
            Unidade Organizacional (Busca Textual)
          </label>
          <div class="relative">
            <input 
              v-model="filtroTextoUnidade" 
              type="text" 
              placeholder="Digite o nome ou sigla da unidade..." 
              class="w-full text-xs border border-gray-300 rounded-lg p-2.5 pl-8 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
            <svg class="w-4 h-4 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <button 
              v-if="filtroTextoUnidade" 
              @click="filtroTextoUnidade = ''" 
              class="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-xs"
            >
              ✕
            </button>
          </div>
        </div>

        <!-- 2. Filtro de Status de Tramitação -->
        <div>
          <label class="block text-xs font-semibold text-gray-700 mb-1">
            Status da Tramitação
          </label>
          <select 
            v-model="filtroStatus" 
            @change="carregarMapeamentos" 
            class="w-full text-xs border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 bg-white"
          >
            <option :value="null">Todos os Status</option>
            <option value="RASCUNHO">Rascunho</option>
            <option value="SUBMETIDO">Submetido para UGERC</option>
          </select>
        </div>

        <!-- 3. Busca Geral por Processo ou Evento -->
        <div>
          <label class="block text-xs font-semibold text-gray-700 mb-1">
            Buscar por Processo / Evento
          </label>
          <div class="relative">
            <input 
              v-model="filtroTextoGeral" 
              type="text" 
              placeholder="Pesquisar por processo, risco ou projeto..." 
              class="w-full text-xs border border-gray-300 rounded-lg p-2.5 pl-8 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
            <svg class="w-4 h-4 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 100-6 3 3 0 000 6z" />
            </svg>
            <button 
              v-if="filtroTextoGeral" 
              @click="filtroTextoGeral = ''" 
              class="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-xs"
            >
              ✕
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Tabela de Fichas de Riscos Mapeados -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-gray-50/70">
        <div>
          <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
            <span>📋</span>
            <span>Fichas Cadastradas</span>
            <span class="text-xs font-normal text-gray-500">
              ({{ mapeamentosFiltrados.length }} exibida{{ mapeamentosFiltrados.length === 1 ? '' : 's' }})
            </span>
          </h3>
          <p class="text-[11px] text-gray-500 mt-0.5">
            Permissões ativas: Administradores possuem acesso pleno; Gestores gerenciam apenas fichas do seu setor principal; Chefias superiores possuem permissão de visualização.
          </p>
        </div>

        <!-- Indicador e Botões de Ação em Lote no Cabeçalho do Card -->
        <div v-if="selecionadosIds.length > 0" class="flex items-center gap-2 bg-blue-50/80 border border-blue-200 px-3.5 py-1.5 rounded-lg text-xs animate-fade-in shrink-0 flex-wrap">
          <span class="font-bold text-blue-900 flex items-center gap-1.5">
            <span class="w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-[10px] font-black">
              {{ selecionadosIds.length }}
            </span>
            <span>selecionada(s)</span>
          </span>

          <!-- Botão Imprimir em Lote -->
          <button
            @click="imprimirEmLote"
            :disabled="imprimindoLote"
            type="button"
            class="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded shadow-xs transition flex items-center gap-1 cursor-pointer disabled:opacity-50"
            title="Imprimir fichas selecionadas em formato A4"
          >
            <span v-if="!imprimindoLote">🖨️ Imprimir Selecionadas ({{ selecionadosIds.length }})</span>
            <span v-else class="inline-flex items-center gap-1">
              <span class="animate-spin">⏳</span> Gerando impressão...
            </span>
          </button>

          <!-- Botão Excluir em Lote -->
          <button
            v-if="selecionadosExcluiveis.length > 0"
            @click="confirmarExclusaoLote"
            :disabled="excluindoLote"
            type="button"
            class="px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white font-bold rounded shadow-xs transition flex items-center gap-1 cursor-pointer disabled:opacity-50"
            :title="'Excluir as ' + selecionadosExcluiveis.length + ' fichas com permissão'"
          >
            <span v-if="!excluindoLote">🗑️ Excluir ({{ selecionadosExcluiveis.length }})</span>
            <span v-else class="inline-flex items-center gap-1">
              <span class="animate-spin">⏳</span> Excluindo...
            </span>
          </button>

          <button
            @click="desmarcarTodos"
            type="button"
            class="text-gray-600 hover:text-gray-900 font-semibold underline text-[11px] cursor-pointer ml-1"
          >
            Desmarcar
          </button>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200 text-left text-xs">
          <thead class="bg-gray-100/80 text-gray-700 font-semibold uppercase tracking-wider text-[11px]">
            <tr>
              <th class="py-3 px-3 text-center w-10">
                <input
                  type="checkbox"
                  :checked="todosSelecionados"
                  :indeterminate.prop="algunsSelecionados"
                  :disabled="mapeamentosFiltrados.length === 0"
                  @change="alternarSelecionarTodos"
                  class="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                  title="Selecionar / Desmarcar todas as fichas visíveis"
                />
              </th>
              <th class="py-3 px-4">Setor / Unidade</th>
              <th class="py-3 px-4">Processo</th>
              <th class="py-3 px-4">Evento de Risco</th>
              <th class="py-3 px-4 text-center">Residual</th>
              <th class="py-3 px-4 text-center">Severidade</th>
              <th class="py-3 px-4 text-center">Status</th>
              <th class="py-3 px-4 text-center">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-if="carregando">
              <td colspan="8" class="py-12 text-center text-gray-400">
                <span class="inline-block animate-spin mr-2">⏳</span> Carregando fichas de riscos...
              </td>
            </tr>
            <tr v-else-if="mapeamentosFiltrados.length === 0">
              <td colspan="8" class="py-12 text-center text-gray-400">
                <div class="text-3xl mb-2">🔍</div>
                <p class="text-sm font-semibold text-gray-600">Nenhum mapeamento de risco encontrado.</p>
                <p class="text-xs text-gray-400 mt-1">Tente ajustar os filtros acima ou registre um novo mapeamento.</p>
              </td>
            </tr>
            <tr 
              v-for="m in mapeamentosFiltrados" 
              :key="m.id" 
              class="transition"
              :class="selecionadosIds.includes(m.id) ? 'bg-blue-50/70' : 'hover:bg-blue-50/40'"
            >
              <!-- Checkbox de Seleção Individual -->
              <td class="py-3.5 px-3 text-center w-10">
                <input
                  type="checkbox"
                  :value="m.id"
                  v-model="selecionadosIds"
                  class="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500 cursor-pointer"
                  :title="'Selecionar ficha #' + m.id + (m.pode_excluir ? '' : ' (somente leitura para exclusão)')"
                />
              </td>

              <!-- Setor / Unidade -->
              <td class="py-3.5 px-4 font-medium text-gray-900 max-w-xs">
                <div class="font-bold text-gray-900">
                  <span>{{ m.unidade?.nome }}</span>
                </div>
                <div class="flex items-center gap-1.5 mt-1 flex-wrap">
                  <span class="text-[10px] text-gray-400 font-mono">Ficha #{{ m.id }}</span>
                  <span v-if="m.tag_versao" class="text-[10px] font-bold px-1.5 py-0.5 rounded border bg-purple-50 text-purple-700 border-purple-200">
                    {{ m.tag_versao }}
                  </span>
                </div>
                <div v-if="m.criado_por || m.submetido_em" class="text-[10px] text-gray-500 mt-1 leading-tight">
                  <span v-if="m.criado_por" class="block">Criado por: {{ m.criado_por.nome || m.criado_por.username }}</span>
                  <span v-if="m.submetido_em" class="text-blue-700 font-medium block">
                    Submetido em: {{ new Date(m.submetido_em).toLocaleDateString('pt-BR') }}
                  </span>
                </div>
              </td>

              <!-- Processo e Projeto -->
              <td class="py-3.5 px-4 text-gray-600 max-w-xs">
                <span class="font-medium text-gray-800 block truncate" :title="m.processo_outro || m.processo?.nome">
                  {{ m.processo_outro ? ('[Outro] ' + m.processo_outro) : (m.processo?.nome || '-') }}
                </span>
                <span v-if="m.possui_projeto && m.nome_projeto" class="text-[10px] text-blue-600 font-semibold block truncate">
                  🚀 Projeto: {{ m.nome_projeto }}
                </span>
                <span class="text-[10px] text-gray-400 block truncate">
                  {{ m.processo?.macroprocesso || 'Geral' }}
                </span>
              </td>

              <!-- Evento de Risco -->
              <td class="py-3.5 px-4 text-gray-700 max-w-md">
                <div v-if="m.eventos && m.eventos.length > 0">
                  <p class="line-clamp-2 leading-relaxed" :title="m.eventos[0].descricao_evento">
                    {{ m.eventos[0].descricao_evento }}
                  </p>
                  <span class="text-[10px] text-gray-400 mt-0.5 inline-block font-medium">
                    Categoria: {{ m.eventos[0].categoria }}
                  </span>
                </div>
                <span v-else class="text-gray-400 italic">Sem eventos cadastrados</span>
              </td>

              <!-- Risco Residual -->
              <td class="py-3.5 px-4 text-center font-black text-gray-900 text-sm">
                {{ m.eventos && m.eventos[0]?.avaliacao ? m.eventos[0].avaliacao.risco_residual : '-' }}
              </td>

              <!-- Severidade -->
              <td class="py-3.5 px-4 text-center">
                <span 
                  v-if="m.eventos && m.eventos[0]?.avaliacao"
                  :class="getClassificacaoBadge(m.eventos[0].avaliacao.classificacao)"
                  class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase inline-block border"
                >
                  {{ m.eventos[0].avaliacao.classificacao }}
                </span>
                <span v-else class="text-gray-400">-</span>
              </td>

              <!-- Status -->
              <td class="py-3.5 px-4 text-center">
                <span 
                  :class="getStatusBadge(m.status)"
                  class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase inline-block border shadow-xs"
                >
                  {{ m.status }}
                </span>
              </td>

              <!-- Ações -->
              <td class="py-3.5 px-4 text-center whitespace-nowrap">
                <!-- Se pode editar: link de Edição -->
                <router-link 
                  v-if="m.pode_editar"
                  :to="'/riscos/' + m.id + '/editar'"
                  class="inline-flex items-center text-blue-600 hover:text-blue-800 font-bold text-xs px-2.5 py-1 rounded hover:bg-blue-50 transition"
                  title="Editar ficha de risco"
                >
                  Editar
                </router-link>

                <!-- Se não pode editar: link de Visualização (somente leitura) -->
                <router-link 
                  v-else
                  :to="'/riscos/' + m.id + '/editar'"
                  class="inline-flex items-center text-gray-600 hover:text-gray-800 font-medium text-xs px-2.5 py-1 rounded hover:bg-gray-100 transition"
                  title="Visualizar ficha de risco (somente leitura)"
                >
                  Visualizar
                </router-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Barra Flutuante de Ações em Lote Fixa na Base da Tela (visível quando há seleção) -->
    <div 
      v-if="selecionadosIds.length > 0"
      class="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 bg-gray-900/95 backdrop-blur text-white px-5 py-3 rounded-2xl shadow-2xl border border-gray-700 flex items-center gap-4 animate-fade-in flex-wrap justify-center"
    >
      <div class="flex items-center gap-2">
        <span class="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-black shadow-xs">
          {{ selecionadosIds.length }}
        </span>
        <span class="text-xs font-semibold whitespace-nowrap">
          {{ selecionadosIds.length === 1 ? '1 ficha selecionada' : `${selecionadosIds.length} fichas selecionadas` }}
        </span>
      </div>

      <div class="h-4 w-px bg-gray-700 hidden sm:block"></div>

      <div class="flex items-center gap-2">
        <!-- Botão Imprimir em Lote -->
        <button
          @click="imprimirEmLote"
          :disabled="imprimindoLote"
          type="button"
          class="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl shadow-md transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          title="Imprimir fichas selecionadas em formato A4"
        >
          <span v-if="!imprimindoLote">🖨️ Imprimir Selecionadas ({{ selecionadosIds.length }})</span>
          <span v-else class="inline-flex items-center gap-1">
            <span class="animate-spin">⏳</span> Gerando impressão...
          </span>
        </button>

        <!-- Botão Excluir em Lote -->
        <button
          v-if="selecionadosExcluiveis.length > 0"
          @click="confirmarExclusaoLote"
          :disabled="excluindoLote"
          type="button"
          class="px-4 py-1.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-xl shadow-md transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          :title="'Excluir as ' + selecionadosExcluiveis.length + ' fichas com permissão'"
        >
          <span v-if="!excluindoLote">🗑️ Excluir ({{ selecionadosExcluiveis.length }})</span>
          <span v-else class="inline-flex items-center gap-1">
            <span class="animate-spin">⏳</span> Excluindo...
          </span>
        </button>

        <button
          @click="desmarcarTodos"
          type="button"
          class="px-2.5 py-1.5 text-xs text-gray-300 hover:text-white transition cursor-pointer"
        >
          Desmarcar
        </button>
      </div>
    </div>
  </div>

  <!-- Componente de Impressão A4 Oculto em tela e Ativo no Print -->
  <FichaImpressaoA4 :fichas="fichasParaImpressaoLote" />
</div>

</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue';
import api from '../../services/api';
import FichaImpressaoA4 from '../../components/riscos/FichaImpressaoA4.vue';

const mapeamentos = ref<any[]>([]);
const carregando = ref(false);
const fichasParaImpressaoLote = ref<any[]>([]);
const imprimindoLote = ref(false);

const selecionadosIds = ref<number[]>([]);
const excluindoLote = ref(false);

const filtroTextoUnidade = ref('');
const filtroStatus = ref<string | null>(null);
const filtroTextoGeral = ref('');

function normalizarTexto(txt: string) {
  return (txt || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();
}

const mapeamentosFiltrados = computed(() => {
  let lista = mapeamentos.value;

  // Filtro de Unidade por texto (nome ou sigla)
  const qUnidade = normalizarTexto(filtroTextoUnidade.value.trim());
  if (qUnidade) {
    lista = lista.filter((m: any) => {
      const nomeU = normalizarTexto(m.unidade?.nome || '');
      const siglaU = normalizarTexto(m.unidade?.sigla || '');
      return nomeU.includes(qUnidade) || siglaU.includes(qUnidade);
    });
  }

  // Filtro de Termo Geral (processo, evento, projeto)
  const qGeral = normalizarTexto(filtroTextoGeral.value.trim());
  if (qGeral) {
    lista = lista.filter((m: any) => {
      const proc = normalizarTexto(m.processo?.nome || m.processo_outro || '');
      const proj = normalizarTexto(m.nome_projeto || '');
      const evDesc = normalizarTexto(m.eventos?.[0]?.descricao_evento || '');
      const nomeU = normalizarTexto(m.unidade?.nome || '');
      const siglaU = normalizarTexto(m.unidade?.sigla || '');
      return proc.includes(qGeral) || proj.includes(qGeral) || evDesc.includes(qGeral) || nomeU.includes(qGeral) || siglaU.includes(qGeral);
    });
  }

  return lista;
});

const selecionadosExcluiveis = computed(() => {
  const permitidosIds = new Set(mapeamentos.value.filter(m => m.pode_excluir).map(m => m.id));
  return selecionadosIds.value.filter(id => permitidosIds.has(id));
});

const todosSelecionados = computed(() => {
  const visiveis = mapeamentosFiltrados.value;
  return visiveis.length > 0 && visiveis.every((m: any) => selecionadosIds.value.includes(m.id));
});

const algunsSelecionados = computed(() => {
  const visiveis = mapeamentosFiltrados.value;
  const marcados = visiveis.filter((m: any) => selecionadosIds.value.includes(m.id)).length;
  return marcados > 0 && marcados < visiveis.length;
});

function alternarSelecionarTodos() {
  if (todosSelecionados.value) {
    selecionadosIds.value = [];
  } else {
    selecionadosIds.value = mapeamentosFiltrados.value.map((m: any) => m.id);
  }
}

function desmarcarTodos() {
  selecionadosIds.value = [];
}

function getClassificacaoBadge(classif: string) {
  switch (classif) {
    case 'BAIXO': return 'bg-emerald-50 text-emerald-800 border-emerald-200';
    case 'MEDIO': return 'bg-amber-50 text-amber-800 border-amber-200';
    case 'ALTO': return 'bg-orange-50 text-orange-800 border-orange-200';
    default: return 'bg-rose-50 text-rose-800 border-rose-200';
  }
}

function getStatusBadge(st: string) {
  switch (st) {
    case 'RASCUNHO': return 'bg-amber-50 text-amber-800 border-amber-200';
    case 'SUBMETIDO': return 'bg-blue-50 text-blue-800 border-blue-200';
    case 'HOMOLOGADO': return 'bg-emerald-50 text-emerald-800 border-emerald-200';
    default: return 'bg-purple-50 text-purple-800 border-purple-200';
  }
}

async function carregarMapeamentos() {
  carregando.value = true;
  selecionadosIds.value = [];
  try {
    const params: any = {};
    if (filtroStatus.value) params.status = filtroStatus.value;
    const res = await api.get('/api/riscos', { params });
    mapeamentos.value = res.data;
  } catch (err) {
    console.error('Erro ao carregar mapeamentos:', err);
  } finally {
    carregando.value = false;
  }
}

async function imprimirEmLote() {
  if (selecionadosIds.value.length === 0) return;
  try {
    imprimindoLote.value = true;
    const res = await api.post('/api/riscos/detalhes-lote', { ids: selecionadosIds.value });
    fichasParaImpressaoLote.value = res.data;
    await nextTick();
    setTimeout(() => {
      window.print();
      imprimindoLote.value = false;
    }, 200);
  } catch (err: any) {
    console.error('Erro ao obter fichas em lote para impressão:', err);
    alert(err.response?.data?.detail || 'Erro ao carregar dados das fichas em lote para impressão.');
    imprimindoLote.value = false;
  }
}

async function confirmarExclusaoLote() {
  const idsParaExcluir = selecionadosExcluiveis.value;
  const qtd = idsParaExcluir.length;
  if (qtd === 0) {
    alert('Nenhuma das fichas selecionadas possui permissão para exclusão pelo seu usuário.');
    return;
  }

  const confirmou = confirm(
    `ATENÇÃO: Você está prestes a excluir permanentemente ${qtd} ficha(s) de risco selecionada(s).\n\nTodos os eventos de risco, avaliações da Matriz de Riscos, controles internos e planos associados serão removidos do sistema.\n\nDeseja realmente continuar? Esta ação NÃO pode ser desfeita.`
  );
  if (!confirmou) return;

  try {
    excluindoLote.value = true;
    const res = await api.post('/api/riscos/excluir-lote', { ids: idsParaExcluir });
    alert(res.data.message || `${qtd} ficha(s) de risco excluída(s) com sucesso.`);
    selecionadosIds.value = [];
    await carregarMapeamentos();
  } catch (err: any) {
    console.error('Erro ao excluir fichas em lote:', err);
    alert(err.response?.data?.detail || 'Erro ao excluir fichas selecionadas em lote.');
  } finally {
    excluindoLote.value = false;
  }
}

function limparFiltros() {
  selecionadosIds.value = [];
  filtroTextoUnidade.value = '';
  filtroStatus.value = null;
  filtroTextoGeral.value = '';
  carregarMapeamentos();
}

onMounted(async () => {
  await carregarMapeamentos();
});
</script>
