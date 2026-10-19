<template>
  <div>
    <!-- Conteúdo da Interface na Tela (Oculto na Impressão) -->
    <div class="max-w-6xl mx-auto space-y-6 pb-12 print:hidden">
      <!-- Header do Formulário -->
      <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-xl font-bold text-gray-900">Mapeamento de Riscos por Processo</h2>
              <span 
                v-if="form.tag_versao" 
                class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-200"
              >
                {{ form.tag_versao }}
              </span>
            </div>
            <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500 mt-1.5">
              <template v-if="form.criado_por">
                <span class="text-gray-600">
                  Criado por: <strong class="text-gray-800">{{ form.criado_por.nome || form.criado_por.username }}</strong>
                  <span v-if="form.criado_em"> em {{ formatarDataHora(form.criado_em) }}</span>
                </span>
              </template>
              <template v-if="form.submetido_em">
                <span v-if="form.criado_por" class="text-gray-300">•</span>
                <span class="text-blue-700 font-semibold">
                  Submetido em: {{ formatarDataHora(form.submetido_em) }}
                </span>
              </template>
            </div>
          </div>
          <div class="flex items-center space-x-2.5 shrink-0 flex-wrap gap-y-2">
            <span 
              :class="form.status === 'RASCUNHO' ? 'bg-amber-100 text-amber-800' : 'bg-blue-100 text-blue-800'"
              class="px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider"
            >
              {{ form.status }}
            </span>
            <template v-if="podeEditarFicha">
              <button 
                @click="salvar(false)" 
                :disabled="salvando || !podeSalvarRascunho"
                :class="podeSalvarRascunho ? 'bg-gray-100 hover:bg-gray-200 text-gray-800 cursor-pointer shadow-xs border border-gray-300' : 'bg-gray-100 text-gray-400 cursor-not-allowed opacity-60 border border-gray-200'"
                class="px-3.5 py-2 text-xs sm:text-sm font-medium rounded-lg transition flex items-center gap-1.5"
                :title="tooltipSalvarRascunho"
              >
                <span>💾</span>
                <span>Salvar Rascunho</span>
              </button>
              <button 
                @click="salvar(true)" 
                :disabled="salvando || !podeSubmeterBotao"
                :class="podeSubmeterBotao ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm cursor-pointer' : 'bg-gray-200 text-gray-400 cursor-not-allowed border border-gray-300'"
                class="px-4 py-2 text-xs sm:text-sm font-medium rounded-lg transition flex items-center gap-1.5"
                :title="tooltipSubmeter"
              >
                <span v-if="podeSubmeterBotao">🚀</span>
                <span>Submeter para UGERC</span>
              </button>
            </template>
            <span v-else class="px-3 py-1.5 bg-gray-100 text-gray-600 text-xs font-semibold rounded-lg border border-gray-200 flex items-center gap-1">
              <span>🔒</span> Somente Leitura
            </span>

            <!-- Botão Imprimir posicionado ao lado do Submeter -->
            <button 
              type="button" 
              @click="imprimirFichaCompleta"
              :disabled="!podeSubmeter"
              :class="podeSubmeter ? 'bg-emerald-600 hover:bg-emerald-700 text-white cursor-pointer shadow-sm' : 'bg-gray-200 text-gray-400 cursor-not-allowed border border-gray-300'"
              class="px-4 py-2 text-xs sm:text-sm font-medium rounded-lg transition flex items-center gap-1.5"
              :title="!podeSubmeter ? ('Para habilitar a impressão em PDF, conclua todas as etapas obrigatórias: ' + textoPendencias) : 'Imprimir'"
            >
              <span>🖨️</span>
              <span>Imprimir</span>
            </button>
          </div>
        </div>

        <!-- Banner de Somente Leitura -->
        <div v-if="!podeEditarFicha" class="mt-4 p-3 bg-amber-50 border border-amber-200 text-amber-900 rounded-lg text-xs flex items-center gap-2">
          <span class="text-base">ℹ️</span>
          <span><strong>Modo de Visualização:</strong> Instâncias superiores vinculadas no organograma ou usuários com acesso via matriz de visibilidade podem apenas consultar este mapeamento. Fichas só podem ser editadas pelo gestor da própria unidade ou Administrador.</span>
        </div>
      </div>

      <!-- Feedback de Rascunho Salvo -->
      <div 
        v-if="feedbackMensagem" 
        class="bg-emerald-50 border border-emerald-300 text-emerald-900 px-4 py-3 rounded-xl flex items-center justify-between text-xs font-medium shadow-sm transition-all"
      >
        <div class="flex items-center gap-2">
          <span class="text-base">💾</span>
          <span>{{ feedbackMensagem }}</span>
        </div>
        <button type="button" @click="feedbackMensagem = null" class="text-emerald-700 hover:text-emerald-950 font-bold ml-4">✕</button>
      </div>

      <!-- Stepper de Navegação (5 Etapas) -->
      <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
        <div class="grid grid-cols-5 gap-2">
          <button 
            v-for="etapa in etapas" 
            :key="etapa.id"
            @click="irParaEtapa(etapa.id)"
            :class="[
              etapaAtual === etapa.id ? 'border-blue-600 text-blue-700 bg-blue-50/50' : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50',
              'border-b-2 py-3 px-2 text-center text-xs font-medium transition rounded-t-lg flex flex-col items-center relative'
            ]"
          >
          <div class="relative mb-1">
            <span class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition"
                  :class="etapaAtual === etapa.id ? 'bg-blue-600 text-white' : (statusEtapas[etapa.id] ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-200 text-gray-700')">
              {{ etapa.id }}
            </span>
            <span v-if="statusEtapas[etapa.id]" class="absolute -top-1 -right-1.5 w-3.5 h-3.5 bg-emerald-600 text-white text-[9px] font-extrabold rounded-full flex items-center justify-center shadow">
              ✓
            </span>
          </div>
          <span class="truncate w-full">{{ etapa.nome }}</span>
        </button>
      </div>
    </div>

    <!-- Conteúdo da Etapa Atual -->
    <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
      
      <!-- ETAPA 1: Contexto e Processo -->
      <div v-show="etapaAtual === 1" class="space-y-5">
        <h3 class="text-base font-bold text-gray-800 border-b pb-2">1. Entendimento do Contexto e Processo</h3>
        <p class="text-xs text-gray-500">Selecione a Unidade Organizacional, o Processo hospitalar e detalhe a entrega esperada.</p>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          <!-- Unidade Organizacional Pesquisável -->
          <div class="relative" ref="unidadeDropdownRef">
            <label class="block text-xs font-semibold text-gray-700 mb-1 flex items-center justify-between">
              <span>Unidade Organizacional *</span>
              <span class="text-blue-600 font-normal text-[11px]">
                ({{ unidadesFiltradas.length }} disponíveis)
              </span>
            </label>

            <!-- Botão Seletor / Trigger do Dropdown -->
            <button
              type="button"
              @click="toggleUnidadeDropdown"
              class="w-full text-left text-sm border rounded-lg p-2.5 transition-all flex items-center justify-between focus:ring-2 focus:ring-blue-500 focus:outline-none"
              :class="[
                unidadeDropdownAberto ? 'border-blue-500 ring-2 ring-blue-100 bg-white' :
                form.unidade_id ? 'border-blue-300 bg-blue-50/20 text-gray-800' : 'border-gray-300 bg-white text-gray-500'
              ]"
            >
              <div v-if="unidadeSelecionada" class="truncate pr-2 flex items-center gap-2">
                <span v-if="unidadeSelecionada.sigla" class="px-2 py-0.5 rounded font-mono font-bold text-xs bg-blue-100 text-blue-900 border border-blue-300 shrink-0">
                  {{ unidadeSelecionada.sigla }}
                </span>
                <span class="font-semibold text-gray-900 truncate">
                  {{ unidadeSelecionada.nome }}
                </span>
              </div>
              <span v-else class="text-gray-400 text-sm truncate">
                🔍 Pesquise por sigla (ex: UGERC, SETISD) ou nome...
              </span>

              <div class="flex items-center space-x-1 flex-shrink-0 ml-1 text-gray-400">
                <span 
                  v-if="form.unidade_id" 
                  @click.stop="limparSelecaoUnidade" 
                  class="p-0.5 hover:text-gray-600 hover:bg-gray-200 rounded" 
                  title="Limpar seleção"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </span>
                <svg class="w-4 h-4 transition-transform duration-200" :class="{ 'rotate-180': unidadeDropdownAberto }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </button>

            <!-- Painel Flutuante Pesquisável -->
            <div 
              v-if="unidadeDropdownAberto" 
              class="absolute z-50 left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-2xl overflow-hidden flex flex-col"
              style="max-height: 380px;"
            >
              <!-- Campo de Pesquisa por Texto -->
              <div class="p-2.5 border-b border-gray-100 bg-gray-50/90 sticky top-0 z-10 flex items-center space-x-2">
                <div class="relative flex-1">
                  <svg class="w-4 h-4 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  <input
                    ref="unidadeSearchInputRef"
                    v-model="unidadeSearchQuery"
                    type="text"
                    placeholder="Digite a sigla ou nome da unidade..."
                    class="w-full pl-8 pr-7 py-1.5 text-xs bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    v-if="unidadeSearchQuery"
                    @click="unidadeSearchQuery = ''"
                    type="button"
                    class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-xs"
                  >
                    ✕
                  </button>
                </div>
              </div>

              <!-- Lista de Unidades -->
              <div class="overflow-y-auto divide-y divide-gray-100 flex-1">
                <div v-if="unidadesFiltradas.length === 0" class="p-4 text-center text-xs text-gray-400">
                  Nenhuma unidade encontrada para "{{ unidadeSearchQuery }}".
                </div>
                <div
                  v-for="u in unidadesFiltradas"
                  :key="'u-' + u.id"
                  @click="selecionarUnidade(u)"
                  class="px-3 py-2 text-xs rounded-lg cursor-pointer flex items-center justify-between transition-colors hover:bg-gray-100 gap-2"
                  :class="form.unidade_id === u.id ? 'bg-blue-100 text-blue-900 font-semibold' : 'text-gray-700'"
                >
                  <div class="flex items-center gap-2 min-w-0">
                    <span v-if="u.sigla" class="px-1.5 py-0.5 rounded font-mono font-bold text-[10px] bg-blue-100 text-blue-900 border border-blue-200 shrink-0">
                      {{ u.sigla }}
                    </span>
                    <span class="block font-medium truncate">{{ u.nome }}</span>
                  </div>
                  <span v-if="form.unidade_id === u.id" class="text-blue-600 font-bold text-xs shrink-0">✓</span>
                </div>
              </div>
            </div>
          </div>


          <!-- Macroprocesso & Processo Pesquisável com Seções Separadas -->
          <div class="relative" ref="dropdownRef">
            <label class="block text-xs font-semibold text-gray-700 mb-1 flex items-center justify-between">
              <span>Macroprocesso & Processo *</span>
              <span v-if="form.unidade_id" class="text-blue-600 font-normal text-[11px]">
                ({{ macroprocessosFiltrados.totalFiltrados }} disponíveis)
              </span>
            </label>

            <!-- Botão Seletor / Trigger do Dropdown -->
            <button
              type="button"
              @click="toggleDropdown"
              :disabled="!form.unidade_id"
              class="w-full text-left text-sm border rounded-lg p-2.5 transition-all flex items-center justify-between focus:ring-2 focus:ring-blue-500 focus:outline-none"
              :class="[
                !form.unidade_id ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed' :
                dropdownAberto ? 'border-blue-500 ring-2 ring-blue-100 bg-white' :
                form.processo_id ? 'border-blue-300 bg-blue-50/20 text-gray-800' : 'border-gray-300 bg-white text-gray-500'
              ]"
            >
              <div v-if="processoSelecionado" class="truncate pr-2">
                <span class="font-semibold text-gray-900 block truncate">
                  {{ isProcessoOutro ? (form.processo_outro || 'Outro (especificar)') : processoSelecionado.nome }}
                </span>
                <span class="text-[11px] text-gray-500 block truncate">
                  Macroprocesso: {{ processoSelecionado.macroprocessoNome }}
                </span>
              </div>
              <span v-else class="text-gray-400 text-sm truncate">
                {{ form.unidade_id ? '🔍 Pesquise ou selecione um processo...' : 'Selecione primeiro a Unidade Organizacional...' }}
              </span>

              <div class="flex items-center space-x-1 flex-shrink-0 ml-1 text-gray-400">
                <span 
                  v-if="form.processo_id && form.unidade_id" 
                  @click.stop="limparSelecaoProcesso" 
                  class="p-0.5 hover:text-gray-600 hover:bg-gray-200 rounded" 
                  title="Limpar seleção"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </span>
                <svg class="w-4 h-4 transition-transform duration-200" :class="{ 'rotate-180': dropdownAberto }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </button>

            <!-- Painel Flutuante Pesquisável -->
            <div 
              v-if="dropdownAberto && form.unidade_id" 
              class="absolute z-50 left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-2xl overflow-hidden flex flex-col"
              style="max-height: 400px;"
            >
              <!-- Campo de Pesquisa por Texto -->
              <div class="p-2.5 border-b border-gray-100 bg-gray-50/90 sticky top-0 z-10 flex items-center space-x-2">
                <div class="relative flex-1">
                  <svg class="w-4 h-4 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  <input
                    ref="searchInputRef"
                    v-model="searchQuery"
                    type="text"
                    placeholder="Digite para pesquisar processos ou macroprocessos..."
                    class="w-full pl-8 pr-7 py-1.5 text-xs bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    v-if="searchQuery"
                    @click="searchQuery = ''"
                    type="button"
                    class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-xs"
                  >
                    ✕
                  </button>
                </div>
              </div>

              <!-- Lista de Processos Dividida em Seções -->
              <div class="overflow-y-auto divide-y divide-gray-100 flex-1">
                <!-- SEÇÃO 1: Processos Próprios da Área -->
                <div v-if="macroprocessosFiltrados.proprios.length > 0">
                  <div class="bg-blue-50/80 px-3 py-1.5 sticky top-0 z-5 flex items-center justify-between border-b border-blue-100">
                    <span class="text-[11px] font-bold uppercase tracking-wider text-blue-900 flex items-center gap-1.5">
                      <span>🏢</span> Processos Específicos da Unidade / Área
                    </span>
                    <span class="text-[10px] bg-blue-200/80 text-blue-800 px-1.5 py-0.5 rounded font-semibold">
                      {{ macroprocessosFiltrados.totalProprios }}
                    </span>
                  </div>

                  <div v-for="m in macroprocessosFiltrados.proprios" :key="'proprio-' + m.id" class="p-1">
                    <div class="text-[10px] font-bold text-gray-500 uppercase px-2 py-1 tracking-wider">
                      {{ m.nome }}
                    </div>
                    <div class="space-y-0.5">
                      <div
                        v-for="p in m.processos"
                        :key="'p-' + p.id"
                        @click="selecionarProcesso(p)"
                        class="px-2.5 py-1.5 text-xs rounded-lg cursor-pointer flex items-center justify-between transition-colors"
                        :class="form.processo_id === p.id ? 'bg-blue-100 text-blue-900 font-semibold' : 'text-gray-700 hover:bg-gray-100'"
                      >
                        <span>{{ p.nome }}</span>
                        <span v-if="form.processo_id === p.id" class="text-blue-600 font-bold text-xs">✓</span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- SEÇÃO 2: Processos Comuns a Todas as Áreas -->
                <div v-if="macroprocessosFiltrados.comuns.length > 0">
                  <div class="bg-emerald-50/80 px-3 py-1.5 sticky top-0 z-5 flex items-center justify-between border-b border-emerald-100">
                    <span class="text-[11px] font-bold uppercase tracking-wider text-emerald-900 flex items-center gap-1.5">
                      <span>🌐</span> Processos Comuns a Todas as Áreas
                    </span>
                    <span class="text-[10px] bg-emerald-200/80 text-emerald-800 px-1.5 py-0.5 rounded font-semibold">
                      {{ macroprocessosFiltrados.totalComuns }}
                    </span>
                  </div>

                  <div v-for="m in macroprocessosFiltrados.comuns" :key="'comum-' + m.id" class="p-1">
                    <div class="text-[10px] font-bold text-gray-500 uppercase px-2 py-1 tracking-wider">
                      {{ m.nome }}
                    </div>
                    <div class="space-y-0.5">
                      <div
                        v-for="p in m.processos"
                        :key="'p-' + p.id"
                        @click="selecionarProcesso(p)"
                        class="px-2.5 py-1.5 text-xs rounded-lg cursor-pointer flex items-center justify-between transition-colors"
                        :class="form.processo_id === p.id ? 'bg-emerald-100 text-emerald-900 font-semibold' : 'text-gray-700 hover:bg-gray-100'"
                      >
                        <span>{{ p.nome }}</span>
                        <span v-if="form.processo_id === p.id" class="text-emerald-700 font-bold text-xs">✓</span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- SEÇÃO 3: Processos Cadastrados deste Setor / Hierarquia (Categoria Outro) -->
                <div v-if="processosOutrosFiltrados.length > 0" class="p-1 bg-amber-50/40">
                  <div class="bg-amber-100/80 px-3 py-1.5 flex items-center justify-between border-b border-amber-200">
                    <span class="text-[11px] font-bold uppercase tracking-wider text-amber-900 flex items-center gap-1.5">
                      <span>📂</span> Processos Cadastrados deste Setor (Categoria Outro)
                    </span>
                    <span class="text-[10px] bg-amber-200 text-amber-800 px-1.5 py-0.5 rounded font-semibold">
                      {{ processosOutrosFiltrados.length }}
                    </span>
                  </div>
                  <div class="space-y-0.5 mt-1">
                    <div
                      v-for="po in processosOutrosFiltrados"
                      :key="'po-' + po.nome"
                      @click="selecionarProcessoOutroCadastrado(po)"
                      class="px-2.5 py-1.5 text-xs rounded-lg cursor-pointer flex items-center justify-between transition-colors"
                      :class="(isProcessoOutro && form.processo_outro === po.nome) ? 'bg-amber-100 text-amber-900 font-semibold' : 'text-gray-700 hover:bg-amber-100/50'"
                    >
                      <div class="truncate">
                        <span>{{ po.nome }}</span>
                        <span v-if="po.unidade_nome" class="text-[10px] text-gray-500 block truncate">Origem: {{ po.unidade_nome }}</span>
                      </div>
                      <span v-if="isProcessoOutro && form.processo_outro === po.nome" class="text-amber-700 font-bold text-xs flex-shrink-0">✓</span>
                    </div>
                  </div>
                </div>

                <!-- SEÇÃO 4: Macroprocesso Outro (Novo Processo) -->
                <div v-if="macroprocessosFiltrados.outroProcesso" class="p-1 bg-amber-50/50">
                  <div class="text-[10px] font-bold text-amber-800 uppercase px-2 py-1 tracking-wider">
                    Novo Processo
                  </div>
                  <div
                    @click="selecionarProcesso(macroprocessosFiltrados.outroProcesso)"
                    class="px-2.5 py-2 text-xs rounded-lg cursor-pointer flex items-center justify-between transition-colors border border-dashed border-amber-300"
                    :class="isProcessoOutro ? 'bg-amber-100 text-amber-900 font-semibold' : 'text-amber-800 hover:bg-amber-100/60'"
                  >
                    <div class="flex items-center gap-1.5">
                      <span>➕</span>
                      <span>Outro (especificar processo não listado)</span>
                    </div>
                    <span v-if="isProcessoOutro" class="text-amber-700 font-bold text-xs">✓</span>
                  </div>
                </div>

                <!-- Nenhum processo encontrado na busca -->
                <div v-if="macroprocessosFiltrados.totalFiltrados === 0 && processosOutrosFiltrados.length === 0" class="p-6 text-center text-gray-500 text-xs">
                  Nenhum processo encontrado para o termo "{{ searchQuery }}".
                </div>
              </div>
            </div>


            <!-- Campo dinâmico para Outro processo -->
            <div v-if="isProcessoOutro" class="mt-2.5 p-3 bg-amber-50/80 border border-amber-200 rounded-lg space-y-1.5">
              <label class="block text-xs font-bold text-amber-900">
                Nome do Novo Processo *
              </label>
              <input 
                v-model="form.processo_outro" 
                type="text" 
                placeholder="Digite o nome do novo processo mapeado..."
                class="w-full text-sm border-amber-300 rounded-lg p-2.5 border focus:ring-amber-500 bg-white"
              />
              <p class="text-[11px] text-amber-700">
                Ao selecionar "Outro", informe a denominação do processo para análise pela UGERC.
              </p>
            </div>
          </div>
        </div>

        <!-- Seção de Projeto (Condicional ou Transversal) -->
        <div class="bg-blue-50/50 p-4 rounded-lg border border-blue-100 space-y-3">
          <div class="flex items-center justify-between">
            <div>
              <span class="text-sm font-semibold text-gray-800">O risco está associado a um Projeto específico?</span>
              <p class="text-xs text-gray-500">Recomendado para iniciativas e processos transversais corporativos.</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="form.possui_projeto" class="sr-only peer">
              <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          <div v-if="form.possui_projeto" class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">Nome do Projeto *</label>
              <input v-model="form.nome_projeto" type="text" placeholder="Ex: Implantação do Censo Eletrônico" class="w-full text-sm border-gray-300 rounded-lg p-2.5 border focus:ring-blue-500">
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">Pilar do Mapa Estratégico HC-UFPE *</label>
              <select v-model="form.pilar_estrategico_id" class="w-full text-sm border-gray-300 rounded-lg p-2.5 border focus:ring-blue-500">
                <option :value="null">Selecione o Pilar...</option>
                <option v-for="p in pilares" :key="p.id" :value="p.id">{{ p.numero }}. {{ p.nome }}</option>
              </select>
            </div>
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-gray-700 mb-1">Entrega do Processo / Produto Entregue *</label>
          <textarea v-model="form.entrega_processo" rows="2" placeholder="Que produto ou serviço é entregue ao final deste processo? Ex: Relatório de auditoria validado" class="w-full text-sm border-gray-300 rounded-lg p-2.5 border focus:ring-blue-500"></textarea>
        </div>
      </div>

      <!-- ETAPA 2: Identificação do Risco -->
      <div v-show="etapaAtual === 2" class="space-y-5">
        <h3 class="text-base font-bold text-gray-800 border-b pb-2">2. Identificação e Análise do Evento de Risco</h3>

        <div class="grid grid-cols-1 gap-4">
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Categoria do Risco *</label>
            <select v-model="evento.categoria" class="w-full text-sm border-gray-300 rounded-lg p-2.5 border focus:ring-blue-500">
              <option v-for="cat in categoriasRiscoGuia" :key="cat.valor" :value="cat.valor">
                {{ cat.nome }} — {{ cat.descricao }}
              </option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Causa do Evento de Risco * (Origem)</label>
            <input v-model="evento.causa" type="text" placeholder="Motivos que podem provocar a ocorrência (Ex: Escassez de insumos e atraso na entrega de fornecedores)" class="w-full text-sm border-gray-300 rounded-lg p-2.5 border focus:ring-blue-500">
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Descrição do Evento de Risco * (O que pode acontecer)</label>
            <input v-model="evento.descricao_evento" type="text" placeholder="O que pode impedir ou dificultar a entrega (Ex: Atraso no cronograma de cirurgias eletivas)" class="w-full text-sm border-gray-300 rounded-lg p-2.5 border focus:ring-blue-500">
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Consequência do Evento de Risco * (Impacto final)</label>
            <input v-model="evento.consequencia" type="text" placeholder="Impacto negativo sobre os objetivos do processo (Ex: Desassistência ao paciente e aumento do tempo de internação)" class="w-full text-sm border-gray-300 rounded-lg p-2.5 border focus:ring-blue-500">
          </div>
        </div>

        <!-- Preview Dinâmico da Frase Síntese com Legenda de Coerência -->
        <div class="bg-amber-50 p-4 rounded-xl border border-amber-200 space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold uppercase text-amber-900 tracking-wider">Síntese da correlação evento-causa-consequência:</span>
          </div>
          <p class="text-sm text-gray-900 italic font-medium leading-relaxed bg-white/70 p-3 rounded-lg border border-amber-200/60">
            "Devido a <strong>{{ evento.causa || '...' }}</strong>, poderá acontecer <strong>{{ evento.descricao_evento || '...' }}</strong>, o que pode levar a <strong>{{ evento.consequencia || '...' }}</strong>."
          </p>
          <div class="flex items-start gap-1.5 text-[11px] text-amber-800">
            <span class="flex-shrink-0 text-sm">💡</span>
            <span>Esta frase é gerada automaticamente a partir da combinação entre causa, evento e consequência. Caso não haja coerência entre os elementos, revise os campos preenchidos para garantir uma relação lógica entre eles.</span>
          </div>

        </div>
      </div>

      <!-- ETAPA 3: Avaliação & Controles -->
      <div v-show="etapaAtual === 3" class="space-y-6">
        <div class="border-b pb-2 flex justify-between items-center">
          <div>
            <h3 class="text-base font-bold text-gray-800">3. Avaliação dos Riscos e Medidas de Controle</h3>
            <p class="text-xs text-gray-500">Mensuração de Probabilidade, Impacto e Controles Internos.</p>
          </div>
        </div>



        <!-- Probabilidade e Impacto com descrições visíveis em cards selecionáveis -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Probabilidade -->
          <div class="bg-gray-50 p-4 rounded-xl border border-gray-200 flex flex-col justify-between">
            <div>
              <div class="flex justify-between items-center mb-3">
                <div>
                  <label class="block text-xs font-bold text-gray-800">Quão provável é a ocorrência deste risco? *</label>
                </div>
                <span v-if="avaliacao.probabilidade" :class="getBadgeEscalaClass(avaliacao.probabilidade)" class="text-xs px-2.5 py-1 rounded-lg font-bold transition-colors shadow-sm">
                  Peso {{ avaliacao.probabilidade }} - {{ probabilidadeSelecionada?.rotulo }}
                </span>
                <span v-else class="text-[11px] text-amber-800 bg-amber-50 px-2.5 py-1 rounded-lg border border-amber-200 font-semibold">
                  Selecione uma opção
                </span>
              </div>

              <!-- Lista de 5 Opções com Descrição Visível -->
              <div class="space-y-2">
                <div 
                  v-for="p in escalaProbabilidade" 
                  :key="'prob-' + p.peso"
                  @click="avaliacao.probabilidade = p.peso; recalcular()"
                  class="p-2.5 rounded-xl border cursor-pointer transition-all flex items-start gap-3"
                  :class="[
                    avaliacao.probabilidade === p.peso
                      ? 'ring-2 ring-blue-500 border-blue-500 bg-blue-50/50 shadow-sm'
                      : 'bg-white border-gray-200 hover:bg-gray-100/70 hover:border-gray-300'
                  ]"
                >
                  <span 
                    class="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 border mt-0.5"
                    :class="getBotaoEscalaClass(p.peso, avaliacao.probabilidade)"
                  >
                    {{ p.peso }}
                  </span>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between">
                      <span class="font-bold text-xs" :class="avaliacao.probabilidade === p.peso ? 'text-blue-950 font-extrabold' : 'text-gray-800'">
                        {{ p.rotulo }} (Peso {{ p.peso }})
                      </span>
                      <span v-if="avaliacao.probabilidade === p.peso" class="text-blue-600 font-bold text-xs shrink-0">
                        ✓ Selecionado
                      </span>
                    </div>
                    <p class="text-[11px] text-gray-600 mt-0.5 leading-snug">
                      {{ p.descricao }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Impacto -->
          <div class="bg-gray-50 p-4 rounded-xl border border-gray-200 flex flex-col justify-between">
            <div>
              <div class="flex justify-between items-center mb-3">
                <div>
                  <label class="block text-xs font-bold text-gray-800">Qual o grau de impacto deste risco? *</label>
                </div>
                <span v-if="avaliacao.impacto" :class="getBadgeEscalaClass(avaliacao.impacto)" class="text-xs px-2.5 py-1 rounded-lg font-bold transition-colors shadow-sm">
                  Peso {{ avaliacao.impacto }} - {{ impactoSelecionado?.rotulo }}
                </span>
                <span v-else class="text-[11px] text-amber-800 bg-amber-50 px-2.5 py-1 rounded-lg border border-amber-200 font-semibold">
                  Selecione uma opção
                </span>
              </div>

              <!-- Lista de 5 Opções com Descrição Visível -->
              <div class="space-y-2">
                <div 
                  v-for="i in escalaImpacto" 
                  :key="'imp-' + i.peso"
                  @click="avaliacao.impacto = i.peso; recalcular()"
                  class="p-2.5 rounded-xl border cursor-pointer transition-all flex items-start gap-3"
                  :class="[
                    avaliacao.impacto === i.peso
                      ? 'ring-2 ring-blue-500 border-blue-500 bg-blue-50/50 shadow-sm'
                      : 'bg-white border-gray-200 hover:bg-gray-100/70 hover:border-gray-300'
                  ]"
                >
                  <span 
                    class="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 border mt-0.5"
                    :class="getBotaoEscalaClass(i.peso, avaliacao.impacto)"
                  >
                    {{ i.peso }}
                  </span>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between">
                      <span class="font-bold text-xs" :class="avaliacao.impacto === i.peso ? 'text-blue-950 font-extrabold' : 'text-gray-800'">
                        {{ i.rotulo }} (Peso {{ i.peso }})
                      </span>
                      <span v-if="avaliacao.impacto === i.peso" class="text-blue-600 font-bold text-xs shrink-0">
                        ✓ Selecionado
                      </span>
                    </div>
                    <p class="text-[11px] text-gray-600 mt-0.5 leading-snug">
                      {{ i.descricao }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Medidas de Controle Interno Existentes -->
        <div class="space-y-4 bg-gray-50 p-4 rounded-xl border border-gray-200">
          <div>
            <h4 class="text-xs font-bold uppercase tracking-wider text-gray-800">
              Análise de Controles Internos Existentes *
            </h4>
            <p class="text-xs text-gray-500 mt-0.5">
              Selecione o nível de maturidade dos controles instituídos no setor. O Fator de Mitigação é fixado pelo nível escolhido e independe da quantidade de medidas listadas.
            </p>
          </div>

          <!-- Seleção do Nível dos Controles com Texto Completo -->
          <div class="grid grid-cols-1 md:grid-cols-5 gap-2.5 items-stretch">
            <div 
              v-for="nivel in niveisControleTabela3" 
              :key="nivel.valor"
              @click="onNivelControleChange(nivel.valor)"
              class="p-3 rounded-xl border cursor-pointer transition-all flex flex-col justify-between h-full"
              :class="avaliacao.nivel_controle === nivel.valor 
                ? 'bg-blue-50/90 border-blue-500 ring-2 ring-blue-200 shadow-sm' 
                : 'bg-white border-gray-200 hover:bg-gray-50 hover:border-gray-300'"
            >
              <div>
                <div class="mb-2">
                  <span class="font-bold text-xs block" :class="avaliacao.nivel_controle === nivel.valor ? 'text-blue-900' : 'text-gray-800'">
                    {{ nivel.rotulo }}
                  </span>
                  <div class="mt-1">
                    <span class="text-[10px] font-mono px-1.5 py-0.5 rounded font-bold inline-block" :class="nivel.badge">
                      Fator de Mitigação: {{ nivel.fnc.toFixed(1) }}
                    </span>
                  </div>
                </div>
                <p class="text-[11px] leading-relaxed" :class="avaliacao.nivel_controle === nivel.valor ? 'text-blue-950/80' : 'text-gray-600'">
                  {{ nivel.definicao }}
                </p>
              </div>
              <div class="mt-3 pt-2 border-t border-gray-100 text-[10px] text-right font-semibold" :class="avaliacao.nivel_controle === nivel.valor ? 'text-blue-700 font-bold' : 'text-gray-400'">
                {{ avaliacao.nivel_controle === nivel.valor ? '● Selecionado' : '○ Selecionar' }}
              </div>
            </div>
          </div>


          <!-- Seção de Medidas de Controle (Oculta se Inexistente) -->
          <div v-if="avaliacao.nivel_controle === 'INEXISTENTE'" class="text-xs text-gray-600 bg-amber-50 p-3.5 rounded-lg border border-amber-200 flex items-center gap-2">
            <span class="text-base">ℹ️</span>
            <span>Como os controles foram classificados como <strong>Inexistentes</strong>, não há medidas de controle vigentes a descrever. O Fator de Mitigação aplicado é <strong>1,0 (sem redução de risco)</strong>.</span>
          </div>

          <div v-else class="space-y-3 pt-2 border-t border-gray-200">
            <div class="flex justify-between items-center">
              <div>
                <h5 class="text-xs font-bold text-gray-800">Elencar Medidas de Controle Interno Existentes</h5>
                <p class="text-[11px] text-gray-500">Cadastre as ferramentas, rotinas, checklists ou protocolos atualmente adotados pelo setor.</p>
              </div>
              <button 
                type="button" 
                @click="adicionarControle"
                class="px-3 py-1.5 text-xs font-semibold bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition flex items-center gap-1 shadow-sm"
              >
                <span>+</span>
                <span>Adicionar Medida</span>
              </button>
            </div>

            <div v-if="avaliacao.controles.length === 0" class="text-xs text-rose-600 p-3 bg-rose-50 rounded-lg text-center border border-dashed border-rose-200">
              Atenção: Como você classificou o controle como "{{ nivelControleSelecionado?.rotulo }}", é necessário cadastrar ao menos uma medida de controle existente.
            </div>

            <div v-else class="space-y-2">
              <div v-for="(ctrl, idx) in avaliacao.controles" :key="idx" class="flex items-center space-x-2">
                <span class="text-xs font-semibold text-gray-400 w-6">#{{ idx + 1 }}</span>
                <input 
                  v-model="ctrl.descricao_controle" 
                  type="text" 
                  placeholder="Descreva a medida de controle existente (ex: Checklist de conferência diária)" 
                  class="flex-1 text-sm border-gray-300 rounded-lg p-2 border focus:ring-blue-500"
                />
                <button 
                  type="button" 
                  @click="removerControle(idx)"
                  class="p-2 text-rose-500 hover:text-rose-700 hover:bg-rose-50 rounded-lg transition"
                >
                  ✕
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Resumo do Cálculo em Tempo Real com Popups Explicativos -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 bg-gray-50 p-4 rounded-xl border border-gray-200 text-center">
          <!-- 1. Risco Inerente -->
          <div class="relative group">
            <div class="flex items-center justify-center gap-1">
              <span class="text-xs text-gray-500 font-medium">Risco Inerente (P × I)</span>
              <button 
                type="button" 
                @click.stop="togglePopup('inerente')"
                class="text-gray-400 hover:text-blue-600 focus:outline-none transition-colors p-0.5 rounded hover:bg-gray-200/60"
                title="Clique ou passe o mouse para entender o Risco Inerente"
              >
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </button>
            </div>
            
            <!-- Popup Tooltip Explicativo -->
            <div 
              class="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 w-64 p-3 bg-white text-gray-800 rounded-xl shadow-xl border border-blue-100 text-left transition-all duration-200 z-30 pointer-events-none opacity-0 group-hover:opacity-100 group-hover:pointer-events-auto"
              :class="{ '!opacity-100 !pointer-events-auto': popupAtivo === 'inerente' }"
            >
              <div class="flex items-center gap-1.5 font-bold text-blue-950 text-xs mb-1">
                <span>🎯</span>
                <span>Risco Inerente</span>
              </div>
              <p class="text-[11px] text-blue-800 leading-relaxed">
                Risco a que a organização está exposta <strong>sem considerar</strong> quaisquer ações gerenciais ou medidas de controle. Calculado por <em>Probabilidade × Impacto</em>.
              </p>
              <div class="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-white"></div>
            </div>

            <span class="text-xl font-bold text-gray-800 block mt-0.5">
              {{ calculo.risco_inerente !== null ? calculo.risco_inerente : '-' }}
            </span>
          </div>

          <!-- 2. Fator de Mitigação -->
          <div class="relative group">
            <div class="flex items-center justify-center gap-1">
              <span class="text-xs text-gray-500 font-medium">Fator de Mitigação</span>
              <button 
                type="button" 
                @click.stop="togglePopup('fnc')"
                class="text-gray-400 hover:text-purple-600 focus:outline-none transition-colors p-0.5 rounded hover:bg-gray-200/60"
                title="Clique ou passe o mouse para entender o Fator de Mitigação"
              >
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </button>
            </div>

            <!-- Popup Tooltip Explicativo -->
            <div 
              class="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 w-64 p-3 bg-white text-gray-800 rounded-xl shadow-xl border border-purple-100 text-left transition-all duration-200 z-30 pointer-events-none opacity-0 group-hover:opacity-100 group-hover:pointer-events-auto"
              :class="{ '!opacity-100 !pointer-events-auto': popupAtivo === 'fnc' }"
            >
              <div class="flex items-center gap-1.5 font-bold text-purple-950 text-xs mb-1">
                <span>🛡️</span>
                <span>Fator de Mitigação</span>
              </div>
              <p class="text-[11px] text-purple-800 leading-relaxed">
                Índice numérico que expressa o grau de robustez e maturidade dos controles internos instituídos na prevenção e redução do risco.
              </p>
              <div class="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-white"></div>
            </div>

            <span class="text-xl font-bold text-blue-600 block mt-0.5">
              {{ calculo.fator_mitigacao.toFixed(1) }}
            </span>
          </div>

          <!-- 3. Risco Residual -->
          <div class="relative group">
            <div class="flex items-center justify-center gap-1">
              <span class="text-xs text-gray-500 font-medium">Risco Residual</span>
              <button 
                type="button" 
                @click.stop="togglePopup('residual')"
                class="text-gray-400 hover:text-emerald-600 focus:outline-none transition-colors p-0.5 rounded hover:bg-gray-200/60"
                title="Clique ou passe o mouse para entender o Risco Residual"
              >
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </button>
            </div>

            <!-- Popup Tooltip Explicativo -->
            <div 
              class="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 w-64 p-3 bg-white text-gray-800 rounded-xl shadow-xl border border-emerald-100 text-left transition-all duration-200 z-30 pointer-events-none opacity-0 group-hover:opacity-100 group-hover:pointer-events-auto"
              :class="{ '!opacity-100 !pointer-events-auto': popupAtivo === 'residual' }"
            >
              <div class="flex items-center gap-1.5 font-bold text-emerald-950 text-xs mb-1">
                <span>⚖️</span>
                <span>Risco Residual</span>
              </div>
              <p class="text-[11px] text-emerald-800 leading-relaxed">
                Risco remanescente a que a organização continua exposta <strong>após a consideração</strong> das ações e controles gerenciais. Calculado por <em>Risco Inerente × Fator de Mitigação</em>.
              </p>
              <div class="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-white"></div>
            </div>

            <span class="text-xl font-bold text-gray-900 block mt-0.5">
              {{ calculo.risco_residual !== null ? calculo.risco_residual : '-' }}
            </span>
          </div>

          <!-- 4. Classificação Final -->
          <div>
            <span class="text-xs text-gray-500 block">Classificação Final</span>
            <span 
              v-if="calculo.classificacao !== '-'"
              :class="getClassificacaoBadge(calculo.classificacao)"
              class="inline-block mt-1 px-3 py-0.5 rounded-full text-xs font-extrabold uppercase"
            >
              {{ calculo.classificacao }}
            </span>
            <span v-else class="text-xs text-gray-400 inline-block mt-1">Aguardando notas</span>
          </div>
        </div>
      </div>


      <!-- ETAPA 4: Matriz de Priorização -->
      <div v-show="etapaAtual === 4" class="space-y-5">
        <h3 class="text-base font-bold text-gray-800 border-b pb-2">4. Priorização dos Riscos na Matriz de Riscos</h3>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div class="lg:col-span-2">
            <MatrizRisco5x5 
              :activeP="avaliacao.probabilidade" 
              :activeI="avaliacao.impacto" 
              :activeResidual="calculo.risco_residual"
              :activeClassificacao="calculo.classificacao"
              :fatorMitigacao="calculo.fator_mitigacao"
              :nivelControle="nivelControleSelecionado?.rotulo"
            />
          </div>

          <div class="space-y-4">
            <!-- Card de Apetite a Risco com Alto Destaque e Efeito Pulsante Suave -->
            <div 
              class="p-5 rounded-2xl border-2 transition-all duration-300"
              :class="calculo.acima_apetite 
                ? 'bg-rose-50/90 border-rose-400 card-apetite-rose' 
                : 'bg-emerald-50/90 border-emerald-400 card-apetite-emerald'"
            >
              <div class="flex items-start gap-3.5">
                <div 
                  class="p-2.5 rounded-xl shrink-0 text-2xl flex items-center justify-center shadow-sm relative"
                  :class="calculo.acima_apetite ? 'bg-rose-200 text-rose-900' : 'bg-emerald-200 text-emerald-900'"
                >
                  <span v-if="calculo.acima_apetite">🚨</span>
                  <span v-else>🛡️</span>
                </div>

                <div class="flex-1">
                  <div class="flex items-center justify-between flex-wrap gap-2">
                    <div class="flex items-center">
                      <!-- Ponto luminoso pulsante (beacon de status) -->
                      <span class="relative flex h-2.5 w-2.5 mr-2">
                        <span 
                          class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
                          :class="calculo.acima_apetite ? 'bg-rose-400' : 'bg-emerald-400'"
                        ></span>
                        <span 
                          class="relative inline-flex rounded-full h-2.5 w-2.5"
                          :class="calculo.acima_apetite ? 'bg-rose-600' : 'bg-emerald-600'"
                        ></span>
                      </span>

                      <span 
                        class="px-2.5 py-1 rounded-md text-xs font-black tracking-wider uppercase shadow-sm inline-block"
                        :class="calculo.acima_apetite ? 'bg-rose-600 text-white' : 'bg-emerald-700 text-white'"
                      >
                        {{ calculo.acima_apetite ? 'ACIMA DO APETITE A RISCO' : 'DENTRO DO APETITE A RISCO' }}
                      </span>
                    </div>

                    <span 
                      class="text-xs font-bold px-2.5 py-0.5 rounded-full border shadow-xs"
                      :class="calculo.acima_apetite 
                        ? 'bg-rose-100 text-rose-900 border-rose-300' 
                        : 'bg-emerald-100 text-emerald-900 border-emerald-300'"
                    >
                      Residual: {{ calculo.risco_residual ?? '-' }} (Limite: 7,99)
                    </span>
                  </div>

                  <p 
                    class="text-xs leading-relaxed mt-2.5 font-medium"
                    :class="calculo.acima_apetite ? 'text-rose-950' : 'text-emerald-950'"
                  >
                    <template v-if="calculo.acima_apetite">
                      Este risco possui resultado residual <strong>superior a 7,99 (Classificação {{ calculo.classificacao }})</strong>. Conforme deliberação do <strong>Colegiado Executivo do HC-UFPE</strong>, é <strong>OBRIGATÓRIO</strong> elaborar <strong>Plano de Ação</strong> e <strong>Plano de Contingência</strong> na próxima etapa.
                    </template>
                    <template v-else>
                      Este risco está <strong>dentro da tolerância institucional (≤ 7,99)</strong> homologada pelo <strong>Colegiado Executivo</strong>. O risco é tolerado e <strong>não exige tratamento compulsório</strong>, embora novas medidas preventivas possam ser adotadas voluntariamente na Etapa 5.
                    </template>
                  </p>
                </div>
              </div>
            </div>

            <div class="bg-gray-50 p-4 rounded-xl border border-gray-200 space-y-2 text-xs text-gray-600">
              <p><strong>Causa:</strong> {{ evento.causa || 'Não preenchida' }}</p>
              <p><strong>Evento:</strong> {{ evento.descricao_evento || 'Não preenchido' }}</p>
              <p><strong>Consequência:</strong> {{ evento.consequencia || 'Não preenchida' }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- ETAPA 5: Resposta, Planos de Ação e Contingência -->
      <div v-show="etapaAtual === 5" class="space-y-6">
        <div class="border-b pb-3">
          <h3 class="text-base font-bold text-gray-800">5. Respostas aos Riscos, Planos de Ação e Contingência</h3>
          <p class="text-xs text-gray-500">Elabore o plano de ação e plano de contingência com gatilhos operacionais.</p>
        </div>

        <!-- Planos de Ação -->
        <div class="space-y-3">
          <div class="flex justify-between items-center">
            <h4 class="text-xs font-bold text-gray-800 uppercase tracking-wider">Planos de Ação</h4>
            <button 
              type="button" 
              @click="adicionarPlanoAcao"
              class="px-3 py-1.5 text-xs font-semibold bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              + Adicionar Ação
            </button>
          </div>

          <div v-if="evento.planos_acao.length === 0" class="text-xs text-gray-400 p-4 bg-gray-50 rounded-lg text-center border border-dashed">
            Nenhuma ação cadastrada.
          </div>

          <div v-else class="space-y-3">
            <div v-for="(pa, idx) in evento.planos_acao" :key="idx" class="p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-3">
              <div class="flex justify-between items-center border-b pb-2">
                <span class="text-xs font-bold text-gray-700">Ação #{{ idx + 1 }}</span>
                <button type="button" @click="removerPlanoAcao(idx)" class="text-xs text-rose-600 hover:underline">Remover</button>
              </div>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <label class="block text-[11px] font-semibold text-gray-600 mb-1">Tipo de Resposta</label>
                  <select v-model="pa.tipo_resposta" class="w-full text-xs border-gray-300 rounded p-2 border">
                    <option value="MITIGAR">Mitigar / Reduzir</option>
                    <option value="EVITAR">Evitar</option>
                    <option value="COMPARTILHAR">Compartilhar / Transferir</option>
                    <option value="ACEITAR">Aceitar</option>
                  </select>
                </div>
                <div>
                  <label class="block text-[11px] font-semibold text-gray-600 mb-1">Quem (Responsável)</label>
                  <input v-model="pa.quem" type="text" placeholder="Nome ou cargo" class="w-full text-xs border-gray-300 rounded p-2 border" />
                </div>
                <div>
                  <label class="block text-[11px] font-semibold text-gray-600 mb-1">Período (Início - Término)</label>
                  <div class="grid grid-cols-2 gap-1">
                    <input v-model="pa.data_inicio" type="date" class="text-xs border-gray-300 rounded p-1.5 border" />
                    <input v-model="pa.data_termino" type="date" class="text-xs border-gray-300 rounded p-1.5 border" />
                  </div>
                </div>
              </div>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label class="block text-[11px] font-semibold text-gray-600 mb-1">O que fazer?</label>
                  <input v-model="pa.o_que" type="text" placeholder="Ação detalhada" class="w-full text-xs border-gray-300 rounded p-2 border" />
                </div>
                <div>
                  <label class="block text-[11px] font-semibold text-gray-600 mb-1">Como fazer?</label>
                  <input v-model="pa.como" type="text" placeholder="Método / Recursos" class="w-full text-xs border-gray-300 rounded p-2 border" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Planos de Contingência -->
        <div class="space-y-3 pt-4 border-t">
          <div class="flex justify-between items-center">
            <div>
              <div class="flex items-center gap-2">
                <h4 class="text-xs font-bold text-gray-800 uppercase tracking-wider">Planos de Contingência</h4>
                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-100 text-purple-800 border border-purple-200 uppercase">
                  OPCIONAL
                </span>
              </div>
              <p class="text-xs text-gray-500 mt-0.5">Ações preparadas para ativação imediata caso o gatilho ocorra.</p>
            </div>
            <button 
              type="button" 
              @click="adicionarPlanoContingencia"
              class="px-3 py-1.5 text-xs font-semibold bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
            >
              + Adicionar Contingência
            </button>
          </div>

          <div v-if="evento.planos_contingencia.length === 0" class="text-xs text-gray-400 p-4 bg-gray-50 rounded-lg text-center border border-dashed">
            Nenhum plano de contingência cadastrado.
          </div>

          <div v-else class="space-y-3">
            <div v-for="(pc, idx) in evento.planos_contingencia" :key="idx" class="p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-3">
              <div class="flex justify-between items-center border-b pb-2">
                <span class="text-xs font-bold text-gray-700">Contingência #{{ idx + 1 }}</span>
                <button type="button" @click="removerPlanoContingencia(idx)" class="text-xs text-rose-600 hover:underline">Remover</button>
              </div>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label class="block text-[11px] font-semibold text-gray-600 mb-1">Gatilho (Trigger que dispara o plano)</label>
                  <input v-model="pc.gatilho" type="text" placeholder="Ex: Queda do sistema superior a 2 horas" class="w-full text-xs border-gray-300 rounded p-2 border" />
                </div>
                <div>
                  <label class="block text-[11px] font-semibold text-gray-600 mb-1">Responsável pela Ativação</label>
                  <input v-model="pc.responsavel" type="text" placeholder="Cargo / Setor" class="w-full text-xs border-gray-300 rounded p-2 border" />
                </div>
                <div>
                  <label class="block text-[11px] font-semibold text-gray-600 mb-1">O que fazer?</label>
                  <input v-model="pc.o_que" type="text" placeholder="Procedimento manual" class="w-full text-xs border-gray-300 rounded p-2 border" />
                </div>
                <div>
                  <label class="block text-[11px] font-semibold text-gray-600 mb-1">Como fazer?</label>
                  <input v-model="pc.como" type="text" placeholder="Orientações e acionamentos" class="w-full text-xs border-gray-300 rounded p-2 border" />
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>

    </div>

      <!-- Navegação Inferior de Passos -->
      <div class="flex justify-between items-center">
        <button 
          type="button" 
          @click="voltarEtapa" 
          :disabled="etapaAtual === 1"
          class="px-4 py-2 text-sm text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40"
        >
          ← Voltar
        </button>

        <span class="text-xs text-gray-400">Etapa {{ etapaAtual }} de 5</span>

        <button 
          type="button" 
          @click="avancarEtapa" 
          :disabled="etapaAtual === 5"
          class="px-5 py-2 text-sm text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-40 shadow-sm"
        >
          Avançar →
        </button>
      </div>
    </div> <!-- Fim de .max-w-6xl (print:hidden) -->

    <!-- Seção de Impressão Unificada (Visível em Impressão ou Geração de PDF - Multi-páginas) -->
    <div id="secao-relatorio-impressao" class="hidden print:block text-gray-900 bg-white font-sans max-w-[99%] mx-auto">
      <!-- Cabeçalho Institucional -->
      <div class="bloco-impressao border-b-2 border-blue-900 pb-2.5 mb-3 flex justify-between items-start">
        <div class="flex items-center gap-3">
          <div class="w-11 h-11 bg-blue-900 text-white rounded-lg flex items-center justify-center font-black text-lg tracking-tighter">
            HC
          </div>
          <div>
            <h1 class="text-sm font-extrabold uppercase text-blue-950 tracking-wide">Hospital das Clínicas da UFPE / EBSERH</h1>
            <p class="text-[11px] text-gray-700 font-semibold">UGERC - Unidade de Gestão de Riscos e Controles Internos</p>
          </div>
        </div>
        <div class="text-right">
          <span class="inline-block px-2.5 py-0.5 rounded border text-[11px] font-bold"
                :class="form.status === 'HOMOLOGADO' ? 'border-emerald-500 bg-emerald-50 text-emerald-800' : form.status === 'SUBMETIDO' ? 'border-blue-500 bg-blue-50 text-blue-800' : 'border-amber-500 bg-amber-50 text-amber-800'">
            STATUS: {{ form.status }}
          </span>
          <p class="text-[10px] text-gray-500 mt-0.5">Ficha ID #{{ form.id || 'NOVA' }}</p>
          <p class="text-[10px] text-gray-400">Emissão: {{ dataHoraAtual }}</p>
        </div>
      </div>

      <div class="bloco-impressao text-center mb-3">
        <h2 class="text-sm font-bold text-gray-900 uppercase tracking-wide">Ficha Completa de Mapeamento de Risco</h2>
        <p class="text-[11px] text-gray-600">Relatório Unificado das 5 Etapas Metodológicas UGERC</p>
      </div>

      <!-- 1. Contexto e Processo -->
      <div class="bloco-impressao mb-3 border border-gray-300 rounded-md">
        <div class="bg-gray-100 px-3 py-1 border-b border-gray-300 font-bold text-xs uppercase text-gray-800 flex justify-between">
          <span>1. Entendimento do Contexto e Processo Hospitalar</span>
          <span class="text-[10px] font-normal text-gray-600">Etapa 1</span>
        </div>
        <div class="p-2.5 text-xs space-y-2">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <span class="font-bold text-gray-700 block text-[11px]">Unidade Organizacional:</span>
              <span class="text-gray-900">{{ unidadeSelecionada ? `${unidadeSelecionada.nome} (${unidadeSelecionada.sigla || 'Sem sigla'})` : 'Não informada' }}</span>
            </div>
            <div>
              <span class="font-bold text-gray-700 block text-[11px]">Processo / Macroprocesso:</span>
              <span class="text-gray-900">
                {{ isProcessoOutro ? (form.processo_outro ? `${form.processo_outro} (Outro Processo)` : 'Outro Processo') : (processoSelecionado ? `${processoSelecionado.nome} [${processoSelecionado.macroprocessoNome}]` : 'Não selecionado') }}
              </span>
            </div>
          </div>

          <!-- Exibir Pilar Estratégico e Projeto Vinculado APENAS se houver registro destes na ficha -->
          <div 
            v-if="pilarSelecionado || (form.possui_projeto && form.nome_projeto)" 
            class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1 border-t border-gray-100"
          >
            <div v-if="pilarSelecionado">
              <span class="font-bold text-gray-700 block text-[11px]">Pilar Estratégico HC-UFPE:</span>
              <span class="text-gray-900">{{ pilarSelecionado.nome }}</span>
            </div>
            <div v-if="form.possui_projeto && form.nome_projeto">
              <span class="font-bold text-gray-700 block text-[11px]">Projeto Vinculado:</span>
              <span class="text-gray-900">{{ form.nome_projeto }}</span>
            </div>
          </div>

          <div class="pt-1 border-t border-gray-100">
            <span class="font-bold text-gray-700 block text-[11px]">Entrega Esperada do Processo:</span>
            <p class="text-gray-800 italic bg-gray-50/70 p-2 rounded border border-gray-200 mt-0.5 whitespace-pre-wrap">{{ form.entrega_processo || 'Não informada' }}</p>
          </div>
        </div>
      </div>

      <!-- 2. Identificação do Risco -->
      <div class="bloco-impressao mb-3 border border-gray-300 rounded-md">
        <div class="bg-gray-100 px-3 py-1 border-b border-gray-300 font-bold text-xs uppercase text-gray-800 flex justify-between">
          <span>2. Identificação do Risco</span>
          <span class="text-[10px] font-normal text-gray-600">Etapa 2</span>
        </div>
        <div class="p-2.5 text-xs space-y-2">
          <div class="flex items-center gap-2">
            <span class="font-bold text-gray-700 text-[11px]">Categoria do Risco:</span>
            <span class="px-2 py-0.5 bg-blue-100 text-blue-900 font-bold rounded text-[10px] border border-blue-200">
              {{ categoriaSelecionada?.nome || evento.categoria }}
            </span>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-2.5 pt-1">
            <div class="p-2 rounded bg-gray-50/70 border border-gray-200">
              <span class="font-bold text-gray-700 block text-[10px] uppercase">Causa (Origem / Fator)</span>
              <p class="text-gray-900 mt-0.5 text-[11px]">{{ evento.causa || 'Não preenchida' }}</p>
            </div>
            <div class="p-2 rounded bg-gray-50/70 border border-gray-200">
              <span class="font-bold text-gray-700 block text-[10px] uppercase">Evento de Risco</span>
              <p class="text-gray-900 mt-0.5 font-semibold text-rose-950 text-[11px]">{{ evento.descricao_evento || 'Não preenchido' }}</p>
            </div>
            <div class="p-2 rounded bg-gray-50/70 border border-gray-200">
              <span class="font-bold text-gray-700 block text-[10px] uppercase">Consequência (Impacto)</span>
              <p class="text-gray-900 mt-0.5 text-[11px]">{{ evento.consequencia || 'Não preenchida' }}</p>
            </div>
          </div>
          <div class="p-2 bg-blue-50/60 rounded border border-blue-200 text-blue-950 text-[11px]">
            <span class="font-bold block text-[10px] text-blue-900 mb-0.5">Declaração Integrada do Risco:</span>
            <em>"Devido a {{ evento.causa || '[Causa]' }}, pode ocorrer {{ evento.descricao_evento || '[Evento]' }}, resultando em {{ evento.consequencia || '[Consequência]' }}."</em>
          </div>
        </div>
      </div>

      <!-- 3 e 4. Avaliação e Controles Existentes -->
      <div class="bloco-impressao mb-3 border border-gray-300 rounded-md">
        <div class="bg-gray-100 px-3 py-1 border-b border-gray-300 font-bold text-xs uppercase text-gray-800 flex justify-between">
          <span>3 e 4. Avaliação e Controles Existentes</span>
          <span class="text-[10px] font-normal text-gray-600">Etapas 3 e 4</span>
        </div>
        <div class="p-2.5 text-xs space-y-2.5">
          <div class="grid grid-cols-4 gap-2 text-center">
            <div class="p-1.5 bg-gray-50/70 rounded border border-gray-200">
              <span class="text-[9px] uppercase text-gray-500 font-bold block">Probabilidade</span>
              <span class="text-sm font-extrabold text-gray-900">{{ avaliacao.probabilidade || '-' }}</span>
              <span class="text-[9px] text-gray-600 block">{{ probabilidadeSelecionada?.rotulo || '' }}</span>
            </div>
            <div class="p-1.5 bg-gray-50/70 rounded border border-gray-200">
              <span class="text-[9px] uppercase text-gray-500 font-bold block">Impacto</span>
              <span class="text-sm font-extrabold text-gray-900">{{ avaliacao.impacto || '-' }}</span>
              <span class="text-[9px] text-gray-600 block">{{ impactoSelecionado?.rotulo || '' }}</span>
            </div>
            <div class="p-1.5 bg-gray-50/70 rounded border border-gray-200">
              <span class="text-[9px] uppercase text-gray-500 font-bold block">Risco Inerente</span>
              <span class="text-sm font-extrabold text-blue-900">{{ calculo.risco_inerente !== null ? calculo.risco_inerente : '-' }}</span>
              <span class="text-[9px] text-gray-500 block">P × I</span>
            </div>
            <div class="p-1.5 bg-gray-50/70 rounded border border-gray-200">
              <span class="text-[9px] uppercase text-gray-500 font-bold block">Fator de Mitigação</span>
              <span class="text-sm font-extrabold text-gray-900">{{ calculo.fator_mitigacao }}</span>
              <span class="text-[9px] text-gray-600 block truncate">{{ nivelControleSelecionado?.rotulo || 'Inexistente' }}</span>
            </div>
          </div>

          <div class="p-2 rounded border flex items-center justify-between"
               :class="calculo.acima_apetite ? 'bg-rose-50 border-rose-300 text-rose-950' : 'bg-emerald-50 border-emerald-300 text-emerald-950'">
            <div>
              <span class="text-[9px] font-bold uppercase tracking-wider block">
                {{ calculo.acima_apetite ? '⚠️ ACIMA DO APETITE A RISCO (> 7,99)' : '🛡️ DENTRO DO APETITE A RISCO (≤ 7,99)' }}
              </span>
              <p class="text-[11px] mt-0.5">
                {{ calculo.acima_apetite ? 'Este risco ultrapassa a tolerância da organização e exige tratamento compulsório (Plano de Ação e Contingência).' : 'Este risco está dentro da tolerância institucional. Tratamento complementar pode ser adotado voluntariamente.' }}
              </p>
            </div>
            <div class="text-right pl-3 shrink-0">
              <span class="text-[10px] uppercase font-bold block">Risco Residual:</span>
              <span class="text-xl font-black">{{ calculo.risco_residual !== null ? calculo.risco_residual : '-' }}</span>
              <span class="text-[9px] uppercase font-bold block">({{ calculo.classificacao }})</span>
            </div>
          </div>

          <!-- Controles Internos Existentes -->
          <div>
            <span class="font-bold text-gray-700 block mb-0.5 text-[11px]">Controles Internos Existentes Registrados:</span>
            <div v-if="avaliacao.controles.length === 0" class="text-gray-400 italic text-[11px]">
              Nenhum controle formal associado (Nível Inexistente / Fator de Mitigação 1.0).
            </div>
            <ol v-else class="list-decimal pl-5 space-y-0.5 text-gray-800 text-[11px]">
              <li v-for="(c, cIdx) in avaliacao.controles" :key="cIdx">
                {{ c.descricao_controle }}
              </li>
            </ol>
          </div>
        </div>
      </div>

      <!-- 5. Planos de Ação e Contingência -->
      <div class="bloco-impressao mb-3 border border-gray-300 rounded-md">
        <div class="bg-gray-100 px-3 py-1 border-b border-gray-300 font-bold text-xs uppercase text-gray-800 flex justify-between">
          <span>5. Tratamento, Planos de Ação e Contingência</span>
          <span class="text-[10px] font-normal text-gray-600">Etapa 5</span>
        </div>
        <div class="p-2.5 text-xs space-y-3">
          <!-- Tabela de Planos de Ação -->
          <div>
            <h4 class="font-bold text-gray-800 uppercase text-[11px] mb-1">Planos de Ação</h4>
            <div v-if="evento.planos_acao.length === 0" class="text-gray-400 italic bg-gray-50 p-2 rounded border text-[11px]">
              Nenhum plano de ação cadastrado.
            </div>
            <table v-else class="w-full text-left border-collapse border border-gray-300 text-[10px] table-fixed">
              <thead>
                <tr class="bg-gray-100 border-b border-gray-300">
                  <th class="p-1 border-r border-gray-300 font-bold w-[5%] text-center">#</th>
                  <th class="p-1 border-r border-gray-300 font-bold w-[15%]">Tipo</th>
                  <th class="p-1 border-r border-gray-300 font-bold w-[32%]">O que fazer?</th>
                  <th class="p-1 border-r border-gray-300 font-bold w-[26%]">Como?</th>
                  <th class="p-1 border-r border-gray-300 font-bold w-[12%]">Quem?</th>
                  <th class="p-1 font-bold w-[10%]">Prazo</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200">
                <tr v-for="(pa, paIdx) in evento.planos_acao" :key="paIdx">
                  <td class="p-1 border-r border-gray-200 text-center font-bold">{{ paIdx + 1 }}</td>
                  <td class="p-1 border-r border-gray-200 font-semibold">{{ pa.tipo_resposta }}</td>
                  <td class="p-1 border-r border-gray-200">{{ pa.o_que }}</td>
                  <td class="p-1 border-r border-gray-200">{{ pa.como }}</td>
                  <td class="p-1 border-r border-gray-200">{{ pa.quem }}</td>
                  <td class="p-1">{{ pa.data_inicio ? `${pa.data_inicio} até ${pa.data_termino}` : '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Tabela de Contingência -->
          <div>
            <div class="flex items-center gap-2 mb-1">
              <h4 class="font-bold text-gray-800 uppercase text-[11px]">Planos de Contingência</h4>
              <span class="px-1.5 py-0.2 rounded text-[9px] font-bold bg-gray-100 text-gray-600 border border-gray-200">
                OPCIONAL
              </span>
            </div>
            <div v-if="evento.planos_contingencia.length === 0" class="text-gray-400 italic bg-gray-50 p-2 rounded border text-[11px]">
              Nenhum plano de contingência cadastrado.
            </div>
            <table v-else class="w-full text-left border-collapse border border-gray-300 text-[10px] table-fixed">
              <thead>
                <tr class="bg-gray-100 border-b border-gray-300">
                  <th class="p-1 border-r border-gray-300 font-bold w-[5%] text-center">#</th>
                  <th class="p-1 border-r border-gray-300 font-bold w-[28%]">Gatilho (Trigger)</th>
                  <th class="p-1 border-r border-gray-300 font-bold w-[17%]">Responsável</th>
                  <th class="p-1 border-r border-gray-300 font-bold w-[25%]">O que fazer?</th>
                  <th class="p-1 font-bold w-[25%]">Como agir?</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200">
                <tr v-for="(pc, pcIdx) in evento.planos_contingencia" :key="pcIdx">
                  <td class="p-1 border-r border-gray-200 text-center font-bold">{{ pcIdx + 1 }}</td>
                  <td class="p-1 border-r border-gray-200 font-semibold text-rose-900">{{ pc.gatilho }}</td>
                  <td class="p-1 border-r border-gray-200">{{ pc.responsavel }}</td>
                  <td class="p-1 border-r border-gray-200">{{ pc.o_que }}</td>
                  <td class="p-1">{{ pc.como }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Assinaturas e Homologação -->
      <div class="bloco-impressao mt-4 pt-4 border-t border-gray-300 grid grid-cols-2 gap-10 text-center text-xs">
        <div>
          <div class="border-b border-gray-400 mb-1 pb-6"></div>
          <p class="font-bold text-gray-800 text-[11px]">Responsável pelo Mapeamento</p>
          <p class="text-[10px] text-gray-500">{{ unidadeSelecionada ? unidadeSelecionada.nome : 'Gestor da Unidade Organizacional' }}</p>
        </div>
        <div>
          <div class="border-b border-gray-400 mb-1 pb-6"></div>
          <p class="font-bold text-gray-800 text-[11px]">UGERC / Governança Institucional</p>
          <p class="text-[10px] text-gray-500">Unidade de Gestão de Riscos e Controles Internos - HC-UFPE</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '../../services/api';
import MatrizRisco5x5 from '../../components/riscos/MatrizRisco5x5.vue';

const route = useRoute();
const router = useRouter();

const etapaAtual = ref(1);
const salvando = ref(false);
const popupAtivo = ref<string | null>(null);
const etapa3Avancada = ref(false);
const processoCarregadoFicha = ref<any>(null);

function togglePopup(tipo: string) {
  popupAtivo.value = popupAtivo.value === tipo ? null : tipo;
}

function irParaEtapa(id: number) {
  if (etapaAtual.value === 3 && id > 3) {
    etapa3Avancada.value = true;
  }
  etapaAtual.value = id;
}

function avancarEtapa() {
  if (etapaAtual.value === 3) {
    etapa3Avancada.value = true;
  }
  if (etapaAtual.value < 5) {
    etapaAtual.value += 1;
  }
}

function voltarEtapa() {
  if (etapaAtual.value > 1) {
    etapaAtual.value -= 1;
  }
}

const etapas = [
  { id: 1, nome: 'Contexto & Processo' },
  { id: 2, nome: 'Identificação' },
  { id: 3, nome: 'Avaliação & Controles' },
  { id: 4, nome: 'Matriz de Riscos' },
  { id: 5, nome: 'Planos de Ação' }
];

const unidades = ref<any[]>([]);
const macroprocessos = ref<any[]>([]);
const processosOutrosCadastrados = ref<any[]>([]);
const pilares = ref<any[]>([]);

// Dropdown e Pesquisa de Unidade Organizacional
const unidadeDropdownRef = ref<HTMLElement | null>(null);
const unidadeSearchInputRef = ref<HTMLInputElement | null>(null);
const unidadeDropdownAberto = ref(false);
const unidadeSearchQuery = ref('');
const feedbackMensagem = ref<string | null>(null);

// Dropdown e Pesquisa de Processos
const dropdownRef = ref<HTMLElement | null>(null);
const searchInputRef = ref<HTMLInputElement | null>(null);
const dropdownAberto = ref(false);
const searchQuery = ref('');

function normalizarTexto(txt: string) {
  return (txt || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();
}

const unidadeSelecionada = computed(() => {
  if (!form.unidade_id) return null;
  return unidades.value.find((u: any) => u.id === form.unidade_id) || null;
});

const unidadesFiltradas = computed(() => {
  const q = normalizarTexto(unidadeSearchQuery.value.trim());
  if (!q) return unidades.value;
  return unidades.value.filter((u: any) =>
    normalizarTexto(u.nome).includes(q) || (u.sigla && normalizarTexto(u.sigla).includes(q))
  );
});

function toggleUnidadeDropdown() {
  unidadeDropdownAberto.value = !unidadeDropdownAberto.value;
  if (unidadeDropdownAberto.value) {
    unidadeSearchQuery.value = '';
    nextTick(() => {
      unidadeSearchInputRef.value?.focus();
    });
  }
}

async function selecionarUnidade(u: any) {
  form.unidade_id = u.id;
  unidadeDropdownAberto.value = false;
  unidadeSearchQuery.value = '';
  await onUnidadeChange();
}

function limparSelecaoUnidade() {
  form.unidade_id = null;
  form.processo_id = null;
  form.processo_outro = '';
  macroprocessos.value = [];
  processosOutrosCadastrados.value = [];
}

const pilarSelecionado = computed(() => {
  if (!form.pilar_estrategico_id) return null;
  return pilares.value.find((p: any) => p.id === form.pilar_estrategico_id) || null;
});

const categoriaSelecionada = computed(() => {
  return categoriasRiscoGuia.find(c => c.valor === evento.categoria) || null;
});

const dataHoraAtual = computed(() => {
  return new Date().toLocaleString('pt-BR');
});

function imprimirFichaCompleta() {
  window.print();
}

const processosOutrosFiltrados = computed(() => {
  const q = normalizarTexto(searchQuery.value.trim());
  if (!q) return processosOutrosCadastrados.value;
  return processosOutrosCadastrados.value.filter((po: any) =>
    normalizarTexto(po.nome).includes(q) || (po.unidade_nome && normalizarTexto(po.unidade_nome).includes(q))
  );
});

const macroprocessosFiltrados = computed(() => {
  const q = normalizarTexto(searchQuery.value.trim());

  const proprios: any[] = [];
  const comuns: any[] = [];
  let outroProcesso: any = null;

  for (const m of macroprocessos.value) {
    if (m.nome === 'Outro') {
      const pOutro = m.processos?.[0] || { id: m.id, nome: 'Outro processo' };
      if (!q || normalizarTexto(pOutro.nome).includes(q) || normalizarTexto(m.nome).includes(q) || normalizarTexto('novo').includes(q)) {
        outroProcesso = {
          ...pOutro,
          macroprocessoNome: 'Outro'
        };
      }
      continue;
    }

    const procsProprios = (m.processos || []).filter((p: any) => !p.is_transversal);
    const procsComuns = (m.processos || []).filter((p: any) => p.is_transversal);

    // Filtra próprios pela busca
    const procsPropriosFiltrados = procsProprios.filter((p: any) => {
      if (!q) return true;
      return normalizarTexto(p.nome).includes(q) || normalizarTexto(m.nome).includes(q);
    });
    if (procsPropriosFiltrados.length > 0) {
      proprios.push({
        id: m.id,
        nome: m.nome,
        processos: procsPropriosFiltrados
      });
    }

    // Filtra comuns pela busca
    const procsComunsFiltrados = procsComuns.filter((p: any) => {
      if (!q) return true;
      return normalizarTexto(p.nome).includes(q) || normalizarTexto(m.nome).includes(q);
    });
    if (procsComunsFiltrados.length > 0) {
      comuns.push({
        id: m.id,
        nome: m.nome,
        processos: procsComunsFiltrados
      });
    }
  }

  const totalProprios = proprios.reduce((acc, m) => acc + m.processos.length, 0);
  const totalComuns = comuns.reduce((acc, m) => acc + m.processos.length, 0);

  return {
    proprios,
    comuns,
    outroProcesso,
    totalProprios,
    totalComuns,
    totalFiltrados: totalProprios + totalComuns + (outroProcesso ? 1 : 0)
  };
});

const processoSelecionado = computed(() => {
  if (!form.processo_id) return null;
  for (const m of macroprocessos.value) {
    const p = m.processos?.find((x: any) => x.id === form.processo_id);
    if (p) {
      return {
        ...p,
        macroprocessoNome: m.nome
      };
    }
  }
  if (processoCarregadoFicha.value && processoCarregadoFicha.value.id === form.processo_id) {
    return processoCarregadoFicha.value;
  }
  return null;
});

const isProcessoOutro = computed(() => {
  if (form.processo_outro && form.processo_outro.trim()) return true;
  if (!form.processo_id) return false;
  for (const m of macroprocessos.value) {
    const p = m.processos?.find((x: any) => x.id === form.processo_id);
    if (p && (m.nome === 'Outro' || p.nome === 'Outro processo' || p.nome === 'Outro')) {
      return true;
    }
  }
  return false;
});

function toggleDropdown() {
  if (!form.unidade_id) return;
  dropdownAberto.value = !dropdownAberto.value;
  if (dropdownAberto.value) {
    searchQuery.value = '';
    nextTick(() => {
      searchInputRef.value?.focus();
    });
  }
}

function limparSelecaoProcesso() {
  form.processo_id = null;
  form.processo_outro = '';
  searchQuery.value = '';
}

function selecionarProcesso(p: any) {
  form.processo_id = p.id;
  dropdownAberto.value = false;
  searchQuery.value = '';
  if (p.permite_projeto) {
    form.possui_projeto = true;
  }
  if (!isProcessoOutro.value) {
    form.processo_outro = '';
  }
}

function selecionarProcessoOutroCadastrado(po: any) {
  if (macroprocessosFiltrados.value.outroProcesso) {
    selecionarProcesso(macroprocessosFiltrados.value.outroProcesso);
  }
  form.processo_outro = po.nome;
}

function handleClickOutside(event: MouseEvent) {
  const el = dropdownRef.value;
  if (el && !el.contains(event.target as Node)) {
    dropdownAberto.value = false;
  }
  const uEl = unidadeDropdownRef.value;
  if (uEl && !uEl.contains(event.target as Node)) {
    unidadeDropdownAberto.value = false;
  }
  popupAtivo.value = null;
}

const form = reactive({
  id: null as number | null,
  unidade_id: null as number | null,
  processo_id: null as number | null,
  processo_outro: '',
  possui_projeto: false,
  nome_projeto: '',
  pilar_estrategico_id: null as number | null,
  entrega_processo: '',
  status: 'RASCUNHO',
  versao: 1,
  tag_versao: 'v1.0 (Original)',
  submetido_em: null as string | null,
  criado_em: null as string | null,
  criado_por: null as any
});

const categoriasRiscoGuia = [
  {
    valor: 'ACIDENTE',
    nome: 'Acidente',
    descricao: 'Situações perigosas ao trabalhador (máquinas sem proteção, trabalho em altura, eletricidade, iluminação inadequada, incêndio).'
  },
  {
    valor: 'BIOLOGICO',
    nome: 'Biológico',
    descricao: 'Exposição a bactérias, vírus, fungos e protozoários inerentes às atividades hospitalares e assistenciais.'
  },
  {
    valor: 'COMPLIANCE',
    nome: 'Compliance',
    descricao: 'Cumprimento de leis trabalhistas, sanitárias, normas e regras internas da Ebserh, combate a fraudes e corrupção.'
  },
  {
    valor: 'ERGONOMICO',
    nome: 'Ergonômico',
    descricao: 'Postura inadequada, levantamento/transporte de peso, jornadas prolongadas e sobrecarga/estresse físico.'
  },
  {
    valor: 'ESTRATEGICO',
    nome: 'Estratégico',
    descricao: 'Ameaças externas às diretrizes estratégicas institucionais, decisões dos gestores, cenários políticos e econômicos.'
  },
  {
    valor: 'FINANCEIRO',
    nome: 'Financeiro',
    descricao: 'Prejuízos à execução orçamentária, inadimplência de fornecedores, dependência orçamentária e perda de recursos.'
  },
  {
    valor: 'FISICO',
    nome: 'Físico',
    descricao: 'Exposição a ruído, calor, frio, radiações ionizantes/não-ionizantes, pressões anormais e vibrações.'
  },
  {
    valor: 'OPERACIONAL',
    nome: 'Operacional',
    descricao: 'Falhas em processos internos, equipamentos sem manutenção, problemas de logística, gestão de pessoas e retrabalho.'
  },
  {
    valor: 'QUIMICO',
    nome: 'Químico',
    descricao: 'Substâncias, poeiras, gases ou vapores tóxicos absorvidos por via respiratória, dérmica ou ingestão.'
  },
  {
    valor: 'REPUTACAO',
    nome: 'Reputação',
    descricao: 'Perda de credibilidade e danos à imagem institucional do HC-UFPE e da Ebserh perante a sociedade e usuários.'
  },
  {
    valor: 'SEGURANCA_INFORMACAO',
    nome: 'Segurança da Informação',
    descricao: 'Vulnerabilidades no controle de acesso a dados sensíveis (assistenciais/ensino/administrativos), incidentes cibernéticos e LGPD.'
  }
];

const escalaProbabilidade = [
  { peso: 1, rotulo: 'Muito baixa', descricao: 'Evento pode ocorrer apenas em circunstâncias excepcionais' },
  { peso: 2, rotulo: 'Baixa', descricao: 'Evento pode ocorrer apenas em algum momento' },
  { peso: 3, rotulo: 'Média', descricao: 'Evento deve ocorrer em algum momento' },
  { peso: 4, rotulo: 'Alta', descricao: 'Evento provavelmente ocorra na maioria das circunstâncias' },
  { peso: 5, rotulo: 'Muito Alta', descricao: 'Evento esperado que ocorra na maioria das circunstâncias' }
];

const escalaImpacto = [
  { peso: 1, rotulo: 'Muito Baixo', descricao: 'Mínimo impacto nos objetivos do processo' },
  { peso: 2, rotulo: 'Baixo', descricao: 'Pequeno impacto nos objetivos do processo' },
  { peso: 3, rotulo: 'Médio', descricao: 'Moderado impacto nos objetivos do processo' },
  { peso: 4, rotulo: 'Alto', descricao: 'Significativo impacto nos objetivos do processo' },
  { peso: 5, rotulo: 'Muito Alto', descricao: 'Catastrófico impacto nos objetivos do processo' }
];

const escalaCoresSuaves: Record<number, { normal: string; ativo: string; badge: string }> = {
  1: {
    normal: 'bg-emerald-50/60 text-emerald-800 border-emerald-200/80 hover:bg-emerald-100/70',
    ativo: 'bg-emerald-200 text-emerald-950 font-bold border-emerald-400 ring-2 ring-emerald-300 shadow-sm',
    badge: 'bg-emerald-100 text-emerald-900 border border-emerald-300'
  },
  2: {
    normal: 'bg-lime-50/60 text-lime-800 border-lime-200/80 hover:bg-lime-100/70',
    ativo: 'bg-lime-200 text-lime-950 font-bold border-lime-400 ring-2 ring-lime-300 shadow-sm',
    badge: 'bg-lime-100 text-lime-900 border border-lime-300'
  },
  3: {
    normal: 'bg-amber-50/60 text-amber-800 border-amber-200/80 hover:bg-amber-100/70',
    ativo: 'bg-amber-200 text-amber-950 font-bold border-amber-400 ring-2 ring-amber-300 shadow-sm',
    badge: 'bg-amber-100 text-amber-900 border border-amber-300'
  },
  4: {
    normal: 'bg-orange-50/60 text-orange-800 border-orange-200/80 hover:bg-orange-100/70',
    ativo: 'bg-orange-200 text-orange-950 font-bold border-orange-400 ring-2 ring-orange-300 shadow-sm',
    badge: 'bg-orange-100 text-orange-900 border border-orange-300'
  },
  5: {
    normal: 'bg-rose-50/60 text-rose-800 border-rose-200/80 hover:bg-rose-100/70',
    ativo: 'bg-rose-200 text-rose-950 font-bold border-rose-400 ring-2 ring-rose-300 shadow-sm',
    badge: 'bg-rose-100 text-rose-900 border border-rose-300'
  }
};

function getBotaoEscalaClass(valor: number, selecionado: number | null) {
  const conf = escalaCoresSuaves[valor];
  if (!conf) return 'bg-white text-gray-700 border-gray-300';
  return selecionado === valor ? conf.ativo : conf.normal;
}

function getBadgeEscalaClass(valor: number | null) {
  if (!valor) return 'bg-blue-100 text-blue-800';
  return escalaCoresSuaves[valor]?.badge || 'bg-blue-100 text-blue-800';
}

const niveisControleTabela3 = [
  {
    valor: 'INEXISTENTE',
    rotulo: 'Inexistente',
    fnc: 1.0,
    classificacaoTcu: 'Muito Alto',
    badge: 'bg-rose-100 text-rose-800 border border-rose-300',
    definicao: 'Controles inexistentes, mal desenhados ou mal implementados, isto é, não funcionais.'
  },
  {
    valor: 'FRACO',
    rotulo: 'Fraco',
    fnc: 0.8,
    classificacaoTcu: 'Alto',
    badge: 'bg-orange-100 text-orange-800 border border-orange-300',
    definicao: 'Controles têm abordagens ad hoc, tendem a ser aplicados caso a caso, a responsabilidade é individual, havendo elevado grau de confiança no conhecimento das pessoas.'
  },
  {
    valor: 'MEDIANO',
    rotulo: 'Mediano',
    fnc: 0.6,
    classificacaoTcu: 'Médio',
    badge: 'bg-amber-100 text-amber-800 border border-amber-300',
    definicao: 'Controles implementados mitigam alguns aspectos do risco, mas não contemplam todos os aspectos relevantes do risco devido a deficiências no desenho ou nas ferramentas utilizadas.'
  },
  {
    valor: 'SATISFATORIO',
    rotulo: 'Satisfatório',
    fnc: 0.4,
    classificacaoTcu: 'Baixo',
    badge: 'bg-blue-100 text-blue-800 border border-blue-300',
    definicao: 'Controles implementados e sustentados por ferramentas adequadas e, embora passíveis de aperfeiçoamento, mitigam o risco satisfatoriamente.'
  },
  {
    valor: 'FORTE',
    rotulo: 'Forte',
    fnc: 0.2,
    classificacaoTcu: 'Muito Baixo',
    badge: 'bg-emerald-100 text-emerald-800 border border-emerald-300',
    definicao: 'Controles implementados podem ser considerados a "melhor prática", mitigando todos os aspectos relevantes do risco.'
  }
];

const evento = reactive({
  categoria: 'OPERACIONAL',
  causa: '',
  descricao_evento: '',
  consequencia: '',
  planos_acao: [] as any[],
  planos_contingencia: [] as any[]
});

const avaliacao = reactive({
  probabilidade: null as number | null,
  impacto: null as number | null,
  nivel_controle: 'INEXISTENTE',
  controles: [] as { descricao_controle: string }[]
});

const calculo = reactive({
  risco_inerente: null as number | null,
  fator_mitigacao: 1.0,
  risco_residual: null as number | null,
  classificacao: '-',
  acima_apetite: false
});

const probabilidadeSelecionada = computed(() => escalaProbabilidade.find(p => p.peso === avaliacao.probabilidade));
const impactoSelecionado = computed(() => escalaImpacto.find(i => i.peso === avaliacao.impacto));
const nivelControleSelecionado = computed(() => niveisControleTabela3.find(n => n.valor === avaliacao.nivel_controle));


function recalcular() {
  const p = avaliacao.probabilidade;
  const i = avaliacao.impacto;
  const nivelObj = niveisControleTabela3.find(n => n.valor === avaliacao.nivel_controle) || niveisControleTabela3[0];
  const fator = nivelObj.fnc;
  calculo.fator_mitigacao = fator;

  if (!p || !i) {
    calculo.risco_inerente = null;
    calculo.risco_residual = null;
    calculo.classificacao = '-';
    calculo.acima_apetite = false;
    return;
  }

  const inerente = p * i;
  const residual = Math.round(inerente * fator);

  let classif = 'BAIXO';
  if (residual <= 2) classif = 'BAIXO';
  else if (residual <= 7) classif = 'MEDIO';
  else if (residual <= 14) classif = 'ALTO';
  else classif = 'EXTREMO';

  calculo.risco_inerente = inerente;
  calculo.risco_residual = residual;
  calculo.classificacao = classif;
  calculo.acima_apetite = (residual > 7);
}

function onNivelControleChange(novoNivel: string) {
  avaliacao.nivel_controle = novoNivel;
  if (novoNivel === 'INEXISTENTE') {
    avaliacao.controles = [];
  }
  recalcular();
}




function adicionarControle() {
  avaliacao.controles.push({ descricao_controle: '' });
  recalcular();
}

function removerControle(index: number) {
  avaliacao.controles.splice(index, 1);
  recalcular();
}

function adicionarPlanoAcao() {
  evento.planos_acao.push({
    tipo_resposta: 'MITIGAR',
    o_que: '',
    como: '',
    quem: '',
    data_inicio: '',
    data_termino: '',
    status: 'PLANEJADO'
  });
}

function removerPlanoAcao(index: number) {
  evento.planos_acao.splice(index, 1);
}

function adicionarPlanoContingencia() {
  evento.planos_contingencia.push({
    gatilho: '',
    o_que: '',
    como: '',
    responsavel: ''
  });
}

function removerPlanoContingencia(index: number) {
  evento.planos_contingencia.splice(index, 1);
}

function getClassificacaoBadge(classif: string) {
  switch (classif) {
    case 'BAIXO': return 'bg-emerald-100 text-emerald-800';
    case 'MEDIO': return 'bg-amber-100 text-amber-800';
    case 'ALTO': return 'bg-orange-100 text-orange-800';
    default: return 'bg-rose-100 text-rose-800';
  }
}

async function carregarProcessos(unidadeId?: number | null, incluirProcessoId?: number | null) {
  try {
    const params: any = {};
    if (unidadeId) params.unidade_id = unidadeId;
    if (incluirProcessoId) params.incluir_processo_id = incluirProcessoId;
    const [resP, resOutros] = await Promise.all([
      api.get('/api/processos', { params }),
      api.get('/api/processos/outros', { params: unidadeId ? { unidade_id: unidadeId } : {} })
    ]);
    macroprocessos.value = resP.data;
    processosOutrosCadastrados.value = resOutros.data || [];
  } catch (err) {
    console.error('Erro ao carregar processos:', err);
  }
}

const etapa1Valida = computed(() => {
  if (!form.unidade_id || !form.processo_id) return false;
  if (!form.entrega_processo || !form.entrega_processo.trim()) return false;
  if (isProcessoOutro.value && (!form.processo_outro || !form.processo_outro.trim())) return false;
  if (form.possui_projeto) {
    if (!form.nome_projeto || !form.nome_projeto.trim() || !form.pilar_estrategico_id) return false;
  }
  return true;
});

const etapa2Valida = computed(() => {
  if (!etapa1Valida.value) return false;
  if (!evento.categoria || !evento.categoria.trim()) return false;
  if (!evento.causa || !evento.causa.trim()) return false;
  if (!evento.descricao_evento || !evento.descricao_evento.trim()) return false;
  if (!evento.consequencia || !evento.consequencia.trim()) return false;
  return true;
});

const etapa3Valida = computed(() => {
  if (!etapa2Valida.value) return false;
  if (!avaliacao.probabilidade || avaliacao.probabilidade < 1 || avaliacao.probabilidade > 5) return false;
  if (!avaliacao.impacto || avaliacao.impacto < 1 || avaliacao.impacto > 5) return false;
  if (avaliacao.nivel_controle !== 'INEXISTENTE') {
    if (avaliacao.controles.length === 0) return false;
    for (const c of avaliacao.controles) {
      if (!c.descricao_controle || !c.descricao_controle.trim()) return false;
    }
  }
  return true;
});

const etapa4Valida = computed(() => {
  return etapa3Valida.value && etapa3Avancada.value && calculo.risco_residual !== null && calculo.risco_residual > 0;
});

const etapa5Valida = computed(() => {
  if (!etapa4Valida.value) return false;

  const isRiscoAltoOuExtremo = calculo.classificacao === 'ALTO' || calculo.classificacao === 'EXTREMO';

  // Para riscos altos ou extremos, exige no mínimo 1 plano de ação adicionado
  if (isRiscoAltoOuExtremo) {
    if (evento.planos_acao.length === 0) return false;
  }

  // Valida campos dos planos de ação existentes
  for (const pa of evento.planos_acao) {
    if (!pa.o_que || !pa.o_que.trim()) return false;
    if (!pa.como || !pa.como.trim()) return false;
    if (!pa.quem || !pa.quem.trim()) return false;
    if (!pa.data_inicio || !pa.data_inicio.trim()) return false;
    if (!pa.data_termino || !pa.data_termino.trim()) return false;
  }

  // Planos de contingência não são obrigatórios para submissão; se existirem, valida campos
  for (const pc of evento.planos_contingencia) {
    if (!pc.gatilho || !pc.gatilho.trim()) return false;
    if (!pc.responsavel || !pc.responsavel.trim()) return false;
    if (!pc.o_que || !pc.o_que.trim()) return false;
    if (!pc.como || !pc.como.trim()) return false;
  }

  return true;
});

const podeEditarFicha = ref(true);
const snapshotOriginal = ref('');

function formatarDataHora(dtStr?: string | null) {
  if (!dtStr) return '-';
  try {
    const d = new Date(dtStr);
    return d.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
  } catch {
    return dtStr;
  }
}

function gerarSnapshot() {
  return JSON.stringify({
    unidade_id: form.unidade_id,
    processo_id: form.processo_id,
    processo_outro: form.processo_outro?.trim() || '',
    possui_projeto: form.possui_projeto,
    nome_projeto: form.nome_projeto?.trim() || '',
    pilar_estrategico_id: form.pilar_estrategico_id,
    entrega_processo: form.entrega_processo?.trim() || '',
    categoria: evento.categoria,
    causa: evento.causa?.trim() || '',
    descricao_evento: evento.descricao_evento?.trim() || '',
    consequencia: evento.consequencia?.trim() || '',
    probabilidade: avaliacao.probabilidade,
    impacto: avaliacao.impacto,
    nivel_controle: avaliacao.nivel_controle,
    controles: avaliacao.controles.map(c => c.descricao_controle?.trim() || ''),
    planos_acao: evento.planos_acao.map(pa => ({
      tipo_resposta: pa.tipo_resposta,
      o_que: pa.o_que?.trim() || '',
      como: pa.como?.trim() || '',
      quem: pa.quem?.trim() || '',
      data_inicio: pa.data_inicio,
      data_termino: pa.data_termino,
      status: pa.status
    })),
    planos_contingencia: evento.planos_contingencia.map(pc => ({
      gatilho: pc.gatilho?.trim() || '',
      responsavel: pc.responsavel?.trim() || '',
      o_que: pc.o_que?.trim() || '',
      como: pc.como?.trim() || ''
    }))
  });
}

const formAlterado = computed(() => {
  if (!snapshotOriginal.value) return false;
  return snapshotOriginal.value !== gerarSnapshot();
});

const podeSalvarRascunho = computed(() => {
  if (!podeEditarFicha.value) return false;
  return formAlterado.value;
});

const tooltipSalvarRascunho = computed(() => {
  if (!podeEditarFicha.value) {
    return 'Modo Somente Leitura: você não possui permissão para editar esta ficha.';
  }
  if (!formAlterado.value) {
    return 'Nenhuma alteração foi realizada na ficha. Altere algum campo para habilitar o salvamento do rascunho.';
  }
  return 'Salvar alterações realizadas no rascunho da ficha';
});

const statusEtapas = computed<Record<number, boolean>>(() => ({
  1: etapa1Valida.value,
  2: etapa2Valida.value,
  3: etapa3Valida.value,
  4: etapa4Valida.value,
  5: etapa5Valida.value
}));

const podeSubmeter = computed(() => {
  return etapa1Valida.value && etapa2Valida.value && etapa3Valida.value && etapa4Valida.value && etapa5Valida.value;
});

const podeSubmeterBotao = computed(() => {
  if (!podeEditarFicha.value) return false;
  if (!podeSubmeter.value) return false;
  // Ao editar uma ficha existente, o botão de submeter só fica disponível quando o usuário avança até a etapa 5
  if (form.id && etapaAtual.value !== 5) {
    return false;
  }
  // Se a ficha já estiver submetida, só reativa a opção de submissão se algum campo foi alterado
  if (form.status === 'SUBMETIDO' && !formAlterado.value) {
    return false;
  }
  return true;
});

const tooltipSubmeter = computed(() => {
  if (!podeEditarFicha.value) {
    return 'Modo Somente Leitura: apenas o gestor da unidade ou Administrador pode editar/submeter.';
  }
  if (form.id && etapaAtual.value !== 5) {
    return 'Por segurança, avance até a Etapa 5 para revisar todas as etapas antes de submeter à UGERC.';
  }
  if (!podeSubmeter.value) {
    return 'Preencha as etapas obrigatórias para habilitar: ' + textoPendencias.value;
  }
  if (form.status === 'SUBMETIDO' && !formAlterado.value) {
    return 'Ficha já submetida. Para submeter uma nova versão à UGERC, altere ao menos um campo.';
  }
  return 'Submeter mapeamento à UGERC';
});

const textoPendencias = computed(() => {
  const p: string[] = [];
  if (!etapa1Valida.value) p.push('Etapa 1 (Contexto & Processo)');
  if (!etapa2Valida.value) p.push('Etapa 2 (Identificação do Risco)');
  if (!etapa3Valida.value) p.push('Etapa 3 (Avaliação & Controles)');
  if (!etapa4Valida.value) p.push('Etapa 4 (Matriz de Riscos - avance a partir da etapa 3)');
  if (!etapa5Valida.value) {
    const isAlto = calculo.classificacao === 'ALTO' || calculo.classificacao === 'EXTREMO';
    p.push(isAlto ? 'Etapa 5 (Plano de Ação obrigatório para riscos altos/extremos)' : 'Etapa 5 (Planos de Ação)');
  }
  return p.join(', ');
});

async function onUnidadeChange() {
  if (form.unidade_id) {
    await carregarProcessos(form.unidade_id, form.processo_id);
    let existe = false;
    for (const m of macroprocessos.value) {
      if (m.processos?.some((p: any) => p.id === form.processo_id)) {
        existe = true;
        break;
      }
    }
    if (!existe && (!processoCarregadoFicha.value || processoCarregadoFicha.value.id !== form.processo_id)) {
      form.processo_id = null;
    }
  } else {
    macroprocessos.value = [];
    processosOutrosCadastrados.value = [];
    form.processo_id = null;
  }
}

async function carregarAuxiliares() {
  try {
    const [resU, resPil] = await Promise.all([
      api.get('/api/unidades?apenas_mapeamento=true'),
      api.get('/api/processos/pilares-estrategicos')
    ]);
    unidades.value = resU.data;
    pilares.value = resPil.data;
    // Se o usuário possui apenas 1 unidade disponível para mapear e for novo risco, auto-seleciona
    if (!form.id && unidades.value.length === 1 && !form.unidade_id) {
      await selecionarUnidade(unidades.value[0]);
    } else if (form.unidade_id) {
      await carregarProcessos(form.unidade_id, form.processo_id);
    }
  } catch (err) {
    console.error('Erro ao carregar dados auxiliares:', err);
  }
}

async function carregarMapeamento(id: number) {
  try {
    const res = await api.get(`/api/riscos/${id}`);
    const data = res.data;
    form.id = data.id;
    form.unidade_id = data.unidade_id;
    form.versao = data.versao || 1;
    form.tag_versao = data.tag_versao || 'v1.0 (Original)';
    form.submetido_em = data.submetido_em || null;
    form.criado_em = data.criado_em || null;
    form.criado_por = data.criado_por || null;
    podeEditarFicha.value = (data.pode_editar !== false);

    // Garante que a unidade da ficha conste na lista de unidades para correta exibição
    if (data.unidade && !unidades.value.some((u: any) => u.id === data.unidade.id)) {
      unidades.value.push(data.unidade);
    }

    // Carrega processos incluindo obrigatoriamente o processo mapeado da ficha
    if (data.unidade_id) {
      await carregarProcessos(data.unidade_id, data.processo_id);
    }
    form.processo_id = data.processo_id;
    form.processo_outro = data.processo_outro || '';
    form.possui_projeto = data.possui_projeto;
    form.nome_projeto = data.nome_projeto || '';
    form.pilar_estrategico_id = data.pilar_estrategico_id;
    form.entrega_processo = data.entrega_processo;
    form.status = data.status;

    // Registra os metadados do processo da ficha para fallback e garantia visual
    if (data.processo || data.processo_nome) {
      processoCarregadoFicha.value = {
        id: data.processo_id,
        nome: data.processo?.nome || data.processo_nome,
        macroprocessoNome: data.processo?.macroprocesso?.nome || data.macroprocesso_nome || 'Processo Hospitalar',
        permite_projeto: data.processo?.permite_projeto || false,
        is_transversal: data.processo?.is_transversal || false
      };

      // Garante que o processo da ficha conste em macroprocessos.value para seleção e checkmark
      let encontrado = false;
      for (const m of macroprocessos.value) {
        if (m.processos?.some((p: any) => p.id === data.processo_id)) {
          encontrado = true;
          break;
        }
      }
      if (!encontrado && data.processo_id) {
        const macroNome = processoCarregadoFicha.value.macroprocessoNome;
        const macroExistente = macroprocessos.value.find((m: any) => m.nome === macroNome);
        const procObj = {
          id: processoCarregadoFicha.value.id,
          nome: processoCarregadoFicha.value.nome,
          is_transversal: processoCarregadoFicha.value.is_transversal,
          permite_projeto: processoCarregadoFicha.value.permite_projeto
        };
        if (macroExistente) {
          if (!macroExistente.processos) macroExistente.processos = [];
          macroExistente.processos.unshift(procObj);
        } else {
          macroprocessos.value.unshift({
            id: -1,
            nome: macroNome,
            processos: [procObj]
          });
        }
      }
    }

    if (data.eventos && data.eventos.length > 0) {
      const ev = data.eventos[0];
      evento.categoria = ev.categoria;
      evento.causa = ev.causa;
      evento.descricao_evento = ev.descricao_evento;
      evento.consequencia = ev.consequencia;
      evento.planos_acao = ev.planos_acao ? JSON.parse(JSON.stringify(ev.planos_acao)) : [];
      evento.planos_contingencia = ev.planos_contingencia ? JSON.parse(JSON.stringify(ev.planos_contingencia)) : [];

      if (ev.avaliacao) {
        avaliacao.probabilidade = ev.avaliacao.probabilidade;
        avaliacao.impacto = ev.avaliacao.impacto;
        avaliacao.nivel_controle = ev.avaliacao.nivel_controle || (ev.avaliacao.fator_mitigacao === 1.0 ? 'INEXISTENTE' : ev.avaliacao.fator_mitigacao === 0.8 ? 'FRACO' : ev.avaliacao.fator_mitigacao === 0.6 ? 'MEDIANO' : ev.avaliacao.fator_mitigacao === 0.4 ? 'SATISFATORIO' : 'FORTE');
        avaliacao.controles = ev.avaliacao.controles ? JSON.parse(JSON.stringify(ev.avaliacao.controles)) : [];
        if (ev.avaliacao.probabilidade && ev.avaliacao.impacto) {
          etapa3Avancada.value = true;
        }
      }
      recalcular();
    }

    nextTick(() => {
      snapshotOriginal.value = gerarSnapshot();
    });
  } catch (err) {
    console.error('Erro ao carregar mapeamento:', err);
  }
}

async function salvar(submeter: boolean) {
  if (!podeEditarFicha.value) {
    alert('Esta ficha está em modo somente leitura para o seu usuário.');
    return;
  }

  if (!submeter) {
    if (!podeSalvarRascunho.value) {
      alert('Nenhuma alteração foi realizada na ficha para salvar.');
      return;
    }
  }

  if (submeter) {
    if (!podeSubmeterBotao.value) {
      if (form.id && etapaAtual.value !== 5) {
        alert('Por segurança, ao editar uma ficha, você deve avançar até a Etapa 5 para revisar o mapeamento antes de submeter à UGERC.');
        etapaAtual.value = 5;
        return;
      }
      if (form.status === 'SUBMETIDO' && !formAlterado.value) {
        alert('Esta ficha já foi submetida à UGERC. Para submeter uma nova versão, faça alguma alteração nos campos.');
        return;
      }
      alert('Atenção: Para submeter à UGERC é necessário que todas as 5 etapas estejam devidamente preenchidas.\n\nPendências encontradas:\n- ' + textoPendencias.value.split(', ').join('\n- '));
      if (!etapa1Valida.value) etapaAtual.value = 1;
      else if (!etapa2Valida.value) etapaAtual.value = 2;
      else if (!etapa3Valida.value) etapaAtual.value = 3;
      else if (!etapa4Valida.value) etapaAtual.value = 4;
      else etapaAtual.value = 5;
      return;
    }
  }

  if (!form.unidade_id) {
    alert('Por favor, informe a Unidade Organizacional na Etapa 1.');
    etapaAtual.value = 1;
    return;
  }

  const novoStatus = submeter ? 'SUBMETIDO' : 'RASCUNHO';

  salvando.value = true;
  try {
    const payload = {
      id: form.id,
      unidade_id: form.unidade_id,
      processo_id: form.processo_id,
      processo_outro: form.processo_outro?.trim() || null,
      possui_projeto: form.possui_projeto,
      nome_projeto: form.nome_projeto,
      pilar_estrategico_id: form.pilar_estrategico_id,
      entrega_processo: form.entrega_processo,
      status: novoStatus,
      eventos: [
        {
          categoria: evento.categoria,
          causa: evento.causa,
          descricao_evento: evento.descricao_evento,
          consequencia: evento.consequencia,
          avaliacao: {
            probabilidade: avaliacao.probabilidade,
            impacto: avaliacao.impacto,
            nivel_controle: avaliacao.nivel_controle,
            fator_mitigacao: calculo.fator_mitigacao,
            controles: avaliacao.nivel_controle !== 'INEXISTENTE' ? avaliacao.controles.map(c => c.descricao_controle) : []
          },

          planos_acao: evento.planos_acao,
          planos_contingencia: evento.planos_contingencia
        }
      ]
    };

    const res = await api.post('/api/riscos', payload);
    form.id = res.data.id;
    form.status = res.data.status;
    if (res.data.versao) form.versao = res.data.versao;
    if (res.data.tag_versao) form.tag_versao = res.data.tag_versao;
    if (res.data.submetido_em) form.submetido_em = res.data.submetido_em;
    if (res.data.criado_em) form.criado_em = res.data.criado_em;
    if (res.data.criado_por) form.criado_por = res.data.criado_por;

    snapshotOriginal.value = gerarSnapshot();

    if (submeter) {
      alert(`Mapeamento submetido à UGERC com sucesso! [${form.tag_versao}]`);
      router.push('/riscos/mapeados');
    } else {
      feedbackMensagem.value = 'Rascunho salvo com sucesso! Você permanece na mesma página para continuar preenchendo.';
      if (route.name === 'novo-risco' || route.path.includes('/novo')) {
        router.replace({ path: `/riscos/${res.data.id}/editar` });
      }
      setTimeout(() => {
        feedbackMensagem.value = null;
      }, 6000);
    }
  } catch (err: any) {
    console.error('Erro ao salvar:', err);
    alert(err.response?.data?.detail || 'Erro ao salvar mapeamento de risco.');
  } finally {
    salvando.value = false;
  }
}


function resetarFormulario() {
  form.id = null;
  form.unidade_id = null;
  form.processo_id = null;
  form.processo_outro = '';
  form.possui_projeto = false;
  form.nome_projeto = '';
  form.pilar_estrategico_id = null;
  form.entrega_processo = '';
  form.status = 'RASCUNHO';
  form.versao = 1;
  form.tag_versao = 'v1.0 (Original)';
  form.submetido_em = null;
  form.criado_em = null;
  form.criado_por = null;
  podeEditarFicha.value = true;
  processoCarregadoFicha.value = null;

  evento.categoria = 'OPERACIONAL';
  evento.causa = '';
  evento.descricao_evento = '';
  evento.consequencia = '';
  evento.planos_acao = [];
  evento.planos_contingencia = [];

  avaliacao.probabilidade = null;
  avaliacao.impacto = null;
  avaliacao.nivel_controle = 'INEXISTENTE';
  avaliacao.controles = [];

  calculo.risco_inerente = null;
  calculo.fator_mitigacao = 1.0;
  calculo.risco_residual = null;
  calculo.classificacao = '-';
  calculo.acima_apetite = false;

  etapaAtual.value = 1;
  etapa3Avancada.value = false;
}

onMounted(async () => {
  document.addEventListener('click', handleClickOutside);
  const idParam = route.params.id;
  if (idParam) {
    form.id = Number(idParam);
    await carregarAuxiliares();
    await carregarMapeamento(Number(idParam));
  } else {
    await carregarAuxiliares();
    recalcular();
    nextTick(() => {
      snapshotOriginal.value = gerarSnapshot();
    });
  }
});

watch(
  () => route.params.id,
  async (novoId) => {
    if (novoId) {
      if (Number(novoId) !== form.id) {
        form.id = Number(novoId);
        await carregarMapeamento(Number(novoId));
      }
    } else {
      resetarFormulario();
      await carregarAuxiliares();
      recalcular();
      nextTick(() => {
        snapshotOriginal.value = gerarSnapshot();
      });
    }
  }
);

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<style scoped>
@keyframes pulse-ring-emerald {
  0%, 100% {
    box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.35), 0 4px 12px -2px rgba(16, 185, 129, 0.15);
    border-color: rgba(52, 211, 153, 0.7);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(16, 185, 129, 0.15), 0 8px 18px -2px rgba(16, 185, 129, 0.25);
    border-color: rgba(16, 185, 129, 1);
  }
}

@keyframes pulse-ring-rose {
  0%, 100% {
    box-shadow: 0 0 0 2px rgba(244, 63, 94, 0.4), 0 4px 12px -2px rgba(244, 63, 94, 0.2);
    border-color: rgba(251, 113, 133, 0.7);
  }
  50% {
    box-shadow: 0 0 0 7px rgba(244, 63, 94, 0.18), 0 8px 20px -2px rgba(244, 63, 94, 0.3);
    border-color: rgba(244, 63, 94, 1);
  }
}

.card-apetite-emerald {
  animation: pulse-ring-emerald 2.8s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

.card-apetite-rose {
  animation: pulse-ring-rose 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@media print {
  @page {
    size: A4 portrait;
    margin: 8mm 7mm;
  }

  *, *:before, *:after {
    box-sizing: border-box !important;
  }

  html, body {
    background: #ffffff !important;
    color: #111827 !important;
    height: auto !important;
    min-height: auto !important;
    overflow: visible !important;
    font-size: 9.5pt;
    line-height: 1.3;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
  }

  .print\:hidden {
    display: none !important;
  }

  #secao-relatorio-impressao {
    display: block !important;
    position: static !important;
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
    box-sizing: border-box !important;
  }

  .bloco-impressao {
    break-inside: avoid !important;
    page-break-inside: avoid !important;
    box-sizing: border-box !important;
    margin-bottom: 10px !important;
  }

  table {
    width: 100% !important;
    table-layout: fixed !important;
    box-sizing: border-box !important;
    page-break-inside: auto;
    word-break: break-word !important;
  }

  tr {
    break-inside: avoid !important;
    page-break-inside: avoid !important;
  }

  td, th {
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
  }
}
</style>
