<template>
  <div class="max-w-6xl mx-auto space-y-6 pb-12">
    <!-- Header do Formulário -->
    <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex justify-between items-center">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Mapeamento de Riscos por Processo</h2>
        <p class="text-xs text-gray-500 mt-1">Conforme Guia Prático GU.UGERC.001 (HC-UFPE / EBSERH)</p>
      </div>
      <div class="flex items-center space-x-3">
        <span 
          :class="form.status === 'RASCUNHO' ? 'bg-amber-100 text-amber-800' : 'bg-blue-100 text-blue-800'"
          class="px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider"
        >
          {{ form.status }}
        </span>
        <button 
          @click="salvar(false)" 
          :disabled="salvando"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition"
        >
          Salvar Rascunho
        </button>
        <button 
          @click="salvar(true)" 
          :disabled="salvando"
          class="px-5 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition"
        >
          Submeter para UGERC
        </button>
      </div>
    </div>

    <!-- Stepper de Navegação (5 Etapas) -->
    <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
      <div class="grid grid-cols-5 gap-2">
        <button 
          v-for="etapa in etapas" 
          :key="etapa.id"
          @click="etapaAtual = etapa.id"
          :class="[
            etapaAtual === etapa.id ? 'border-blue-600 text-blue-700 bg-blue-50/50' : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50',
            'border-b-2 py-3 px-2 text-center text-xs font-medium transition rounded-t-lg flex flex-col items-center'
          ]"
        >
          <span class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold mb-1"
                :class="etapaAtual === etapa.id ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'">
            {{ etapa.id }}
          </span>
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
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Unidade Organizacional *</label>
            <select v-model="form.unidade_id" @change="onUnidadeChange" class="w-full text-sm border-gray-300 rounded-lg p-2.5 border focus:ring-blue-500">
              <option :value="null">Selecione a Unidade...</option>
              <option v-for="u in unidades" :key="u.id" :value="u.id">{{ u.nome }} ({{ u.tipo }})</option>
            </select>
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

                <!-- SEÇÃO 3: Macroprocesso Outro -->
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
                <div v-if="macroprocessosFiltrados.totalFiltrados === 0" class="p-6 text-center text-gray-500 text-xs">
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
              <option value="OPERACIONAL">Operacional (falhas de processos, sistemas ou pessoas)</option>
              <option value="LEGAL_CONFORMIDADE">Legal / Conformidade (não atendimento a leis e normas)</option>
              <option value="FINANCEIRO_ORCAMENTARIO">Financeiro / Orçamentário (perda de recursos, custos imprevistos)</option>
              <option value="IMAGEM_REPUTACAO">Imagem / Reputação (desgaste da imagem pública do hospital)</option>
              <option value="SEGURANCA_INFORMACAO">Segurança da Informação (vazamento, indisponibilidade de dados)</option>
              <option value="ASSISTENCIAL_PACIENTE">Assistencial / Segurança do Paciente (eventos adversos)</option>
              <option value="INTEGRIDADE">Integridade (desvios de conduta, ética e corrupção)</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Causa do Evento de Risco * (Origem)</label>
            <input v-model="evento.causa" type="text" placeholder="Motivos que podem provocar a ocorrência (Ex: Escassez de insumos)" class="w-full text-sm border-gray-300 rounded-lg p-2.5 border focus:ring-blue-500">
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Descrição do Evento de Risco * (O que pode acontecer)</label>
            <input v-model="evento.descricao_evento" type="text" placeholder="O que pode impedir ou dificultar a entrega (Ex: Atraso no cronograma cirúrgico)" class="w-full text-sm border-gray-300 rounded-lg p-2.5 border focus:ring-blue-500">
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Consequência do Evento de Risco * (Impacto final)</label>
            <input v-model="evento.consequencia" type="text" placeholder="Impacto negativo sobre os objetivos do processo (Ex: Desassistência ao paciente e aumento do tempo de internação)" class="w-full text-sm border-gray-300 rounded-lg p-2.5 border focus:ring-blue-500">
          </div>
        </div>

        <!-- Preview Dinâmico da Frase Síntese -->
        <div class="bg-amber-50 p-4 rounded-lg border border-amber-200">
          <span class="text-xs font-bold uppercase text-amber-800 tracking-wider">Síntese Padronizada UGERC:</span>
          <p class="text-sm text-gray-800 italic mt-1">
            "Devido a <strong>{{ evento.causa || '...' }}</strong>, poderá acontecer <strong>{{ evento.descricao_evento || '...' }}</strong>, o que pode levar a <strong>{{ evento.consequencia || '...' }}</strong>."
          </p>
        </div>
      </div>

      <!-- ETAPA 3: Avaliação & Controles -->
      <div v-show="etapaAtual === 3" class="space-y-6">
        <h3 class="text-base font-bold text-gray-800 border-b pb-2">3. Avaliação dos Riscos e Medidas de Controle</h3>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Probabilidade -->
          <div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <label class="block text-xs font-bold text-gray-700 mb-2">Quão provável é a ocorrência deste risco? (Probabilidade: {{ avaliacao.probabilidade }})</label>
            <div class="grid grid-cols-5 gap-1.5">
              <button 
                v-for="p in [1, 2, 3, 4, 5]" 
                :key="'p-' + p"
                type="button"
                @click="avaliacao.probabilidade = p; recalcular()"
                :class="avaliacao.probabilidade === p ? 'bg-blue-600 text-white font-bold' : 'bg-white text-gray-700 hover:bg-gray-100 border'"
                class="py-2 text-xs rounded-lg transition"
              >
                {{ p }}
              </button>
            </div>
            <p class="text-[11px] text-gray-500 mt-2">
              {{ ['1 - Improvável', '2 - Pouco Provável', '3 - Possível', '4 - Provável', '5 - Quase Certo'][avaliacao.probabilidade - 1] }}
            </p>
          </div>

          <!-- Impacto -->
          <div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <label class="block text-xs font-bold text-gray-700 mb-2">Qual o grau de impacto deste risco? (Impacto: {{ avaliacao.impacto }})</label>
            <div class="grid grid-cols-5 gap-1.5">
              <button 
                v-for="i in [1, 2, 3, 4, 5]" 
                :key="'i-' + i"
                type="button"
                @click="avaliacao.impacto = i; recalcular()"
                :class="avaliacao.impacto === i ? 'bg-blue-600 text-white font-bold' : 'bg-white text-gray-700 hover:bg-gray-100 border'"
                class="py-2 text-xs rounded-lg transition"
              >
                {{ i }}
              </button>
            </div>
            <p class="text-[11px] text-gray-500 mt-2">
              {{ ['1 - Insignificante', '2 - Menor', '3 - Moderado', '4 - Maior', '5 - Catastrófico'][avaliacao.impacto - 1] }}
            </p>
          </div>
        </div>

        <!-- Controles Existentes -->
        <div class="space-y-3">
          <div class="flex justify-between items-center">
            <div>
              <h4 class="text-xs font-bold text-gray-800">Medidas de Controle Interno Existentes</h4>
              <p class="text-xs text-gray-500">Cada controle ativo reduz o Risco Residual através do Fator de Mitigação.</p>
            </div>
            <button 
              type="button" 
              @click="adicionarControle"
              class="px-3 py-1.5 text-xs font-semibold bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition"
            >
              + Adicionar Controle
            </button>
          </div>

          <div v-if="avaliacao.controles.length === 0" class="text-xs text-gray-400 p-4 bg-gray-50 rounded-lg text-center border border-dashed">
            Nenhum controle informado. Fator de Mitigação aplicado: 1.0 (Sem redução de risco).
          </div>

          <div v-else class="space-y-2">
            <div v-for="(ctrl, idx) in avaliacao.controles" :key="idx" class="flex items-center space-x-2">
              <span class="text-xs font-semibold text-gray-400 w-6">#{{ idx + 1 }}</span>
              <input 
                v-model="ctrl.descricao_controle" 
                type="text" 
                placeholder="Descreva a medida de controle existente (ex: Checklist de checagem diária)" 
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

        <!-- Resumo do Cálculo em Tempo Real -->
        <div class="grid grid-cols-4 gap-3 bg-gray-50 p-4 rounded-xl border border-gray-200 text-center">
          <div>
            <span class="text-xs text-gray-500 block">Risco Inerente (P × I)</span>
            <span class="text-xl font-bold text-gray-800">{{ calculo.risco_inerente }}</span>
          </div>
          <div>
            <span class="text-xs text-gray-500 block">Fator de Mitigação</span>
            <span class="text-xl font-bold text-blue-600">{{ calculo.fator_mitigacao }}</span>
          </div>
          <div>
            <span class="text-xs text-gray-500 block">Risco Residual</span>
            <span class="text-xl font-bold text-gray-900">{{ calculo.risco_residual }}</span>
          </div>
          <div>
            <span class="text-xs text-gray-500 block">Classificação Final</span>
            <span 
              :class="getClassificacaoBadge(calculo.classificacao)"
              class="inline-block mt-1 px-3 py-0.5 rounded-full text-xs font-extrabold uppercase"
            >
              {{ calculo.classificacao }}
            </span>
          </div>
        </div>
      </div>

      <!-- ETAPA 4: Matriz de Priorização -->
      <div v-show="etapaAtual === 4" class="space-y-5">
        <h3 class="text-base font-bold text-gray-800 border-b pb-2">4. Priorização dos Riscos na Matriz 5x5</h3>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div class="lg:col-span-2">
            <MatrizRisco5x5 :activeP="avaliacao.probabilidade" :activeI="avaliacao.impacto" />
          </div>

          <div class="space-y-4">
            <div class="p-4 rounded-xl border" :class="calculo.acima_apetite ? 'bg-rose-50 border-rose-200' : 'bg-emerald-50 border-emerald-200'">
              <span class="text-xs font-bold uppercase tracking-wider block" :class="calculo.acima_apetite ? 'text-rose-700' : 'text-emerald-700'">
                {{ calculo.acima_apetite ? 'ACIMA DO APETITE A RISCO' : 'DENTRO DO APETITE A RISCO' }}
              </span>
              <p class="text-xs text-gray-700 mt-2 leading-relaxed">
                {{ calculo.acima_apetite 
                  ? 'Este risco possui resultado residual > 7,99 (Alto ou Extremo). Conforme deliberação do Colegiado Executivo do HC-UFPE, é OBRIGATÓRIO elaborar Plano de Ação 5W2H e Plano de Contingência.'
                  : 'Este risco está dentro da tolerância institucional (≤ 7,99). Não exige tratamento compulsório, mas novas medidas podem ser adotadas voluntariamente.' }}
              </p>
            </div>

            <div class="bg-gray-50 p-4 rounded-xl border border-gray-200 space-y-2 text-xs text-gray-600">
              <p><strong>Causa:</strong> {{ evento.causa || 'Não preenchida' }}</p>
              <p><strong>Evento:</strong> {{ evento.descricao_evento || 'Não preenchido' }}</p>
              <p><strong>Consequência:</strong> {{ evento.consequencia || 'Não preenchida' }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- ETAPA 5: Resposta, 5W2H e Contingência -->
      <div v-show="etapaAtual === 5" class="space-y-6">
        <div class="border-b pb-2 flex justify-between items-center">
          <div>
            <h3 class="text-base font-bold text-gray-800">5. Respostas aos Riscos, Planos de Ação e Contingência</h3>
            <p class="text-xs text-gray-500">Elabore o plano de tratamento (5W2H) e plano de contingência com gatilhos operacionais.</p>
          </div>
        </div>

        <!-- Planos de Ação 5W2H -->
        <div class="space-y-3">
          <div class="flex justify-between items-center">
            <h4 class="text-xs font-bold text-gray-800 uppercase tracking-wider">Planos de Ação (Metodologia 5W2H)</h4>
            <button 
              type="button" 
              @click="adicionarPlanoAcao"
              class="px-3 py-1.5 text-xs font-semibold bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              + Adicionar Ação 5W2H
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
                  <label class="block text-[11px] font-semibold text-gray-600 mb-1">O que fazer? (What)</label>
                  <input v-model="pa.o_que" type="text" placeholder="Ação detalhada" class="w-full text-xs border-gray-300 rounded p-2 border" />
                </div>
                <div>
                  <label class="block text-[11px] font-semibold text-gray-600 mb-1">Como fazer? (How)</label>
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
              <h4 class="text-xs font-bold text-gray-800 uppercase tracking-wider">Planos de Contingência</h4>
              <p class="text-xs text-gray-500">Ações preparadas para ativação imediata caso o gatilho ocorra.</p>
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
        @click="etapaAtual = Math.max(1, etapaAtual - 1)" 
        :disabled="etapaAtual === 1"
        class="px-4 py-2 text-sm text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40"
      >
        ← Voltar
      </button>

      <span class="text-xs text-gray-400">Etapa {{ etapaAtual }} de 5</span>

      <button 
        type="button" 
        @click="etapaAtual = Math.min(5, etapaAtual + 1)" 
        :disabled="etapaAtual === 5"
        class="px-5 py-2 text-sm text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-40 shadow-sm"
      >
        Avançar →
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '../../services/api';
import MatrizRisco5x5 from '../../components/riscos/MatrizRisco5x5.vue';

const route = useRoute();
const router = useRouter();

const etapaAtual = ref(1);
const salvando = ref(false);

const etapas = [
  { id: 1, nome: 'Contexto & Processo' },
  { id: 2, nome: 'Identificação' },
  { id: 3, nome: 'Avaliação & Controles' },
  { id: 4, nome: 'Priorização 5x5' },
  { id: 5, nome: 'Planos de Ação' }
];

const unidades = ref<any[]>([]);
const macroprocessos = ref<any[]>([]);
const pilares = ref<any[]>([]);

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
  return null;
});

const isProcessoOutro = computed(() => {
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

function handleClickOutside(event: MouseEvent) {
  const el = dropdownRef.value;
  if (el && !el.contains(event.target as Node)) {
    dropdownAberto.value = false;
  }
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
  status: 'RASCUNHO'
});

const evento = reactive({
  categoria: 'OPERACIONAL',
  causa: '',
  descricao_evento: '',
  consequencia: '',
  planos_acao: [] as any[],
  planos_contingencia: [] as any[]
});

const avaliacao = reactive({
  probabilidade: 3,
  impacto: 3,
  controles: [] as { descricao_controle: string }[]
});

const calculo = reactive({
  risco_inerente: 9,
  fator_mitigacao: 1.0,
  risco_residual: 9,
  classificacao: 'MEDIO',
  acima_apetite: true
});

function recalcular() {
  const p = avaliacao.probabilidade;
  const i = avaliacao.impacto;
  const inerente = p * i;
  const num = avaliacao.controles.length;

  let fator = 1.0;
  if (num === 1) fator = 0.8;
  else if (num === 2) fator = 0.6;
  else if (num === 3) fator = 0.4;
  else if (num >= 4) fator = 0.2;

  const residual = Math.round(inerente * fator);
  let classif = 'BAIXO';
  if (residual <= 2) classif = 'BAIXO';
  else if (residual <= 7) classif = 'MEDIO';
  else if (residual <= 14) classif = 'ALTO';
  else classif = 'EXTREMO';

  calculo.risco_inerente = inerente;
  calculo.fator_mitigacao = fator;
  calculo.risco_residual = residual;
  calculo.classificacao = classif;
  calculo.acima_apetite = (residual > 7);
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

async function carregarProcessos(unidadeId?: number | null) {
  try {
    const params = unidadeId ? { unidade_id: unidadeId } : {};
    const resP = await api.get('/api/processos', { params });
    macroprocessos.value = resP.data;
  } catch (err) {
    console.error('Erro ao carregar processos:', err);
  }
}

async function onUnidadeChange() {
  if (form.unidade_id) {
    await carregarProcessos(form.unidade_id);
    let existe = false;
    for (const m of macroprocessos.value) {
      if (m.processos?.some((p: any) => p.id === form.processo_id)) {
        existe = true;
        break;
      }
    }
    if (!existe) {
      form.processo_id = null;
    }
  } else {
    macroprocessos.value = [];
    form.processo_id = null;
  }
}

async function carregarAuxiliares() {
  try {
    const [resU, resPil] = await Promise.all([
      api.get('/api/unidades'),
      api.get('/api/processos/pilares-estrategicos')
    ]);
    unidades.value = resU.data;
    pilares.value = resPil.data;
    if (form.unidade_id) {
      await carregarProcessos(form.unidade_id);
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
    if (data.unidade_id) {
      await carregarProcessos(data.unidade_id);
    }
    form.processo_id = data.processo_id;
    form.processo_outro = data.processo_outro || '';
    form.possui_projeto = data.possui_projeto;
    form.nome_projeto = data.nome_projeto || '';
    form.pilar_estrategico_id = data.pilar_estrategico_id;
    form.entrega_processo = data.entrega_processo;
    form.status = data.status;

    if (data.eventos && data.eventos.length > 0) {
      const ev = data.eventos[0];
      evento.categoria = ev.categoria;
      evento.causa = ev.causa;
      evento.descricao_evento = ev.descricao_evento;
      evento.consequencia = ev.consequencia;
      evento.planos_acao = ev.planos_acao || [];
      evento.planos_contingencia = ev.planos_contingencia || [];

      if (ev.avaliacao) {
        avaliacao.probabilidade = ev.avaliacao.probabilidade;
        avaliacao.impacto = ev.avaliacao.impacto;
        avaliacao.controles = ev.avaliacao.controles || [];
      }
      recalcular();
    }
  } catch (err) {
    console.error('Erro ao carregar mapeamento:', err);
  }
}

async function salvar(submeter: boolean) {
  if (!form.unidade_id || !form.processo_id) {
    alert('Por favor, informe a Unidade Organizacional e o Processo na Etapa 1.');
    etapaAtual.value = 1;
    return;
  }

  if (isProcessoOutro.value && !form.processo_outro?.trim()) {
    alert('Por favor, informe a denominação do novo processo mapeado ("Outro") na Etapa 1.');
    etapaAtual.value = 1;
    return;
  }

  if (submeter) {
    if (!evento.descricao_evento || !evento.causa || !evento.consequencia) {
      alert('Por favor, preencha Causa, Evento de Risco e Consequência na Etapa 2.');
      etapaAtual.value = 2;
      return;
    }
    if (calculo.acima_apetite && evento.planos_acao.length === 0) {
      alert('Riscos acima do apetite (> 7,99) exigem ao menos um Plano de Ação 5W2H na Etapa 5.');
      etapaAtual.value = 5;
      return;
    }
    form.status = 'SUBMETIDO';
  } else {
    form.status = 'RASCUNHO';
  }

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
      status: form.status,
      eventos: [
        {
          categoria: evento.categoria,
          causa: evento.causa,
          descricao_evento: evento.descricao_evento,
          consequencia: evento.consequencia,
          avaliacao: {
            probabilidade: avaliacao.probabilidade,
            impacto: avaliacao.impacto,
            controles: avaliacao.controles.map(c => c.descricao_controle)
          },
          planos_acao: evento.planos_acao,
          planos_contingencia: evento.planos_contingencia
        }
      ]
    };

    const res = await api.post('/api/riscos', payload);
    form.id = res.data.id;
    alert(submeter ? 'Mapeamento submetido à UGERC com sucesso!' : 'Rascunho salvo com sucesso!');
    router.push('/riscos');
  } catch (err: any) {
    console.error('Erro ao salvar:', err);
    alert(err.response?.data?.detail || 'Erro ao salvar mapeamento de risco.');
  } finally {
    salvando.value = false;
  }
}

onMounted(async () => {
  document.addEventListener('click', handleClickOutside);
  await carregarAuxiliares();
  const idParam = route.params.id;
  if (idParam) {
    await carregarMapeamento(Number(idParam));
  } else {
    recalcular();
  }
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>
